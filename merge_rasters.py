"""
Merge SRTM tiles and generate Slope using pure Python (rasterio + numpy).
Run this if GDAL command-line tools are not available.
"""

import rasterio
from rasterio.merge import merge
from rasterio.enums import Resampling
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Find all SRTM tiles
tiles = list(RAW_DIR.glob("srtm_*.tif"))
print(f"Found {len(tiles)} SRTM tiles")

if not tiles:
    print("No tiles found!")
    exit(1)

# Step 1: Merge tiles
print("\n1. Merging tiles...")
datasets = [rasterio.open(t) for t in tiles]
merged_array, merged_transform = merge(datasets)

# Get profile from first dataset
profile = datasets[0].profile.copy()
profile.update(
    driver='GTiff',
    height=merged_array.shape[1],
    width=merged_array.shape[2],
    transform=merged_transform,
    compress='lzw'
)

# Close datasets
for ds in datasets:
    ds.close()

# Write merged DEM
dem_path = OUTPUT_DIR / "mahanadi_dem_30m.tif"
with rasterio.open(dem_path, 'w', **profile) as dst:
    dst.write(merged_array)
print(f"   [OK] DEM saved: {dem_path}")

# Step 2: Generate Slope
print("\n2. Generating slope...")
with rasterio.open(dem_path) as src:
    dem = src.read(1).astype(np.float32)
    transform = src.transform
    nodata = src.nodata
    
    # Cell size in meters (approximate at this latitude)
    cellsize = abs(transform[0]) * 111320
    
    # Gradient calculation
    dy, dx = np.gradient(dem, cellsize)
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    
    # Handle nodata
    if nodata is not None:
        slope[dem == nodata] = nodata
    
    # Write slope
    slope_path = OUTPUT_DIR / "mahanadi_slope.tif"
    slope_profile = src.profile.copy()
    with rasterio.open(slope_path, 'w', **slope_profile) as dst:
        dst.write(slope.astype(np.float32), 1)
    print(f"   [OK] Slope saved: {slope_path}")

# Step 3: Generate basic HAND (Height Above Minimum in neighborhood)
# Note: This is a simplified approximation. True HAND requires flow direction.
print("\n3. Generating simplified HAND approximation...")
with rasterio.open(dem_path) as src:
    dem = src.read(1).astype(np.float32)
    
    from scipy.ndimage import minimum_filter
    
    # Find local minimum in a 33x33 window (~1km at 30m resolution)
    local_min = minimum_filter(dem, size=33)
    
    # HAND = elevation - local minimum
    hand = dem - local_min
    hand = np.maximum(hand, 0)  # No negative values
    
    if nodata is not None:
        hand[dem == nodata] = nodata
    
    hand_path = OUTPUT_DIR / "mahanadi_hand.tif"
    hand_profile = src.profile.copy()
    with rasterio.open(hand_path, 'w', **hand_profile) as dst:
        dst.write(hand.astype(np.float32), 1)
    print(f"   [OK] HAND (simplified) saved: {hand_path}")

print("\n" + "=" * 50)
print("VERIFICATION")
print("=" * 50)

for name in ["mahanadi_dem_30m.tif", "mahanadi_slope.tif", "mahanadi_hand.tif"]:
    path = OUTPUT_DIR / name
    if path.exists():
        with rasterio.open(path) as src:
            print(f"  {name}: {src.width}x{src.height}, CRS={src.crs}")
    else:
        print(f"  {name}: MISSING")

print("\nDone!")
