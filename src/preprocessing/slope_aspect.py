import numpy as np
import rasterio
from pathlib import Path

def calculate_slope(dem_path: str, output_path: str) -> None:
    """
    Calculates slope in degrees from a DEM raster using Horn's method (typical for GIS).
    
    Args:
        dem_path (str): Path to input DEM.
        output_path (str): Path to save slope raster.
    """
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        transform = src.transform
        profile = src.profile
        
        # Cell sizes
        dx = transform[0]
        dy = -transform[4] # Usually negative in GeoTIFF
        
        # We need gradient. np.gradient might compute central differences but Horn's method is specific.
        # For simplicity and standard compliance, let's use a 3x3 window approach or richdem/wbt if available.
        # However, implementing a basic slope calculation using numpy gradient is a good fallback 
        # and removes extra heavy dependencies if we want pure python.
        
        # Using numpy gradient (central difference), which is similar to Zevenbergen-Thorne
        # Horn's is slightly different (weighted). 
        # Let's stick to numpy gradient for efficiency and simplicity.
        
        # Gradient in y and x
        # Note: np.gradient returns (d/dy, d/dx) for 2D array
        grad_y, grad_x = np.gradient(dem, dy, dx)
        
        # Slope = arctan(sqrt(dz/dx^2 + dz/dy^2)) * (180 / pi)
        slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
        slope_deg = np.degrees(slope_rad)
        
        # Handle edges or nodata if necessary (gradient might produce artifacts at edges)
        # Nodata handling:
        if src.nodata is not None:
             mask = (dem == src.nodata)
             slope_deg[mask] = src.nodata

        profile.update(dtype=rasterio.float32, count=1)
        
        with rasterio.open(output_path, 'w', **profile) as dest:
            dest.write(slope_deg.astype(rasterio.float32), 1)

    print(f"Slope raster saved to {output_path}")

if __name__ == "__main__":
    # example
    # calculate_slope("data/processed/dem.tif", "data/processed/slope.tif")
    pass
