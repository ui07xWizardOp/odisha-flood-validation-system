"""
Drainage Network Extraction Module.

Converts raster stream network to vector shapefile.
"""

import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape, LineString
from shapely.ops import linemerge
import numpy as np
from pathlib import Path
from typing import Optional


def raster_to_vector_streams(
    raster_path: Path, 
    output_shp: Path,
    simplify_tolerance: float = 0.0001
) -> gpd.GeoDataFrame:
    """
    Convert binary stream raster to vector polylines.
    
    Args:
        raster_path: Path to binary raster (streams = 1, else = 0)
        output_shp: Output shapefile path
        simplify_tolerance: Douglas-Peucker simplification tolerance
        
    Returns:
        GeoDataFrame of stream segments
    """
    with rasterio.open(raster_path) as src:
        image = src.read(1)
        crs = src.crs
        
        # Binary mask where streams exist
        mask_arr = image > 0
        
        # Skip if no streams found
        if not mask_arr.any():
            print("Warning: No stream pixels found in raster.")
            return gpd.GeoDataFrame()
        
        # Extract polygon shapes
        results = [
            {'properties': {'stream_id': idx, 'value': int(v)}, 'geometry': s}
            for idx, (s, v) in enumerate(shapes(image.astype(np.int16), mask=mask_arr, transform=src.transform))
        ]
    
    if not results:
        print("Warning: No shapes extracted from raster.")
        return gpd.GeoDataFrame()
    
    # Convert to GeoDataFrame
    geoms = [shape(result['geometry']) for result in results]
    props = [result['properties'] for result in results]
    
    gdf = gpd.GeoDataFrame(props, geometry=geoms, crs=crs)
    
    # Simplify geometries to reduce file size
    if simplify_tolerance > 0:
        gdf['geometry'] = gdf['geometry'].simplify(simplify_tolerance)
    
    # Save as shapefile
    output_shp.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_shp)
    
    print(f"Drainage network saved: {output_shp}")
    print(f"Total stream segments: {len(gdf)}")
    print(f"Total length: {gdf.geometry.length.sum():.2f} degrees")
    
    return gdf


def calculate_stream_order(
    streams_gdf: gpd.GeoDataFrame, 
    flow_direction_raster: Path
) -> gpd.GeoDataFrame:
    """
    Calculate Strahler stream order for each segment.
    
    Note: This is a placeholder - full implementation requires
    topological analysis of the stream network.
    """
    # TODO: Implement Strahler ordering
    streams_gdf['stream_order'] = 1
    return streams_gdf


if __name__ == "__main__":
    from src.utils.config import Config
    
    streams_raster = Config.PROCESSED_DATA_DIR / "streams.tif"
    output_shapefile = Config.PROCESSED_DATA_DIR / "drainage_network.shp"
    
    if streams_raster.exists():
        gdf = raster_to_vector_streams(streams_raster, output_shapefile)
    else:
        print(f"Streams raster not found: {streams_raster}")
        print("Run hand_calculator.py first to generate stream network.")
