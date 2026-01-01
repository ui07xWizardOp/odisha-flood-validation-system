# AI/ML-Enhanced Crowdsourced Flood Validation System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Enhancing Crowdsourced Flood Validation through Digital Elevation Model Constraints**

A Case Study of the Mahanadi Delta, Odisha

---

## 🌊 Overview

This repository contains the implementation of a novel three-layer validation framework for crowdsourced flood reports, integrating:

1. **Physical Plausibility** - DEM, HAND, slope analysis
2. **Statistical Consistency** - Spatial/temporal clustering
3. **User Reputation** - Trust score weighting

**Study Area**: Mahanadi Delta, Odisha, India (Cyclone Fani 2019)

**Key Result**: 92.3% precision at 15% noise level, outperforming baselines by 4-25 percentage points.

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
| Rainfall | [IMD](https://www.imdpune.gov.in/) | 0.25° grid |
| Social Media | Twitter API | Point data |

See [data/README.md](data/README.md) for download instructions.

---

## 🔬 Reproducing Results

```bash
# Step 1: Generate synthetic datasets
python src/experiments/generate_synthetic_data.py

# Step 2: Run noise sensitivity analysis
python src/experiments/run_experiments.py

# Step 3: Generate paper figures
python src/experiments/generate_figures.py

# Results saved to: results/experiments/
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/validate` | Validate a flood report |
| `POST` | `/reports` | Submit a new report |
| `GET` | `/reports/{id}` | Get report details |
| `GET` | `/reports/nearby/{lat}/{lon}` | Find nearby reports |
| `GET` | `/analytics/stats` | System statistics |
| `GET` | `/analytics/leaderboard` | Top contributors |

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
