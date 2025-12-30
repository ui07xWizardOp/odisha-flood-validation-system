import numpy as np
import rasterio
from rasterio.transform import from_origin
from pathlib import Path

def parse_imd_rainfall_grid(ascii_path: str, output_tif: str):
    """
    Parses IMD Gridded Rainfall (ASCII format) and converts to GeoTIFF.
    Expected format: 6 header lines followed by space-separated values.
    Resolution: 0.25 x 0.25 degree usually.
    """
    header = {}
    data_start_line = 0
    
    with open(ascii_path, 'r') as f:
        # Read header (assumed first 6 lines standard .grd/.asc style)
        # NCOLS ...
        # NROWS ...
        # XLLCORNER ...
        # YLLCORNER ...
        # CELLSIZE ...
        # NODATA_VALUE ...
        for i in range(6):
            line = f.readline().strip().split()
            if len(line) >= 2:
                key = line[0].lower()
                val = float(line[1])
                header[key] = val
                data_start_line += 1
    
    # Read data
    data = np.loadtxt(ascii_path, skiprows=data_start_line)
    
    # Validate dimensions
    nrows = int(header.get('nrows', data.shape[0]))
    ncols = int(header.get('ncols', data.shape[1]))
    nodata = header.get('nodata_value', -999.0)
    
    # Ensure data shape matches
    if data.shape != (nrows, ncols):
        print(f"Warning: Data shape {data.shape} does not match header rows/cols {nrows}, {ncols}")

    # Create transform
    # XLLCORNER is usually lower-left. Rasterio uses top-left usually.
    # Top Left Y = YLL + NROWS * CELLSIZE
    xll = header['xllcorner']
    yll = header['yllcorner']
    cellsize = header['cellsize']
    
    top_y = yll + (nrows * cellsize)
    left_x = xll
    
    transform = from_origin(left_x, top_y, cellsize, cellsize)
    
    # Write GeoTIFF
    out_meta = {
        'driver': 'GTiff',
        'height': nrows,
        'width': ncols,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:4326', # Assuming WGS84 for IMD grid
        'transform': transform,
        'nodata': nodata
    }
    
    with rasterio.open(output_tif, 'w', **out_meta) as dest:
        dest.write(data.astype('float32'), 1)
        
    print(f"Converted {ascii_path} to {output_tif}")

if __name__ == "__main__":
    # parse_imd_rainfall_grid("data/raw/imd/rain.asc", "data/processed/rain.tif")
    pass
