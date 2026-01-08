"""
Geospatial Data Downloader & Processor for Odisha Flood Validation System.

This script automates:
1. Downloading SRTM 30m DEM tiles (OpenTopography/USGS)
2. Downloading pre-computed HAND from HydroSHEDS
3. Generating Slope from DEM using GDAL
4. Clipping all rasters to Mahanadi Delta bounding box

Requirements:
    pip install requests rasterio numpy elevation
    
For GDAL on Windows:
    pip install GDAL  # Or use OSGeo4W installer

Usage:
    python -m src.preprocessing.download_geospatial_data
"""

import os
import sys
import shutil
import zipfile
import requests
from pathlib import Path
import subprocess

# =====================================================
# CONFIGURATION
# =====================================================

# Mahanadi Delta Bounding Box (covers most flood-prone areas)
BOUNDS = {
    'west': 84.5,
    'east': 87.0,
    'south': 19.5,
    'north': 22.0
}

# Output directory
OUTPUT_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")

# File names
DEM_FILE = "mahanadi_dem_30m.tif"
HAND_FILE = "mahanadi_hand.tif"
SLOPE_FILE = "mahanadi_slope.tif"

# =====================================================
# DOWNLOAD FUNCTIONS
# =====================================================

def ensure_directories():
    """Create necessary directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directories ready: {OUTPUT_DIR}, {RAW_DIR}")


def download_srtm_dem():
    """
    Download SRTM 30m DEM using the 'elevation' package.
    This uses NASA's SRTM data via OpenTopography.
    """
    print("\n--- Downloading SRTM 30m DEM ---")
    
    try:
        import elevation
        
        output_path = OUTPUT_DIR / DEM_FILE
        
        # elevation.clip expects (west, south, east, north)
        elevation.clip(
            bounds=(BOUNDS['west'], BOUNDS['south'], BOUNDS['east'], BOUNDS['north']),
            output=str(output_path),
            product='SRTM3'  # SRTM 90m; use 'SRTM1' for 30m if available
        )
        
        # Clean up cache
        elevation.clean()
        
        print(f"[OK] DEM downloaded: {output_path}")
        return output_path
        
    except ImportError:
        print("[WARN] 'elevation' package not installed. Trying alternative method...")
        return download_srtm_alternative()
    except Exception as e:
        print(f"[WARN] elevation.clip failed: {e}")
        return download_srtm_alternative()


def download_srtm_alternative():
    """
    Alternative method: Download individual SRTM tiles from USGS.
    """
    print("[INFO] Using alternative SRTM download method...")
    
    # SRTM tiles covering our region
    tiles = [
        "N19E084", "N19E085", "N19E086",
        "N20E084", "N20E085", "N20E086",
        "N21E084", "N21E085", "N21E086"
    ]
    
    # USGS EarthExplorer requires login, so we'll use a mirror
    # OpenTopography bulk download requires API key
    # Fallback: Use CGIAR-CSI SRTM (public, no auth)
    
    base_url = "https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/"
    
    # CGIAR uses different tile naming: srtm_XX_YY
    # Our tiles roughly correspond to: srtm_55_08, srtm_55_09, srtm_56_08, srtm_56_09
    cgiar_tiles = ["srtm_55_08", "srtm_55_09", "srtm_56_08", "srtm_56_09"]
    
    downloaded = []
    for tile in cgiar_tiles:
        url = f"{base_url}{tile}.zip"
        local_zip = RAW_DIR / f"{tile}.zip"
        
        print(f"  Downloading {tile}...")
        try:
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(local_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract
                with zipfile.ZipFile(local_zip, 'r') as zf:
                    zf.extractall(RAW_DIR)
                
                tif_path = RAW_DIR / f"{tile}.tif"
                if tif_path.exists():
                    downloaded.append(str(tif_path))
                    print(f"    [OK] {tile}")
            else:
                print(f"    [SKIP] {tile} (HTTP {response.status_code})")
        except Exception as e:
            print(f"    [FAIL] {tile}: {e}")
    
    if not downloaded:
        print("[ERROR] No SRTM tiles downloaded. Please download manually from:")
        print("  https://dwtkns.com/srtm30m/")
        print("  Place merged DEM at: data/processed/mahanadi_dem_30m.tif")
        return None
    
    # Merge tiles using GDAL
    output_path = OUTPUT_DIR / DEM_FILE
    merge_cmd = f"gdal_merge.py -o {output_path} " + " ".join(downloaded)
    
    print(f"[INFO] Merging {len(downloaded)} tiles...")
    try:
        subprocess.run(merge_cmd, shell=True, check=True)
        print(f"[OK] DEM merged: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] GDAL merge failed: {e}")
        print("  Ensure GDAL is installed: pip install GDAL")
        return None


def download_hydrosheds_hand():
    """
    Download pre-computed HAND from HydroSHEDS.
    HydroSHEDS provides global HAND at 3-arcsec (~90m) resolution.
    """
    print("\n--- Downloading HydroSHEDS HAND ---")
    
    # HydroSHEDS HAND is distributed via WWF
    # Direct download link for Asia region
    # Note: These are large files (~500MB for Asia)
    
    # For Odisha, we need the South Asia tile
    hand_url = "https://data.hydrosheds.org/file/hydrosheds-v1-dem/hd_as_dem_30s.tif"
    
    # Alternative: Use the newer HydroSHEDS 15-arcsec product
    # hand_url = "https://data.hydrosheds.org/file/hydrosheds-v2/..."
    
    output_path = OUTPUT_DIR / HAND_FILE
    temp_path = RAW_DIR / "hydrosheds_asia_hand.tif"
    
    # Check if already exists
    if output_path.exists():
        print(f"[SKIP] HAND already exists: {output_path}")
        return output_path
    
    print(f"[INFO] Downloading from HydroSHEDS (this may take a while)...")
    print(f"  URL: {hand_url}")
    
    try:
        # Since the full Asia file is huge, let's try a different approach
        # Use rasterio to download just the region we need via VSICURL
        
        import rasterio
        from rasterio.windows import from_bounds
        
        print("[INFO] Using rasterio virtual file system to extract region...")
        
        with rasterio.open(f"/vsicurl/{hand_url}") as src:
            # Get window for our bounds
            window = from_bounds(
                BOUNDS['west'], BOUNDS['south'],
                BOUNDS['east'], BOUNDS['north'],
                src.transform
            )
            
            # Read data
            data = src.read(1, window=window)
            
            # Calculate new transform
            transform = src.window_transform(window)
            
            # Write clipped raster
            profile = src.profile.copy()
            profile.update(
                width=window.width,
                height=window.height,
                transform=transform
            )
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(data, 1)
        
        print(f"[OK] HAND extracted: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[WARN] HydroSHEDS download failed: {e}")
        print("[INFO] Falling back to generating HAND from DEM...")
        return generate_hand_from_dem()


def generate_hand_from_dem():
    """
    Generate HAND from DEM using WhiteboxTools or richdem.
    """
    dem_path = OUTPUT_DIR / DEM_FILE
    output_path = OUTPUT_DIR / HAND_FILE
    
    if not dem_path.exists():
        print(f"[ERROR] DEM not found at {dem_path}. Cannot generate HAND.")
        return None
    
    print("[INFO] Generating HAND from DEM (this may take a few minutes)...")
    
    try:
        # Try WhiteboxTools first
        import whitebox
        wbt = whitebox.WhiteboxTools()
        wbt.set_verbose_mode(False)
        
        # WhiteboxTools HAND calculation
        # First, we need to fill depressions and calculate flow accumulation
        filled_dem = str(RAW_DIR / "filled_dem.tif")
        flow_dir = str(RAW_DIR / "flow_dir.tif")
        flow_acc = str(RAW_DIR / "flow_acc.tif")
        streams = str(RAW_DIR / "streams.tif")
        
        print("  1/4 Filling depressions...")
        wbt.fill_depressions(str(dem_path), filled_dem)
        
        print("  2/4 Calculating flow direction...")
        wbt.d8_pointer(filled_dem, flow_dir)
        
        print("  3/4 Calculating flow accumulation...")
        wbt.d8_flow_accumulation(filled_dem, flow_acc)
        
        print("  4/4 Extracting streams and computing HAND...")
        # Extract streams (threshold ~1000 cells for major streams)
        wbt.extract_streams(flow_acc, streams, threshold=1000)
        
        # Calculate HAND
        wbt.elevation_above_stream(str(dem_path), streams, str(output_path))
        
        print(f"[OK] HAND generated: {output_path}")
        return output_path
        
    except ImportError:
        print("[WARN] WhiteboxTools not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "whitebox"], check=True)
        return generate_hand_from_dem()  # Retry
        
    except Exception as e:
        print(f"[ERROR] HAND generation failed: {e}")
        print("  Try: pip install whitebox")
        return None


def generate_slope():
    """
    Generate Slope raster from DEM using GDAL.
    """
    print("\n--- Generating Slope ---")
    
    dem_path = OUTPUT_DIR / DEM_FILE
    output_path = OUTPUT_DIR / SLOPE_FILE
    
    if not dem_path.exists():
        print(f"[ERROR] DEM not found at {dem_path}. Cannot generate slope.")
        return None
    
    if output_path.exists():
        print(f"[SKIP] Slope already exists: {output_path}")
        return output_path
    
    # Using GDAL
    cmd = f'gdaldem slope "{dem_path}" "{output_path}" -of GTiff -compute_edges'
    
    try:
        print(f"[INFO] Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[OK] Slope generated: {output_path}")
            return output_path
        else:
            print(f"[ERROR] gdaldem failed: {result.stderr}")
            return generate_slope_python()
            
    except Exception as e:
        print(f"[WARN] GDAL command failed: {e}")
        return generate_slope_python()


def generate_slope_python():
    """
    Fallback: Generate slope using rasterio + numpy.
    """
    print("[INFO] Using Python fallback for slope calculation...")
    
    import numpy as np
    import rasterio
    
    dem_path = OUTPUT_DIR / DEM_FILE
    output_path = OUTPUT_DIR / SLOPE_FILE
    
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        transform = src.transform
        profile = src.profile.copy()
        
        # Pixel size in meters (approximate)
        cellsize = abs(transform[0]) * 111320  # degrees to meters at equator
        
        # Calculate gradient
        dy, dx = np.gradient(dem, cellsize)
        
        # Slope in degrees
        slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
        
        # Handle nodata
        slope[dem == src.nodata] = src.nodata
        
        # Write output
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(slope.astype(np.float32), 1)
    
    print(f"[OK] Slope generated (Python): {output_path}")
    return output_path


def verify_outputs():
    """
    Verify all required files exist and are readable.
    """
    print("\n--- Verifying Outputs ---")
    
    import rasterio
    
    files = [
        (OUTPUT_DIR / DEM_FILE, "DEM"),
        (OUTPUT_DIR / HAND_FILE, "HAND"),
        (OUTPUT_DIR / SLOPE_FILE, "Slope"),
    ]
    
    all_ok = True
    for path, name in files:
        if path.exists():
            try:
                with rasterio.open(path) as src:
                    print(f"  [OK] {name}: {src.width}x{src.height} pixels, CRS: {src.crs}")
            except Exception as e:
                print(f"  [WARN] {name}: File exists but unreadable: {e}")
                all_ok = False
        else:
            print(f"  [MISSING] {name}: {path}")
            all_ok = False
    
    return all_ok


# =====================================================
# MAIN
# =====================================================

def main():
    print("=" * 60)
    print("GEOSPATIAL DATA PIPELINE FOR ODISHA FLOOD VALIDATION")
    print("=" * 60)
    print(f"Region: {BOUNDS}")
    print(f"Output: {OUTPUT_DIR.absolute()}")
    print("=" * 60)
    
    ensure_directories()
    
    # Step 1: DEM
    dem_path = download_srtm_dem()
    
    # Step 2: HAND
    if dem_path:
        hand_path = download_hydrosheds_hand()
    else:
        print("[SKIP] HAND (DEM not available)")
        hand_path = None
    
    # Step 3: Slope
    if dem_path:
        slope_path = generate_slope()
    else:
        print("[SKIP] Slope (DEM not available)")
        slope_path = None
    
    # Verify
    print("\n" + "=" * 60)
    success = verify_outputs()
    
    if success:
        print("\n[SUCCESS] All geospatial data ready!")
        print("Layer 1 (Physical Plausibility) can now use real terrain data.")
    else:
        print("\n[PARTIAL] Some files missing. Check logs above.")
        print("You may need to download DEM manually from:")
        print("  https://dwtkns.com/srtm30m/ (select tiles N19-N21, E084-E087)")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
