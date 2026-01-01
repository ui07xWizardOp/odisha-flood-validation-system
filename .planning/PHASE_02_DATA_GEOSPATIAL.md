# 📊 PHASE 2: DATA ACQUISITION & GEOSPATIAL PROCESSING
## Week 3 | DEM Download, Processing, HAND Computation

**Duration:** 7 days  
**Owner:** Geospatial Engineer + Data Analyst  
**Dependencies:** Phase 1 Complete

---

## 📋 Phase Overview

| Metric | Target |
|--------|--------|
| Duration | 1 week |
| Effort | 35 person-hours |
| Deliverables | 8 processed rasters + datasets |
| Risk Level | MEDIUM |

---

## 🎯 Phase Objectives

- [ ] OBJECTIVE 1: Download and mosaic FABDEM tiles for Mahanadi Delta
- [ ] OBJECTIVE 2: Compute HAND raster using WhiteboxTools
- [ ] OBJECTIVE 3: Calculate slope raster from DEM
- [ ] OBJECTIVE 4: Acquire ISRO Bhuvan ground truth data
- [ ] OBJECTIVE 5: Setup social media data collection pipeline

---

## 📝 TASK 2.1: FABDEM Data Download
**Owner:** Geospatial Engineer | **Duration:** 1 day | **Priority:** CRITICAL

### Microtasks

#### 2.1.1 Setup Data Directory
```bash
mkdir -p ~/flood_data/{raw,processed,backup}
cd odisha-flood-validation
ln -s ~/flood_data data_external
echo "data_external/" >> .gitignore
```

#### 2.1.2 Download FABDEM Tiles
**Required Tiles (Bounding Box: 19.5°N - 21.5°N, 84.5°E - 87.0°E):**
- [ ] N19E084_FABDEM_V1-2.tif
- [ ] N19E085_FABDEM_V1-2.tif
- [ ] N19E086_FABDEM_V1-2.tif
- [ ] N20E084_FABDEM_V1-2.tif
- [ ] N20E085_FABDEM_V1-2.tif
- [ ] N20E086_FABDEM_V1-2.tif
- [ ] N21E084_FABDEM_V1-2.tif
- [ ] N21E085_FABDEM_V1-2.tif
- [ ] N21E086_FABDEM_V1-2.tif

**Source:** https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn

```bash
cd ~/flood_data/raw/dem
# Download each tile manually or via script
```

#### 2.1.3 Verify Downloads
```bash
cd ~/flood_data/raw/dem
for file in *.tif; do
    echo "Checking $file"
    gdalinfo $file | grep -E "(Size|Pixel Size|Origin)"
done
```

**Expected Output:**
```
Size is 3601, 3601
Pixel Size = (0.000277777777778,-0.000277777777778)
```

---

## 📝 TASK 2.2: DEM Processing Pipeline
**Owner:** Geospatial Engineer | **Duration:** 1.5 days | **Priority:** CRITICAL

### Microtasks

#### 2.2.1 Mosaic Multiple Tiles
```python
# File: src/preprocessing/dem_processor.py
from rasterio.merge import merge
import rasterio
from pathlib import Path

# Mosaic 9 tiles into single raster
tile_files = list(Path("~/flood_data/raw/dem").glob("*.tif"))
# Output: odisha_fabdem_mosaic.tif
```

**Deliverable:** `~/flood_data/processed/odisha_fabdem_mosaic.tif`

#### 2.2.2 Clip to Study Area
```python
# Bounding box: min_lon=84.5, max_lon=87.0, min_lat=19.5, max_lat=21.5
# Output: mahanadi_dem_30m.tif
```

**Deliverable:** `~/flood_data/processed/mahanadi_dem_30m.tif`

#### 2.2.3 Fill NoData Values
```python
# Use inverse distance weighting to fill holes
# Run: python src/preprocessing/dem_processor.py
```

#### 2.2.4 Verify DEM Quality
```bash
gdalinfo -stats ~/flood_data/processed/mahanadi_dem_30m.tif | grep -E "(Minimum|Maximum|Mean)"
```

**Expected Stats for Mahanadi Delta:**
```
Minimum=-2.00, Maximum=245.00, Mean=12.34
```

---

## 📝 TASK 2.3: HAND Computation
**Owner:** Geospatial Engineer | **Duration:** 1 day | **Priority:** CRITICAL

### Microtasks

#### 2.3.1 Implement HAND Calculator
```python
# File: src/preprocessing/hand_calculator.py
# Steps:
# 1. Fill depressions in DEM
# 2. Extract D8 flow direction
# 3. Calculate flow accumulation
# 4. Extract streams (threshold=1000 cells)
# 5. Compute HAND
```

#### 2.3.2 Run HAND Computation
```bash
python src/preprocessing/hand_calculator.py
```

**Expected Output:**
```
Step 1/5: Filling depressions...
Step 2/5: Computing flow direction...
Step 3/5: Computing flow accumulation...
Step 4/5: Extracting stream network...
Step 5/5: Computing HAND...
HAND raster saved: ~/flood_data/processed/mahanadi_hand.tif

=== HAND Statistics ===
Min HAND: 0.00 m
Max HAND: 87.34 m
Mean HAND: 4.56 m
Median HAND: 2.78 m
Pixels with HAND < 5m: 1247893 (68.4%)
```

**Deliverable:** `~/flood_data/processed/mahanadi_hand.tif`

#### 2.3.3 Extract Drainage Network Vector
```bash
python src/preprocessing/drainage_network.py
# Output: drainage_network.shp
```

**Deliverable:** `~/flood_data/processed/drainage_network.shp`

---

## 📝 TASK 2.4: Slope Calculation
**Owner:** Geospatial Engineer | **Duration:** 0.5 days | **Priority:** HIGH

### Microtasks

#### 2.4.1 Calculate Slope Raster
```python
# File: src/preprocessing/slope_aspect.py
# Uses Horn's method (3x3 moving window)
python src/preprocessing/slope_aspect.py
```

**Expected Output:**
```
Slope raster saved: ~/flood_data/processed/mahanadi_slope.tif
Mean slope: 1.34°
Max slope: 23.45°
Pixels with slope > 15°: 45231 (2.5%)
```

**Deliverable:** `~/flood_data/processed/mahanadi_slope.tif`

---

## 📝 TASK 2.5: ISRO Bhuvan Ground Truth
**Owner:** Geospatial Engineer | **Duration:** 0.5 days | **Priority:** CRITICAL

### Microtasks

#### 2.5.1 Download Flood Extent Maps
- [ ] **Cyclone Fani (May 2019):** Navigation → Archives > Cyclone > 2019 > Fani
- [ ] **Cyclone Amphan (May 2020):** Optional for additional validation

**Source:** https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php

#### 2.5.2 Store and Organize
```bash
mkdir -p ~/flood_data/raw/bhuvan/fani_2019
mkdir -p ~/flood_data/raw/bhuvan/amphan_2020
# Download .shp, .shx, .dbf, .prj files
```

#### 2.5.3 Verify Shapefile
```bash
ogrinfo -al ~/flood_data/raw/bhuvan/fani_2019/fani_flood_inundation.shp | head -20
```

**Expected Fields:**
- DISTRICT
- BLOCK
- VILLAGE
- FLOOD_DEPTH (if available)
- DATE

#### 2.5.4 Import to Database
```python
# File: scripts/import_bhuvan_to_db.py
# Reproject to WGS84 and insert into ground_truth table
python scripts/import_bhuvan_to_db.py
```

---

## 📝 TASK 2.6: Social Media Data Setup
**Owner:** Data Analyst | **Duration:** 1 day | **Priority:** MEDIUM

### Microtasks

#### 2.6.1 Twitter API Configuration
```bash
pip install tweepy==4.14.0
```

```python
# File: src/utils/config.py
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

ODISHA_BBOX = {
    "min_lat": 19.5,
    "max_lat": 21.5,
    "min_lon": 84.5,
    "max_lon": 87.0
}

DISASTER_KEYWORDS = [
    "flood", "flooding", "water logging", "cyclone fani",
    "mahanadi", "cuttack flood", "puri flood", "odisha disaster"
]
```

#### 2.6.2 Collect Historical Tweets (If API Available)
```python
# File: scripts/collect_twitter_data.py
# Query: "(flood OR flooding OR cyclone) place:Odisha lang:en -is:retweet has:geo"
# Period: 2019-05-01 to 2019-05-10
```

**Note:** Academic Research API access required for historical data.

#### 2.6.3 Fallback: Manual Georeferencing
```python
# File: scripts/geocode_tweets.py
# Use Nominatim geocoder for location mentions
```

---

## 📝 TASK 2.7: IMD Rainfall Data
**Owner:** Data Analyst | **Duration:** 0.5 days | **Priority:** MEDIUM

### Microtasks

#### 2.7.1 Download Gridded Rainfall
**Source:** https://www.imdpune.gov.in/cmpg/Griddata/Rainfall.html
- [ ] May 2019 daily rainfall (0.25° × 0.25° resolution)
- [ ] May 2020 daily rainfall

#### 2.7.2 Parse IMD ASCII Grid
```python
# File: scripts/parse_imd_rainfall.py
# Convert ASCII grid to GeoTIFF format
python scripts/parse_imd_rainfall.py
```

**Deliverable:** `~/flood_data/raw/imd/rf_ind2019_0503.tif`

---

## ✅ Phase Completion Checklist

### Processed Rasters
- [ ] `mahanadi_dem_30m.tif` - Clipped and filled DEM
- [ ] `mahanadi_hand.tif` - Height Above Nearest Drainage
- [ ] `mahanadi_slope.tif` - Slope in degrees
- [ ] `drainage_network.shp` - Vector stream network

### Ground Truth Data
- [ ] Bhuvan Cyclone Fani shapefile downloaded
- [ ] Ground truth imported to database
- [ ] Flood polygon verified in QGIS

### Auxiliary Data
- [ ] Twitter data collected (or synthetic fallback planned)
- [ ] IMD rainfall grids downloaded

---

## 🔗 Dependencies for Next Phase
- ✅ DEM, HAND, Slope rasters ready for feature extraction
- ✅ Ground truth polygon for IoU calculation
- ⏳ Feature extractor module depends on these rasters

---

## 📊 Data Quality Metrics

| Dataset | Size | Resolution | Quality Check |
|---------|------|------------|---------------|
| DEM | ~2GB | 30m | No NoData in study area |
| HAND | ~800MB | 30m | 68% pixels < 5m |
| Slope | ~800MB | 30m | Mean 1.34° |
| Bhuvan | ~50MB | Vector | Covers study area |

---

*Phase 2 Last Updated: December 30, 2025*
