#!/bin/bash
# =============================================================================
# Odisha Flood Validation System - Project Directory Setup Script
# =============================================================================
# This script creates the complete directory structure as defined in the
# Comprehensive Plan of Action (Section 1.2.2)
#
# Usage: bash scripts/setup_project.sh
# =============================================================================

set -e  # Exit on any error

echo "=========================================="
echo "  Flood Validation System - Project Setup"
echo "=========================================="

# Define project root (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# -----------------------------------------------------------------------------
# Create Main Directory Structure
# -----------------------------------------------------------------------------
echo "📁 Creating directory structure..."

# Data directories
mkdir -p data/{raw,processed,synthetic,temp}
mkdir -p data/raw/{dem,bhuvan,social_media,imd,incois}
mkdir -p data/raw/bhuvan/{fani_2019,amphan_2020}

# Source code directories
mkdir -p src/{preprocessing,validation,api,utils,experiments}
mkdir -p src/frontend/{web-dashboard,mobile-pwa}

# Notebooks for exploration
mkdir -p notebooks

# Documentation
mkdir -p docs/{paper,api,diagrams}
mkdir -p docs/paper/figures

# Tests
mkdir -p tests/{unit,integration,fixtures}

# Results & Outputs
mkdir -p results/{figures,tables,experiments,models}

# Scripts (already exists, but ensure structure)
mkdir -p scripts

# Configuration
mkdir -p config

echo "✅ Directory structure created!"

# -----------------------------------------------------------------------------
# Create __init__.py files for Python packages
# -----------------------------------------------------------------------------
echo "📦 Creating Python package __init__.py files..."

touch src/__init__.py
touch src/preprocessing/__init__.py
touch src/validation/__init__.py
touch src/api/__init__.py
touch src/utils/__init__.py
touch src/experiments/__init__.py

echo "✅ Python packages initialized!"

# -----------------------------------------------------------------------------
# Create placeholder README files
# -----------------------------------------------------------------------------
echo "📝 Creating README placeholders..."

cat > data/README.md << 'EOF'
# Data Directory

This directory contains all data for the Flood Validation System.

## Structure

- `raw/` - Original downloaded data (do not modify)
  - `dem/` - FABDEM GeoTIFF tiles
  - `bhuvan/` - ISRO Bhuvan flood extent shapefiles
  - `social_media/` - Twitter/X data exports
  - `imd/` - IMD rainfall grids
  - `incois/` - Tide gauge data

- `processed/` - Preprocessed rasters (DEM, HAND, Slope)

- `synthetic/` - Generated synthetic datasets for experiments

- `temp/` - Intermediate processing files (auto-cleaned)

## Note
Large data files (.tif, .shp) are excluded from Git via .gitignore.
Store backups in Google Drive or external storage.
EOF

cat > notebooks/README.md << 'EOF'
# Jupyter Notebooks

This directory contains exploratory Jupyter notebooks.

## Naming Convention
- `01_data_exploration.ipynb` - Initial data inspection
- `02_dem_visualization.ipynb` - DEM/HAND/Slope visualization
- `03_algorithm_prototyping.ipynb` - Validation algorithm experiments
- `04_results_analysis.ipynb` - Final results and figures

## Note
Notebooks are excluded from Git (.ipynb). Export important code to src/.
EOF

cat > results/README.md << 'EOF'
# Results Directory

## Structure

- `figures/` - Publication-quality figures (PNG, PDF)
- `tables/` - Result tables (CSV, LaTeX)
- `experiments/` - Raw experiment outputs
- `models/` - Trained ML models (if any)

## Naming Convention
- Figures: `fig_<number>_<description>.png`
- Tables: `table_<number>_<description>.csv`
EOF

echo "✅ README placeholders created!"

# -----------------------------------------------------------------------------
# Create sample configuration file
# -----------------------------------------------------------------------------
echo "⚙️ Creating sample configuration..."

cat > config/config.yaml << 'EOF'
# Odisha Flood Validation System Configuration
# =============================================

project:
  name: "Odisha Flood Validation"
  version: "1.0.0"
  study_area: "Mahanadi Delta"

# Bounding box for study area (WGS84)
bbox:
  min_lat: 19.5
  max_lat: 21.5
  min_lon: 84.5
  max_lon: 87.0

# Validation thresholds
validation:
  final_threshold: 0.7
  layer_weights:
    physical: 0.4
    statistical: 0.4
    reputation: 0.2

# Physical plausibility parameters
physical:
  max_elevation_diff: 10.0  # meters
  hand_threshold: 5.0       # meters
  steep_slope: 15.0         # degrees

# Statistical consistency parameters
statistical:
  spatial_radius_m: 200
  min_neighbors: 3
  temporal_window_hours: 24

# Reputation system parameters
reputation:
  initial_trust: 0.5
  trust_increment: 0.1
  trust_decrement: 0.15
  min_trust: 0.0
  max_trust: 1.0

# Data paths (relative to project root)
paths:
  dem: "data/processed/mahanadi_dem_30m.tif"
  hand: "data/processed/mahanadi_hand.tif"
  slope: "data/processed/mahanadi_slope.tif"
  ground_truth: "data/raw/bhuvan/fani_2019/fani_flood_inundation.shp"

# Database configuration
database:
  host: "localhost"
  port: 5432
  name: "flood_validation"
  user: "flood_admin"
  # password: set via FLOOD_DB_PASSWORD environment variable

# API configuration
api:
  host: "0.0.0.0"
  port: 8000
  debug: true
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"
EOF

echo "✅ Configuration file created!"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  Project Setup Complete! ✨"
echo "=========================================="
echo ""
echo "Directory structure:"
tree -L 3 --dirsfirst 2>/dev/null || find . -maxdepth 3 -type d | head -30
echo ""
echo "Next steps:"
echo "  1. Run: conda activate flood-validation"
echo "  2. Run: pip install -r requirements.txt"
echo "  3. Setup database: psql -U postgres -f scripts/setup_database.sql"
echo "  4. Copy .env.example to .env and configure"
echo ""
