#!/bin/bash
# =============================================================================
# FABDEM and Bhuvan Data Download Script
# Odisha Flood Validation System
# =============================================================================

set -e

echo "========================================"
echo "Odisha Flood Validation - Data Download"
echo "========================================"

# Configuration
DATA_DIR="${HOME}/flood_data"
RAW_DIR="${DATA_DIR}/raw"

# Create directories
mkdir -p "${RAW_DIR}/dem"
mkdir -p "${RAW_DIR}/bhuvan"
mkdir -p "${RAW_DIR}/social_media"
mkdir -p "${RAW_DIR}/imd"

echo ""
echo "📁 Data directories created at: ${DATA_DIR}"
echo ""

# =============================================================================
# FABDEM Download
# =============================================================================
echo "🗺️  FABDEM DEM Download"
echo "-------------------------------------------"
echo "FABDEM tiles required for Mahanadi Delta (19.5°N - 21.5°N, 84.5°E - 87.0°E):"
echo "  - N19E084, N19E085, N19E086"
echo "  - N20E084, N20E085, N20E086"
echo "  - N21E084, N21E085, N21E086"
echo ""
echo "Download manually from:"
echo "  https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn"
echo ""
echo "Or use the Copernicus Data Space:"
echo "  https://dataspace.copernicus.eu/"
echo ""

# Placeholder for automated download (requires authentication)
# for lat in 19 20 21; do
#     for lon in 084 085 086; do
#         tile="N${lat}E${lon}_FABDEM_V1-2.tif"
#         echo "Downloading ${tile}..."
#         # wget -P "${RAW_DIR}/dem" "https://example.com/fabdem/${tile}"
#     done
# done

# =============================================================================
# ISRO Bhuvan Download Instructions
# =============================================================================
echo "🛰️  ISRO Bhuvan Flood Extent Data"
echo "-------------------------------------------"
echo "Required datasets:"
echo "  1. Cyclone Fani 2019 Flood Inundation Map"
echo "  2. Cyclone Amphan 2020 Flood Inundation Map"
echo ""
echo "Download from:"
echo "  https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php"
echo ""
echo "Navigate to: Archives > Cyclone > 2019 > Fani"
echo "Download the shapefile (.shp, .shx, .dbf, .prj)"
echo ""
echo "Save to: ${RAW_DIR}/bhuvan/"
echo ""

# =============================================================================
# IMD Rainfall Data
# =============================================================================
echo "🌧️  IMD Rainfall Data"
echo "-------------------------------------------"
echo "Download gridded rainfall data from:"
echo "  https://www.imdpune.gov.in/cmpg/Griddata/Rainfall.html"
echo ""
echo "Required period: May 1-10, 2019 (Cyclone Fani)"
echo "Format: ASCII grid (0.25° × 0.25° resolution)"
echo ""
echo "Save to: ${RAW_DIR}/imd/"
echo ""

# =============================================================================
# Verification
# =============================================================================
echo "📋 After downloading, verify with:"
echo ""
echo "  # Check DEM tiles"
echo "  ls -la ${RAW_DIR}/dem/"
echo ""
echo "  # Verify DEM metadata"
echo "  gdalinfo ${RAW_DIR}/dem/N20E085_FABDEM_V1-2.tif"
echo ""
echo "  # Check Bhuvan shapefiles"
echo "  ogrinfo -al ${RAW_DIR}/bhuvan/fani_flood_inundation.shp | head -20"
echo ""

echo "========================================"
echo "Download instructions complete."
echo "========================================"
