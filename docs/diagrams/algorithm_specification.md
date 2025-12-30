# Algorithm Specification

## Three-Layer Flood Report Validation Algorithm

### Overview

The validation algorithm assesses crowdsourced flood reports through three complementary layers:

1. **Physical Plausibility (Layer 1)** - DEM-based terrain analysis
2. **Statistical Consistency (Layer 2)** - Spatio-temporal pattern analysis
3. **Reputation System (Layer 3)** - User trust scoring

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

### Scoring Logic

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

#### Elevation Context
```
if point is local peak (+5m vs neighbors): score = 0.2
if point is depression (-2m vs neighbors): score = 1.0
else:                                       score = 0.8
```

### Layer 1 Aggregation
```
L1_score = 0.4 × HAND_score + 0.4 × elevation_score + 0.2 × slope_score
```

---

## Layer 2: Statistical Consistency

### Purpose
Check if the report is consistent with other reports and environmental conditions.

### Components

#### Spatial Clustering
Uses radius-based neighbor search (200m default):
```
if neighbors >= 5 with similar claims: score = 1.0
if neighbors >= 3:                     score = 0.8
if neighbors >= 1:                     score = 0.6
if isolated:                           score = 0.4
```

#### Temporal Consistency
Correlates with rainfall data:
```
if rainfall_24h > 100mm: score = 1.0
if rainfall_24h > 50mm:  score = 0.8
if rainfall_24h > 10mm:  score = 0.6
if rainfall_24h > 0mm:   score = 0.4
else:                    score = 0.2  (No rain = suspicious)
```

#### Outlier Detection
Uses Z-score against nearby reports:
```
z = |depth - mean(neighbor_depths)| / std(neighbor_depths)
if z < 1.0: score = 1.0  (Consistent)
if z < 2.0: score = 0.7
else:       score = 0.2  (Anomalous)
```

### Layer 2 Aggregation
```
L2_score = 0.5 × spatial_score + 0.3 × temporal_score + 0.2 × outlier_score
```

---

## Layer 3: Reputation System

### Purpose
Weight validation by user historical accuracy using Bayesian trust.

### Trust Score Management
- Initial trust: 0.5
- After verified report: trust += 0.1
- After flagged report: trust -= 0.15
- Range: [0.0, 1.0]

### Layer 3 Score
```
L3_score = user_trust_score
```

---

## Final Score Computation

```
Final_Score = 0.4 × L1_score + 0.4 × L2_score + 0.2 × L3_score
```

### Decision Threshold
```
if Final_Score >= 0.7: status = "validated"
else:                  status = "flagged"
```

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Precision | ≥ 92% | At 15% noise level |
| Recall | ≥ 88% | |
| F1 Score | ≥ 90% | |
| IoU | ≥ 80% | Flood extent overlap |
| Latency | < 200ms | Per report validation |

---

## Pseudocode

```python
def validate_report(report, user, dem, hand, slope, recent_reports, rainfall):
    # Layer 1: Physical
    features = extract_terrain_features(report.lat, report.lon, dem, hand, slope)
    L1 = physical_validator.score(features)
    
    # Layer 2: Statistical
    neighbors = find_nearby_reports(report, recent_reports, radius=200m)
    L2 = statistical_validator.score(neighbors, rainfall)
    
    # Layer 3: Reputation
    L3 = user.trust_score
    
    # Aggregate
    final_score = 0.4*L1 + 0.4*L2 + 0.2*L3
    
    return {
        'status': 'validated' if final_score >= 0.7 else 'flagged',
        'score': final_score,
        'layers': {'L1': L1, 'L2': L2, 'L3': L3}
    }
```

---

## References

1. Rennó et al. (2008) - HAND: Height Above the Nearest Drainage
2. Hawker et al. (2022) - FABDEM: Forest And Buildings removed DEM
3. ISRO Bhuvan - Historical flood extent validation
