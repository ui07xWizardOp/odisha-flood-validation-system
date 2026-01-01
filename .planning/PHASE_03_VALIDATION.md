# 🧠 PHASE 3: VALIDATION ALGORITHM DEVELOPMENT
## Weeks 4-5 | Three-Layer Validation System

**Duration:** 14 days  
**Owner:** ML Developer  
**Dependencies:** Phase 2 Rasters Ready

---

## 📋 Phase Overview

| Metric | Target |
|--------|--------|
| Duration | 2 weeks |
| Effort | 50 person-hours |
| Deliverables | 5 Python modules + Unit tests |
| Risk Level | MEDIUM |

---

## 🎯 Phase Objectives

- [ ] OBJECTIVE 1: Implement Feature Extractor (elevation, HAND, slope at coordinates)
- [ ] OBJECTIVE 2: Build Layer 1: Physical Plausibility Validator
- [ ] OBJECTIVE 3: Build Layer 2: Statistical Consistency Validator
- [ ] OBJECTIVE 4: Build Layer 3: Reputation System
- [ ] OBJECTIVE 5: Create Main Orchestrator with Score Aggregation

---

## 📝 TASK 3.1: Feature Extractor Module
**Owner:** ML Developer | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 3.1.1 Create Feature Extractor Class
```python
# File: src/preprocessing/feature_extractor.py

class FeatureExtractor:
    def __init__(self, dem_path, hand_path, slope_path):
        self.dem_src = rasterio.open(dem_path)
        self.hand_src = rasterio.open(hand_path)
        self.slope_src = rasterio.open(slope_path)
```

#### 3.1.2 Implement Point Feature Extraction
- [ ] `get_elevation_at_point(lat, lon)` → Elevation in meters
- [ ] `get_hand_value(lat, lon)` → HAND value
- [ ] `get_slope_value(lat, lon)` → Slope in degrees

#### 3.1.3 Implement Neighborhood Analysis
- [ ] `get_neighborhood_stats(lat, lon, radius_m=100)` → mean, std, min, max

#### 3.1.4 Combine All Features
```python
def extract_all_features(self, lat, lon):
    return {
        'elevation': self.get_elevation_at_point(lat, lon),
        'hand': self.get_hand_value(lat, lon),
        'slope': self.get_slope_value(lat, lon),
        'elevation_neighborhood_mean': ...,
        'elevation_neighborhood_std': ...,
        'elevation_diff_from_neighbors': ...
    }
```

#### 3.1.5 Unit Test
```python
# Test at Cuttack city center: 20.4625°N, 85.8830°E
# Expected: elevation ~5m, HAND ~2m, slope ~1°
```

---

## 📝 TASK 3.2: Layer 1 - Physical Plausibility
**Owner:** ML Developer | **Duration:** 3 days | **Priority:** CRITICAL

### Microtasks

#### 3.2.1 Define Thresholds
```python
# File: src/validation/layer1_physical.py

MAX_ELEVATION_DIFF = 10.0  # meters
HAND_THRESHOLD = 5.0       # meters
STEEP_SLOPE = 15.0         # degrees
```

#### 3.2.2 Elevation Consistency Check
```python
def check_elevation_consistency(self, lat, lon, reported_depth):
    """
    Logic: If point is much higher than neighbors but reports flood,
    reduce score (suspicious).
    
    Score Range: 0-1
    """
```

**Scoring Logic:**
| Condition | Score |
|-----------|-------|
| Point in depression (elev_diff < -10m) | 1.0 |
| Normal elevation range | 0.8 |
| Point on local high (elev_diff > 10m) | 0.0-0.5 |

#### 3.2.3 HAND Plausibility Check
```python
def check_hand_plausibility(self, lat, lon, reported_depth):
    """
    Logic: Locations far above drainage are unlikely to flood.
    
    HAND > 10m + claiming flood = Very suspicious (0.1)
    HAND > 5m + claiming flood = Somewhat suspicious (0.5)
    HAND < 5m + claiming flood = Plausible (1.0)
    """
```

#### 3.2.4 Slope Check
```python
def check_slope_plausibility(self, lat, lon, reported_depth):
    """
    Logic: Steep slopes don't retain standing water.
    
    Slope > 30° = Very suspicious (0.0)
    Slope > 15° = Suspicious (0.4)
    Slope < 15° = Plausible (1.0)
    """
```

#### 3.2.5 Aggregate Layer 1 Score
```python
def validate(self, lat, lon, reported_depth):
    weights = {'elevation': 0.4, 'hand': 0.4, 'slope': 0.2}
    
    layer1_score = (
        weights['elevation'] * elev_check['score'] +
        weights['hand'] * hand_check['score'] +
        weights['slope'] * slope_check['score']
    )
    return {'layer1_score': layer1_score, ...}
```

#### 3.2.6 Unit Tests
- [ ] Low-lying area with flood → High score (>0.8)
- [ ] Hilltop with flood claim → Low score (<0.3)
- [ ] Steep slope with flood claim → Very low score (<0.2)

---

## 📝 TASK 3.3: Layer 2 - Statistical Consistency
**Owner:** ML Developer | **Duration:** 3 days | **Priority:** HIGH

### Microtasks

#### 3.3.1 Spatial Clustering Check
```python
# File: src/validation/layer2_statistical.py

def check_spatial_clustering(self, lat, lon, reported_depth, radius_m=200):
    """
    Logic: Find nearby reports and check consensus.
    
    >80% neighbors agree = Score 1.0
    50-80% agree = Score 0.7
    30-50% agree = Score 0.4
    <30% agree = Score 0.2
    """
```

#### 3.3.2 Temporal Consistency Check
```python
def check_temporal_consistency(self, lat, lon, timestamp, rainfall_data):
    """
    Logic: Flood reports should come AFTER rainfall.
    
    >100mm rain in 24h = Score 1.0
    50-100mm = Score 0.8
    10-50mm = Score 0.5
    <10mm = Score 0.2
    """
```

#### 3.3.3 Outlier Detection
```python
def check_outlier_detection(self, lat, lon, reported_depth):
    """
    Use Isolation Forest to detect anomalous depth values.
    
    Normal prediction = Score 0.9
    Outlier prediction = Score 0.2
    """
    from sklearn.ensemble import IsolationForest
    clf = IsolationForest(contamination=0.1)
```

#### 3.3.4 Aggregate Layer 2 Score
```python
def validate(self, lat, lon, depth, timestamp, rainfall_data):
    weights = {'spatial': 0.5, 'temporal': 0.3, 'outlier': 0.2}
    
    layer2_score = (
        weights['spatial'] * spatial['score'] +
        weights['temporal'] * temporal['score'] +
        weights['outlier'] * outlier['score']
    )
```

#### 3.3.5 Unit Tests
- [ ] Report in cluster of similar reports → High score
- [ ] Isolated report with no neighbors → Neutral score (0.5)
- [ ] Outlier depth in cluster → Low score

---

## 📝 TASK 3.4: Layer 3 - Reputation System
**Owner:** ML Developer | **Duration:** 2 days | **Priority:** MEDIUM

### Microtasks

#### 3.4.1 Trust Score Management
```python
# File: src/validation/layer3_reputation.py

TRUST_INCREMENT = 0.1   # Reward for verified report
TRUST_DECREMENT = 0.15  # Penalty for flagged report
INITIAL_TRUST = 0.5     # New user starting trust
MIN_TRUST = 0.0
MAX_TRUST = 1.0
```

#### 3.4.2 Get User Trust Score
```python
def get_user_trust_score(self, user_id):
    """Query database for current trust score."""
    query = "SELECT trust_score FROM users WHERE user_id = ?"
```

#### 3.4.3 Update Trust Score
```python
def update_trust_score(self, user_id, was_verified):
    """
    After validation:
    - Verified report: trust += 0.1
    - Flagged report: trust -= 0.15
    """
```

#### 3.4.4 Experience Bonus
```python
def validate(self, user_id):
    """
    Users with >50 reports: +0.1 bonus
    Users with >20 reports: +0.05 bonus
    New users: no bonus
    """
```

---

## 📝 TASK 3.5: Main Orchestrator
**Owner:** ML Developer | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 3.5.1 Create FloodReportValidator Class
```python
# File: src/validation/validator.py

class FloodReportValidator:
    LAYER_WEIGHTS = {
        'physical': 0.4,
        'statistical': 0.4,
        'reputation': 0.2
    }
    
    VALIDATION_THRESHOLD = 0.7
```

#### 3.5.2 Combine All Three Layers
```python
def validate_report(self, user_id, lat, lon, depth, timestamp):
    layer1 = self.layer1.validate(lat, lon, depth)
    layer2 = self.layer2.validate(lat, lon, depth, timestamp)
    layer3 = self.layer3.validate(user_id)
    
    final_score = (
        0.4 * layer1['layer1_score'] +
        0.4 * layer2['layer2_score'] +
        0.2 * layer3['layer3_score']
    )
    
    if final_score >= 0.7:
        return {'status': 'validated', 'score': final_score}
    else:
        return {'status': 'flagged', 'score': final_score}
```

#### 3.5.3 Batch Validation
```python
def validate_batch(self, reports_df):
    """Validate multiple reports efficiently."""
```

#### 3.5.4 Database Persistence
```python
def save_validation_to_database(self, result, report_id):
    """Save validation metadata to validation_metadata table."""
```

---

## 📝 TASK 3.6: Comprehensive Testing
**Owner:** ML Developer | **Duration:** 2 days | **Priority:** HIGH

### Microtasks

#### 3.6.1 Create Test Suite
```python
# File: tests/test_validation.py

def test_low_lying_flood_report():
    """True positive should score high."""
    result = validator.validate(lat=20.46, lon=85.88, depth=1.5)
    assert result['layer1_score'] > 0.8

def test_hilltop_flood_claim():
    """False positive should be flagged."""
    result = validator.validate(lat=20.50, lon=85.90, depth=2.0)
    assert result['layer1_score'] < 0.4
```

#### 3.6.2 Integration Tests
- [ ] End-to-end validation pipeline
- [ ] Database write/read cycle
- [ ] Batch processing with 100 reports

#### 3.6.3 Performance Benchmarks
```python
# Target: <200ms per report on standard hardware
import time
start = time.time()
for _ in range(100):
    validator.validate_report(...)
print(f"Avg time: {(time.time()-start)/100*1000:.1f}ms")
```

---

## ✅ Phase Completion Checklist

### Code Modules
- [ ] `src/preprocessing/feature_extractor.py` - Raster feature extraction
- [ ] `src/validation/layer1_physical.py` - DEM-based checks
- [ ] `src/validation/layer2_statistical.py` - Consensus checks
- [ ] `src/validation/layer3_reputation.py` - Trust scoring
- [ ] `src/validation/validator.py` - Main orchestrator

### Tests
- [ ] Unit tests for each module
- [ ] Integration test for full pipeline
- [ ] Performance benchmark < 200ms

### Documentation
- [ ] Docstrings for all public methods
- [ ] Algorithm specification document

---

## 🔗 Dependencies for Next Phase
- ✅ Validation algorithm ready for API integration
- ✅ Feature extractor available for experiments
- ⏳ API endpoints will wrap validator class

---

## 📊 Algorithm Performance Targets

| Check | Weight | Expected Accuracy |
|-------|--------|-------------------|
| Elevation | 40% of L1 | 85% |
| HAND | 40% of L1 | 90% |
| Slope | 20% of L1 | 95% |
| Spatial | 50% of L2 | 80% |
| Temporal | 30% of L2 | 75% |
| Outlier | 20% of L2 | 70% |
| Trust | 100% of L3 | N/A (adaptive) |

**Overall Target:** 92% precision at 15% noise

---

*Phase 3 Last Updated: December 30, 2025*
