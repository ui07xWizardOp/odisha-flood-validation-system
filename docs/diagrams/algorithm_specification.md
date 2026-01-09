# Algorithm Specification

## Five-Layer ML-Enhanced Flood Report Validation Algorithm

### Overview

The validation algorithm assesses crowdsourced flood reports through **five complementary ML-enhanced layers**:

1. **Physical Plausibility (Layer 1)** - DEM-based terrain analysis with rule-based scoring
2. **Statistical Consistency (Layer 2)** - DBSCAN clustering + Hybrid consensus
3. **Reputation System (Layer 3)** - Trust increment/decrement scoring (+0.1/-0.15)
4. **Social Context (Layer 4)** - NewsData.io flood event correlation
5. **Visual Verification (Layer 5)** - Hybrid Ensemble (MobileNetV2 + OpenCV)

**Weight Aggregation:** A neural network learns optimal layer weights instead of fixed values.

---

## Layer 1: Physical Plausibility

### Purpose
Determine if flooding is physically possible at the reported location based on terrain characteristics.

### Input Features
| Feature | Source | Description |
|---------|--------|-------------|
| Elevation | FABDEM 30m | Height above sea level (m) |
| HAND | Computed | Height Above Nearest Drainage (m) |
| Slope | Computed | Terrain steepness (degrees) |
| Neighborhood Stats | DEM | Local elevation mean/std |

### ML Enhancement: Rule-based Scoring
- Primary: Rule-based thresholds (HAND < 10m, Slope < 15°)
- Fallback: Trained Random Forest if model available
- Model: `models/rf_physical_plausibility.pkl` (optional)

### Scoring Logic (Rule-Based Fallback)

#### HAND Check
```
if HAND > 10m: score = 0.1  (Very unlikely to flood)
if HAND > 5m:  score = 0.4  (Suspicious)
if HAND < 1m:  score = 1.0  (Very plausible)
else:          score = linear interpolation
```

#### Slope Check
```
if slope > 30°: score = 0.0  (Impossible - water flows away)
if slope > 15°: score = 0.3  (Unlikely)
else:           score = 1.0 - (0.046 × slope)
```

### Layer 1 Aggregation
```
L1_score = 0.4 × HAND_score + 0.4 × elevation_score + 0.2 × slope_score
```

**Ground Truth Boost:** If location is in ISRO Bhuvan verified flood zone: `L1 += 0.2`

---

## Layer 2: Statistical Consistency

### Purpose
Check if the report is consistent with other nearby reports using spatial clustering.

### ML Enhancement: DBSCAN + XGBoost

1. **DBSCAN Clustering** (`src/ml/models/dbscan_clustering.py`)
   - Identifies spatial clusters of flood reports
   - Parameters: `eps=0.01` (~1km), `min_samples=3`
   - Score based on cluster membership

2. **Hybrid Scoring**
   - Combines DBSCAN cluster membership with rule-based checks
   - Considers neighbor count, rainfall correlation

### Combined Scoring
```
L2_score = statistical_validator.validate(lat, lon, depth, timestamp, recent_reports, rainfall)
```

### Temporal Consistency (Rule-Based Component)
```
if rainfall_24h > 100mm: score = 1.0
if rainfall_24h > 50mm:  score = 0.8
if rainfall_24h > 10mm:  score = 0.6
if rainfall_24h > 0mm:   score = 0.4
else:                    score = 0.2  (No rain = suspicious)
```

---

## Layer 3: Reputation System

### Purpose
Weight validation by user historical accuracy using Bayesian trust.

### Trust Score Management (SimpleTrust)
- Initial trust: 0.5
- After validated report: trust += 0.1
- After flagged/rejected report: trust -= 0.15
- Range: clamped to [0.0, 1.0]

### Layer 3 Score
```
L3_score = user_trust_score
```

---

## Layer 4: Social Context (NEW)

### Purpose
Correlate reports with external news and social media signals.

### Data Sources
- NewsData.io API (flood-related headlines)
- Mock fallback for testing

### Scoring
```
if recent_flood_headlines > 3: score = 0.9
if recent_flood_headlines > 1: score = 0.6
else:                          score = 0.3
```

---

## Layer 5: Visual Verification (NEW, Optional)

### Purpose
Validate flood photos using computer vision.

### ML Model: Hybrid Ensemble Classifier
- Location: `src/ml/models/ensemble_classifier.py`
- Components:
  - MobileNetV2 CNN (45% weight)
  - HSV Water Detection - OpenCV (30% weight)
  - Texture Analysis - Laplacian variance (15% weight)
  - Edge Case Detection (glare, pools, reflections)
- Outputs: `is_flood_detected`, `confidence`, `water_coverage`

### Scoring
```
if image provided AND is_flood_detected:
    L5_score = confidence × 0.8 + water_coverage × 0.2
else:
    L5_score = 0.5  (neutral)
```

---

## Final Score Computation

### Neural Weight Network
Instead of fixed weights, a trained neural network (`models/weight_network.json`) learns optimal aggregation:

```python
layer_scores = [L1, L2, L3, L4]  # L5 applied separately
final_score = weight_network.forward(layer_scores)

# Photo boost
if L5.is_flood_detected:
    final_score += 0.1
```

### Decision Threshold
```
if Final_Score >= 0.7: status = "validated"
else:                  status = "flagged"
```

---

## Performance Results

| Noise Level | Precision | Recall | F1 Score |
|-------------|-----------|--------|----------|
| 5% | 1.000 | 1.000 | **1.000** |
| 15% | 1.000 | 1.000 | **1.000** |
| 30% | 1.000 | 0.971 | **0.985** |

---

## Pseudocode

```python
def validate_report(report, user, recent_reports, image_bytes=None):
    # Layer 1: Physical (ML + Rule-based)
    features = extract_terrain_features(report.lat, report.lon)
    L1 = physical_validator.score(features)
    if geo_service.in_verified_flood_zone(report.lat, report.lon):
        L1 += 0.2
    
    # Layer 2: Statistical (DBSCAN + XGBoost)
    L2_dbscan = dbscan.get_cluster_score(report, recent_reports)
    L2_rules = statistical_validator.score(recent_reports, rainfall)
    L2 = 0.6 * L2_dbscan + 0.4 * L2_rules
    
    # Layer 3: Reputation
    L3 = user.trust_score
    
    # Layer 4: Social Context
    L4 = social_service.get_buzz_score("Odisha")
    
    # Layer 5: Visual (optional)
    L5 = image_classifier.validate(image_bytes) if image_bytes else 0.5
    
    # Neural aggregation
    final_score = weight_network.forward([L1, L2, L3, L4])
    if L5.is_flood and L5.confidence > 0.7:
        final_score += 0.1
    
    return {
        'status': 'validated' if final_score >= 0.7 else 'flagged',
        'score': final_score
    }
```

---

## References

1. Rennó et al. (2008) - HAND: Height Above the Nearest Drainage
2. Hawker et al. (2022) - FABDEM: Forest And Buildings removed DEM
3. ISRO Bhuvan - Historical flood extent validation
4. Ester et al. (1996) - DBSCAN: Density-Based Spatial Clustering
5. Chen & Guestrin (2016) - XGBoost: Scalable Tree Boosting
