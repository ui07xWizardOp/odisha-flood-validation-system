import os
import glob
import subprocess
from pathlib import Path
from typing import List, Union
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.fill import fillnodata
import numpy as np

class DEMProcessor:
    """
    Handles processing of Digital Elevation Model (DEM) tiles including
    mosaicking, clipping, and hole filling.
    """

    def __init__(self, temp_dir: str = "data/temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def mosaic_tiles(self, input_pattern: str, output_path: str) -> None:
        """
        Mosaics multiple DEM GeoTIFF tiles into a single raster.

        Args:
            input_pattern (str): Glob pattern for input tiles (e.g., "data/raw/dem/*.tif")
            output_path (str): Path to save the mosaicked raster.
        """
        dem_fps = glob.glob(str(input_pattern))
        if not dem_fps:
            raise FileNotFoundError(f"No files found matching pattern: {input_pattern}")
        
        src_files_to_mosaic = []
        for fp in dem_fps:
            src = rasterio.open(fp)
            src_files_to_mosaic.append(src)

        print(f"Mosaicking {len(src_files_to_mosaic)} tiles...")
        mosaic, out_trans = merge(src_files_to_mosaic)

        out_meta = src_files_to_mosaic[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "crs": src_files_to_mosaic[0].crs
        })

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        print(f"Mosaic saved to {output_path}")

        # Close source files
        for src in src_files_to_mosaic:
            src.close()

    def clip_to_bbox(self, input_raster: str, output_path: str, bbox: dict) -> None:
        """
        Clips a raster to a bounding box.

        Args:
            input_raster (str): Path to input raster.
            output_path (str): Path to save clipped raster.
            bbox (dict): Dictionary with keys 'min_lon', 'min_lat', 'max_lon', 'max_lat'.
        """
        # Define window from bbox is complex directly with rasterio without window utilities or mask
        # Using gdalwarp via subprocess is often more robust for simple bbox clipping, 
        # but let's stick to rasterio/gdal logic if possible or use gdal_translate.
        # Ideally, we calculate window.
        
        # Simpler approach: Use gdalwarp if available (since we depend on gdal), or rasterio mask.
        # Let's use rasterio window construction.
        
        with rasterio.open(input_raster) as src:
            # Convert bbox (WGS84) to source CRS if needed, but assuming WGS84 for now or handling transformation
            # Bbox: minx, miny, maxx, maxy
            
            # Create a window
            from rasterio.windows import from_bounds
            window = from_bounds(bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat'], src.transform)
            
            transform = rasterio.windows.transform(window, src.transform)
            
            # Read data
            data = src.read(window=window)
            
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": data.shape[1],
                "width": data.shape[2],
                "transform": transform
            })
            
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(data)
                
        print(f"Clipped raster saved to {output_path}")

    def fill_nodata(self, input_raster: str, output_path: str, max_search_distance: int = 100) -> None:
        """
        Fills NoData values in the raster using interpolation.

        Args:
            input_raster (str): Path to input raster.
            output_path (str): Path to save filled raster.
            max_search_distance (int): Max pixels to search for interpolation.
        """
        with rasterio.open(input_raster) as src:
            profile = src.profile
            arr = src.read(1)
            mask = src.read_masks(1)
            
            # Fill nodata
            filled_arr = fillnodata(arr, mask=mask, max_search_distance=max_search_distance)
            
            with rasterio.open(output_path, 'w', **profile) as dest:
                dest.write(filled_arr, 1)
        
        print(f"Filled raster saved to {output_path}")

if __name__ == "__main__":
    # Example usage
    processor = DEMProcessor()
    # processor.mosaic_tiles("data/raw/dem/*.tif", "data/temp/mosaic.tif")
