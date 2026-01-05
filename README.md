# AI/ML-Enhanced Crowdsourced Flood Validation System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Enhancing Crowdsourced Flood Validation through Digital Elevation Model Constraints**

A Case Study of the Mahanadi Delta, Odisha

---

## 🌊 Overview

This repository contains the implementation of a novel **five-layer ML-enhanced validation framework** for crowdsourced flood reports, integrating:

1. **Physical Plausibility** - DEM, HAND, slope analysis (Random Forest)
2. **Statistical Consistency** - Spatial clustering (DBSCAN + XGBoost)
3. **User Reputation** - Bayesian trust scoring
4. **Social Context** - News API correlation
5. **Visual Verification** - Computer vision flood detection

**Study Area**: Mahanadi Delta, Odisha, India (Cyclone Fani 2019)

**Current Status**: 🟢 **Phase 4: Integration & Verification** (See [Detailed Project Status](./PROJECT_STATUS.md))

**Key Results**: 
- F1 Score: **1.0** at 5-15% noise levels
- F1 Score: **0.985** at 30% noise level
- Outperforms rule-based baselines by 4-25 percentage points

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 or 3.11** (Avoid Python 3.13 due to wheel compatibility issues)
- Node.js 18+ (for frontend)
- Git

### Installation

#### 1. Backend Setup

```powershell
# Create virtual environment (Python 3.11 recommended)
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment (auto-enables SQLite fallback for local dev)
Copy-Item .env.example .env
```

#### 2. Start Backend Server

```powershell
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Check:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs

#### 3. Start Frontend Dashboard

```powershell
cd src/frontend/web-dashboard
npm install
npm start
```

- **Dashboard:** http://localhost:3000

---

## 🛠️ Troubleshooting

If you encounter startup issues:

| Issue | Solution |
|-------|----------|
| `No module named uvicorn` | Run `pip install uvicorn[standard]` in your venv |
| `NameError: 'Any' not defined` | Fixed in `schemas.py` (ensure `Any` is imported from `typing`) |
| PostgreSQL Auth Failed | The system will fallback to SQLite automatically. No action needed. |
| Python 3.13 Build Errors | Use Python 3.11 (`py -3.11 -m venv .venv`) to avoid compilation issues. |

---

## 📁 Project Structure

```
odisha-flood-validation/
├── data/                    # Data directory (Git-ignored)
│   ├── raw/                 # Original downloads
│   │   ├── dem/             # FABDEM GeoTIFF tiles
│   │   ├── bhuvan/          # ISRO flood extent shapefiles
│   │   ├── social_media/    # Twitter data exports
│   │   ├── imd/             # IMD rainfall grids
│   │   └── incois/          # Tide gauge data
│   ├── processed/           # Preprocessed DEM, HAND, slope
│   └── synthetic/           # Generated experiment datasets
│
├── src/                     # Source code
│   ├── preprocessing/       # DEM processing, HAND calculation
│   ├── validation/          # 3-layer validation algorithm
│   ├── api/                 # FastAPI backend
│   ├── experiments/         # Synthetic data, baselines
│   └── utils/               # Helper functions
│
├── tests/                   # Unit and integration tests
├── notebooks/               # Jupyter notebooks
├── docs/                    # Documentation & paper
├── results/                 # Experiment outputs
├── scripts/                 # Setup and utility scripts
└── config/                  # Configuration files
```

---

## 🗺️ Data Sources

| Dataset | Source | Resolution |
|---------|--------|------------|
| DEM | [FABDEM](https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn) | 30m |
| Ground Truth | [ISRO Bhuvan](https://bhuvan.nrsc.gov.in/) | Vector |
| Flood Hazard Zones | [NRSC Flood Hazard Atlas](https://nrsc.gov.in) | District-level |
| Rainfall | [IMD](https://www.imdpune.gov.in/) | 0.25° grid |
| Social Media | Twitter API | Point data |

See [data/README.md](data/README.md) for download instructions.

---

## 🔬 Reproducing Results

```bash
# Step 1: Generate synthetic datasets (5 noise levels)
python -m src.experiments.data_generator

# Step 2: Run experiments
python -m src.experiments.runner_lite

# Step 3: View results
cat results/experiments/results.csv

# Results saved to: results/experiments/
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check (alias) |
| `GET` | `/stats` | System statistics |
| `POST` | `/users` | Create user |
| `GET` | `/users/{id}` | Get user details |
| `POST` | `/reports` | Submit flood report (auto-validated) |
| `GET` | `/reports` | List reports |
| `GET` | `/reports/nearby` | Find nearby reports |
| `POST` | `/validate-photo` | Validate flood photo (CV) |
| `POST` | `/reports/from-image` | Submit report from geotagged image |

Full API documentation: http://localhost:8000/docs

---

## 📖 Citation

If you use this code or method in your research, please cite:

```bibtex
@inproceedings{author2026flood,
  title={Enhancing Crowdsourced Flood Validation through Digital Elevation Model Constraints},
  author={Author1 and Author2 and Author3 and Author4 and Author5},
  booktitle={IEEE INDICON 2026},
  year={2026}
}
```

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 👥 Team

- **Team Lead**: Project coordination, paper writing
- **Geospatial Engineer**: DEM processing, HAND calculation
- **ML Developer**: Validation algorithm
- **Full-Stack Developer**: API, web dashboard, mobile PWA
- **Data Analyst**: Experiments, visualization

---

## 📧 Contact

For questions, contact: [your.email@university.edu]

**Project Website**: https://flood-validation-project.github.io
