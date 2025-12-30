# 📄 PHASE 5: EXPERIMENTS, DOCUMENTATION & FINAL DELIVERY
## Weeks 8-10 | Synthetic Data, Experiments, Paper Writing, Demo

**Duration:** 21 days  
**Owner:** All Members  
**Dependencies:** Phase 4 System Complete

---

## 📋 Phase Overview

| Metric | Target |
|--------|--------|
| Duration | 3 weeks |
| Effort | 80 person-hours |
| Deliverables | Paper + Video + Live Demo |
| Risk Level | HIGH (Deadline pressure) |

---

## 🎯 Phase Objectives

- [ ] OBJECTIVE 1: Generate synthetic datasets with controlled noise levels
- [ ] OBJECTIVE 2: Implement baseline methods for comparison
- [ ] OBJECTIVE 3: Run comprehensive experiments and collect metrics
- [ ] OBJECTIVE 4: Write and submit research paper (IEEE format)
- [ ] OBJECTIVE 5: Prepare and rehearse SIH demo presentation

---

## 📝 TASK 5.1: Synthetic Dataset Generation
**Owner:** Data Analyst | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 5.1.1 Create Synthetic Data Generator
```python
# File: src/experiments/generate_synthetic_data.py

class SyntheticDataGenerator:
    def __init__(self, dem_path, ground_truth_polygon, event_date):
        """Initialize with DEM and Bhuvan ground truth."""
```

#### 5.1.2 Generate Report Types
| Type | Description | Location | Claims Flood |
|------|-------------|----------|--------------|
| True Positive | Real flood | Inside polygon | Yes |
| True Negative | Real safe | Outside polygon | No |
| False Positive | Fake flood | Outside polygon | Yes (noise) |
| False Negative | Missed flood | Inside polygon | No (noise) |

#### 5.1.3 Generate Datasets at Different Noise Levels
```python
for noise in [5, 10, 15, 20, 30]:
    dataset = generator.generate_full_dataset(
        total_reports=1000,
        noise_percentage=noise
    )
    dataset.to_csv(f"crowd_reports_noise_{noise}pct.csv")
```

**Deliverables:**
- [ ] `crowd_reports_noise_5pct.csv`
- [ ] `crowd_reports_noise_10pct.csv`
- [ ] `crowd_reports_noise_15pct.csv`
- [ ] `crowd_reports_noise_20pct.csv`
- [ ] `crowd_reports_noise_30pct.csv`

#### 5.1.4 User Trust Simulation
```python
# File: src/experiments/simulate_user_trust.py
# Simulate 100 users with varying reliability:
# - 70% reliable (accuracy 0.8-0.95)
# - 20% average (accuracy 0.5-0.8)
# - 10% unreliable (accuracy 0.1-0.5)
```

---

## 📝 TASK 5.2: Baseline Implementation
**Owner:** ML Developer | **Duration:** 1 day | **Priority:** HIGH

### Microtasks

#### 5.2.1 Create Baseline Validators
```python
# File: src/experiments/baseline_methods.py

class NoValidationBaseline:
    """Accept all reports without validation."""
    
class PureMLBaseline:
    """Isolation Forest on (lat, lon, depth) - no DEM."""
    
class DEMOnlyBaseline:
    """Layer 1 only - no consensus/reputation."""
    
class RandomValidation:
    """Random 70% acceptance (sanity check)."""
```

#### 5.2.2 Factory Function
```python
def get_baseline_validator(method_name):
    methods = {
        'none': NoValidationBaseline,
        'pure_ml': PureMLBaseline,
        'dem_only': DEMOnlyBaseline,
        'random': RandomValidation
    }
```

---

## 📝 TASK 5.3: Metrics Calculation
**Owner:** Data Analyst | **Duration:** 1 day | **Priority:** HIGH

### Microtasks

#### 5.3.1 Implement Metrics Suite
```python
# File: src/utils/metrics.py

class ValidationMetrics:
    def calculate_classification_metrics(y_true, y_pred, y_scores):
        """Returns: precision, recall, F1, specificity, ROC-AUC"""
    
    def calculate_iou(predicted_polygon, ground_truth_polygon):
        """Intersection over Union for flood extent."""
    
    def generate_roc_curve_data(y_true, y_scores):
        """For plotting ROC curves."""
```

#### 5.3.2 IoU Calculation
```python
def create_flood_extent_polygon(validated_reports, buffer_distance=0.01):
    """Create polygon from buffered validated flood points."""
    points = [Point(lon, lat).buffer(buffer_distance) for ...]
    return unary_union(points)
```

---

## 📝 TASK 5.4: Experiment Execution
**Owner:** ML Developer + Data Analyst | **Duration:** 3 days | **Priority:** CRITICAL

### Microtasks

#### 5.4.1 Create Experiment Runner
```python
# File: src/experiments/run_experiments.py

class ExperimentRunner:
    def run_single_experiment(self, dataset_path, method):
        """Run one experiment configuration."""
    
    def run_noise_sensitivity_analysis(self, noise_levels=[5,10,15,20,30]):
        """Test all methods across noise levels."""
```

#### 5.4.2 Run All Experiments
```bash
python src/experiments/run_experiments.py
# Output: results/experiments/noise_sensitivity_summary.csv
```

#### 5.4.3 Expected Results
| Method | Precision | Recall | F1 | IoU |
|--------|-----------|--------|-----|-----|
| No Validation | 85.0% | 100% | 91.9% | 62.3% |
| Pure ML | 67.4% | 82.1% | 74.0% | 54.8% |
| DEM Only | 88.3% | 79.5% | 83.7% | 71.2% |
| **Proposed** | **92.3%** | **88.7%** | **90.5%** | **82.4%** |

#### 5.4.4 Generate Comparison Plots
```python
runner.generate_comparison_plots(results)
# Output: metrics_vs_noise.png, iou_comparison.png
```

---

## 📝 TASK 5.5: Paper Writing
**Owner:** Team Lead + All Members | **Duration:** 5 days | **Priority:** CRITICAL

### Microtasks

#### 5.5.1 Setup LaTeX Environment
- [ ] Create Overleaf project with IEEE template
- [ ] Add all team members as collaborators
- [ ] Setup bibliography file

#### 5.5.2 Section Assignments
| Section | Owner | Due Date |
|---------|-------|----------|
| Abstract (200 words) | Team Lead | Week 9 Day 1 |
| Introduction | Team Lead | Week 9 Day 2 |
| Related Work | Data Analyst | Week 9 Day 2 |
| Methodology | ML Developer | Week 9 Day 3 |
| Experiments | Data Analyst | Week 9 Day 4 |
| Results | ML Developer | Week 9 Day 4 |
| Discussion | Team Lead | Week 9 Day 5 |
| Conclusion | Team Lead | Week 9 Day 6 |

#### 5.5.3 Figures to Create
- [ ] System architecture diagram (vector PDF)
- [ ] Algorithm flowchart
- [ ] F1 vs noise level graph
- [ ] IoU comparison bar chart
- [ ] ROC curves for all methods
- [ ] Study area map with DEM overlay
- [ ] Dashboard/PWA screenshots

#### 5.5.4 Tables to Create
- [ ] Table 1: Validation performance at 15% noise
- [ ] Table 2: Ablation study (each layer contribution)
- [ ] Table 3: Hyperparameters

#### 5.5.5 Paper Checklist
- [ ] All figures have captions
- [ ] All tables are referenced in text
- [ ] References in IEEE format
- [ ] Word count < 4000 (8 pages)
- [ ] Proofread by all members

---

## 📝 TASK 5.6: Video Demo Creation
**Owner:** Full-Stack Dev | **Duration:** 1 day | **Priority:** HIGH

### Microtasks

#### 5.6.1 Demo Script
```
Duration: 3 minutes
Sections:
1. Problem introduction (30s)
2. System demo - online submission (45s)
3. System demo - offline mode (45s)
4. Dashboard walkthrough (45s)
5. Results summary (15s)
```

#### 5.6.2 Recording Setup
- [ ] Screen recording software (OBS/Loom)
- [ ] 1080p resolution
- [ ] Microphone for voiceover
- [ ] Clean desktop background

#### 5.6.3 Post-Production
- [ ] Add intro/outro slides
- [ ] Add subtitles
- [ ] Upload to YouTube (unlisted)
- [ ] Create thumbnail

---

## 📝 TASK 5.7: Live Demo Preparation
**Owner:** All Members | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 5.7.1 Deploy Applications
- [ ] Web Dashboard → Vercel/Netlify
- [ ] API → Render/Railway (free tier)
- [ ] Mobile PWA → Public URL
- [ ] Pre-load demo database

#### 5.7.2 Presentation Slides
```
Slides: 10 max
1. Title + Team
2. Problem Statement
3. Our Solution (3-layer diagram)
4. Demo Screenshot 1: Map
5. Demo Screenshot 2: Validation
6. Offline Capability
7. Results Graph
8. Comparison Table
9. Future Work
10. Thank You + QR Code
```

#### 5.7.3 Demo Script Rehearsal
| Time | Speaker | Content |
|------|---------|---------|
| 0:00-0:30 | Team Lead | Hook + Problem |
| 0:30-1:30 | Data Analyst | Problem stats |
| 1:30-3:30 | ML Dev + Geo Eng | Technical demo |
| 3:30-5:00 | Full-Stack Dev | Offline demo |
| 5:00-6:00 | Team Lead | Results |
| 6:00-6:30 | Team Lead | Why we'll win |
| 6:30-8:00 | All | Q&A |

#### 5.7.4 Pre-Demo Checklist
- [ ] Laptop fully charged + backup battery
- [ ] Internet hotspot as backup
- [ ] API server running on cloud
- [ ] Demo database pre-loaded
- [ ] Phone with PWA tested
- [ ] Offline mode tested
- [ ] Slides in 2 browsers
- [ ] Team roles practiced 3x
- [ ] Water bottle 💧

---

## 📝 TASK 5.8: Final Deliverables
**Owner:** Team Lead | **Duration:** 1 day | **Priority:** CRITICAL

### Microtasks

#### 5.8.1 Research Paper
- [ ] Main paper (8 pages IEEE format)
- [ ] Supplementary material (4 pages)
- [ ] PDF generated without errors

#### 5.8.2 Code & Data
- [ ] GitHub repository cleaned
- [ ] README.md complete
- [ ] All branches merged to main
- [ ] Release tagged (v1.0.0)
- [ ] Synthetic datasets on Zenodo

#### 5.8.3 Demo Materials
- [ ] Video demo on YouTube
- [ ] Live demo URLs working
- [ ] Presentation slides ready

#### 5.8.4 Documentation
- [ ] API documentation (Swagger)
- [ ] Architecture diagrams
- [ ] Database schema diagram

---

## ✅ Final Checklist

### Week 8 Milestones
- [ ] All synthetic datasets generated
- [ ] All baseline methods implemented
- [ ] All experiments run
- [ ] All figures generated

### Week 9 Milestones
- [ ] Paper sections 1-5 drafted
- [ ] Paper sections 6-7 drafted
- [ ] Paper fully integrated
- [ ] Internal review complete

### Week 10 Milestones
- [ ] Paper proofread and submitted
- [ ] Video demo recorded
- [ ] Live demo deployed
- [ ] Presentation rehearsed 3x
- [ ] All deliverables archived

---

## 📊 Success Criteria

### Paper Quality
| Metric | Target |
|--------|--------|
| Novelty | DEM-based validation (unique) |
| Results | 92%+ precision at 15% noise |
| Writing | Clear, IEEE-compliant |
| Figures | Publication-quality |

### Demo Quality
| Metric | Target |
|--------|--------|
| Stability | No crashes in 5 min demo |
| Speed | < 2s validation response |
| Offline | Works in airplane mode |
| Visual | Professional UI |

### Team Readiness
| Metric | Target |
|--------|--------|
| Rehearsals | 3 full run-throughs |
| Q&A Prep | 20+ prepared answers |
| Backup Plans | Offline demo ready |

---

## 🏆 Post-Submission

- [ ] 🎉 Team celebration!
- [ ] LinkedIn posts announcing project
- [ ] Twitter thread with results
- [ ] Update personal portfolios
- [ ] Prepare for conference (if accepted)

---

*Phase 5 Last Updated: December 30, 2025*  
*Status: 85% complete*  
*Days to Deadline: 7*
