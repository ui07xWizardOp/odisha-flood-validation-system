# 🏗️ PHASE 1: FOUNDATION SETUP
## Weeks 1-2 | Environment & Repository Initialization

**Duration:** 14 days  
**Owner:** Team Lead + All Members  
**Dependencies:** None (Starting phase)

---

## 📋 Phase Overview

| Metric | Target |
|--------|--------|
| Duration | 2 weeks |
| Effort | 40 person-hours |
| Deliverables | 5 |
| Risk Level | LOW |

---

## 🎯 Phase Objectives

- [x] OBJECTIVE 1: Complete development environment setup for all 5 team members
- [ ] OBJECTIVE 2: Initialize GitHub repository with proper structure
- [ ] OBJECTIVE 3: Setup PostgreSQL database with PostGIS extension
- [ ] OBJECTIVE 4: Establish team communication protocols
- [ ] OBJECTIVE 5: Create Google Drive organization structure

---

## 📝 TASK 1.1: Development Environment Setup
**Owner:** All Members | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 1.1.1 System Requirements Verification
- [ ] Verify OS: Ubuntu 22.04 LTS / Windows 11 with WSL2 / macOS Ventura+
- [ ] Check RAM: Minimum 16GB (32GB for Geospatial Engineer)
- [ ] Ensure Storage: 100GB free space for DEM data
- [ ] Test Internet: Stable connection for API access

#### 1.1.2 Python Environment Setup
```bash
# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Create project environment
conda create -n flood-validation python=3.10 -y
conda activate flood-validation

# Install core packages
pip install pandas==2.1.0 numpy==1.24.3 matplotlib==3.7.2 seaborn==0.12.2
pip install scikit-learn==1.3.0 scipy==1.11.1
pip install geopandas==0.13.2 rasterio==1.3.8 shapely==2.0.1
pip install psycopg2-binary==2.9.7 sqlalchemy==2.0.20
pip install fastapi==0.103.1 uvicorn==0.23.2 pydantic==2.3.0
pip install requests==2.31.0 python-dotenv==1.0.0
pip install jupyterlab==4.0.5

# Export environment
conda env export > environment.yml
```

**Verification:**
- [ ] Run `python --version` → Should be 3.10.x
- [ ] Run `pip list | grep pandas` → Should show 2.1.0
- [ ] Run `jupyter lab` → Should open in browser

#### 1.1.3 Geospatial Tools (Geospatial Engineer)
```bash
# Install QGIS 3.34 LTS
sudo apt-get update
sudo apt-get install qgis qgis-plugin-grass

# Install WhiteboxTools
wget https://www.whiteboxgeo.com/WBT_Linux/WhiteboxTools_linux_amd64.zip
unzip WhiteboxTools_linux_amd64.zip -d ~/whiteboxtools
echo 'export PATH=$PATH:~/whiteboxtools' >> ~/.bashrc
source ~/.bashrc

# Install GDAL
conda install -c conda-forge gdal=3.7.1

# Verify installations
gdalinfo --version
qgis --version
whitebox_tools --version
```

**Verification:**
- [ ] `gdalinfo --version` → GDAL 3.7.x
- [ ] `whitebox_tools --version` → WhiteboxTools 2.x

#### 1.1.4 Frontend Setup (Full-Stack Developer)
```bash
# Install Node.js 20 LTS
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# Install global tools
npm install -g yarn@1.22.19
npm install -g @react-native-community/cli

# Verify
node --version  # Should be v20.x.x
yarn --version  # Should be 1.22.19
```

---

## 📝 TASK 1.2: GitHub Repository Initialization
**Owner:** Team Lead | **Duration:** 1 day | **Priority:** CRITICAL

### Microtasks

#### 1.2.1 Create Repository Structure
```bash
mkdir odisha-flood-validation && cd odisha-flood-validation
git init
git branch -M main

# Create directory structure
mkdir -p {data/{raw,processed,synthetic},src/{preprocessing,validation,api,frontend},notebooks,docs,tests,results/{figures,tables}}
```

#### 1.2.2 Create .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.env
venv/
*.egg-info/

# Data (too large for Git)
data/raw/
data/processed/*.tif
data/processed/*.shp

# Jupyter
.ipynb_checkpoints/
*.ipynb

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

#### 1.2.3 Setup Branch Strategy
```
main                    # Production-ready code only
├── develop             # Integration branch
    ├── feature/dem-processing
    ├── feature/validation-algorithm
    ├── feature/api-endpoints
    └── feature/frontend-dashboard
```

#### 1.2.4 Configure Git for All Members
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global core.editor "nano"

# Setup SSH keys
ssh-keygen -t ed25519 -C "your.email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
# Add public key to GitHub: cat ~/.ssh/id_ed25519.pub
```

**Verification:**
- [ ] All 5 members can clone the repository
- [ ] All members can create feature branches
- [ ] First test commit pushed successfully

---

## 📝 TASK 1.3: Database Setup
**Owner:** Team Lead + Full-Stack Dev | **Duration:** 1 day | **Priority:** HIGH

### Microtasks

#### 1.3.1 Install PostgreSQL with PostGIS
```bash
sudo apt-get install postgresql-15 postgresql-15-postgis-3
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 1.3.2 Create Project Database
```sql
-- Run as postgres user
sudo -u postgres psql

CREATE DATABASE flood_validation;
CREATE USER flood_admin WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE flood_validation TO flood_admin;
\c flood_validation
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
\q
```

#### 1.3.3 Create Core Tables
```sql
-- Users and Trust Scores Table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    trust_score REAL DEFAULT 0.5 CHECK (trust_score >= 0 AND trust_score <= 1),
    total_reports INTEGER DEFAULT 0,
    verified_reports INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);

-- Flood Reports Table
CREATE TABLE flood_reports (
    report_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    depth_meters REAL CHECK (depth_meters >= 0),
    timestamp TIMESTAMP NOT NULL,
    photo_url TEXT,
    description TEXT,
    validation_status VARCHAR(20) CHECK (validation_status IN ('pending', 'validated', 'flagged', 'rejected')),
    final_score REAL,
    physical_score REAL,
    statistical_score REAL,
    reputation_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX idx_reports_location ON flood_reports USING GIST(location);
CREATE INDEX idx_reports_timestamp ON flood_reports(timestamp);
```

**Verification:**
- [ ] Connect: `psql -U flood_admin -d flood_validation`
- [ ] Run: `SELECT PostGIS_Version();` → Should return version
- [ ] Insert test user and verify

---

## 📝 TASK 1.4: Team Communication Setup
**Owner:** Team Lead | **Duration:** 0.5 days | **Priority:** MEDIUM

### Microtasks

#### 1.4.1 Slack/Discord Channel Structure
```
#general              - Team-wide announcements
#dev-backend          - API, database, processing
#dev-frontend         - Web & mobile development
#data-geospatial      - DEM, QGIS, raster processing
#ml-algorithm         - Validation logic, experiments
#paper-writing        - LaTeX, figures, references
#random               - Off-topic, team bonding
```

#### 1.4.2 Meeting Schedule
| Meeting | Day | Time | Duration | Purpose |
|---------|-----|------|----------|---------|
| Weekly Standup | Monday | 8:00 PM IST | 30 min | Progress, blockers |
| Code Review | Friday | 9:00 PM IST | 15 min | Merge PRs |
| Mid-Phase Review | Bi-weekly | Saturday | 60 min | Milestones |
| Paper Writing | Week 9-10 | TBD | 2 hours | Overleaf collab |

#### 1.4.3 Daily Standup Format (Async)
```markdown
**[Your Name] - [Date]**

✅ **Completed Yesterday:**
- Task 1
- Task 2

🔄 **Working on Today:**
- Task 3

🚧 **Blockers:**
- Issue 1 (needs help from [Person])
```

---

## 📝 TASK 1.5: Cloud Resources Setup
**Owner:** Team Lead | **Duration:** 0.5 days | **Priority:** MEDIUM

### Microtasks

#### 1.5.1 Google Cloud Platform (Optional)
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Enable Earth Engine
pip install earthengine-api
earthengine authenticate
```

#### 1.5.2 Google Drive Organization
```
Odisha Flood Validation Project/
├── 1. Literature/
│   ├── Core Papers (5 must-reads)
│   └── Supplementary Papers
├── 2. Data/
│   ├── DEM_FABDEM/
│   ├── ISRO_Bhuvan_Shapefiles/
│   ├── Social_Media_Historical/
│   └── Cyclone_Reports/
├── 3. Meeting Notes/
│   ├── Week_01_Kickoff.md
│   └── ... (weekly)
├── 4. Presentations/
└── 5. Paper Drafts/
```

---

## ✅ Phase Completion Checklist

### End of Week 1
- [ ] All 5 members have working Python environment
- [ ] Git repository initialized with proper structure
- [ ] Database running with PostGIS extension
- [ ] Slack/Discord channels created

### End of Week 2
- [ ] All members can push/pull from GitHub
- [ ] Database schema created and tested
- [ ] Geospatial tools verified (GDAL, WhiteboxTools)
- [ ] Google Drive organized with folders
- [ ] First team standup completed

---

## 🔗 Dependencies for Next Phase
- ✅ Python environment with geospatial packages
- ✅ PostgreSQL database ready for data ingestion
- ✅ GitHub repository for collaborative development
- ⏳ Ready to download DEM data (Phase 2)

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Environment Setup | 5/5 members | Run verification commands |
| Git Access | 100% | Everyone can push |
| Database Health | Operational | `SELECT 1` succeeds |
| Team Sync | 2 standups | Meeting attendance |

---

*Phase 1 Last Updated: December 30, 2025*
