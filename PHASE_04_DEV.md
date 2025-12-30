# 💻 PHASE 4: BACKEND & FRONTEND DEVELOPMENT
## Weeks 6-7 | API, Web Dashboard, Mobile PWA

**Duration:** 14 days  
**Owner:** Full-Stack Developer  
**Dependencies:** Phase 3 Validator Ready

---

## 📋 Phase Overview

| Metric | Target |
|--------|--------|
| Duration | 2 weeks |
| Effort | 60 person-hours |
| Deliverables | API + Web Dashboard + Mobile PWA |
| Risk Level | MEDIUM |

---

## 🎯 Phase Objectives

- [ ] OBJECTIVE 1: Build FastAPI backend with validation endpoints
- [ ] OBJECTIVE 2: Create database helper classes with ORM
- [ ] OBJECTIVE 3: Develop React web dashboard with map visualization
- [ ] OBJECTIVE 4: Build offline-capable Progressive Web App
- [ ] OBJECTIVE 5: Implement real-time sync architecture

---

## 📝 TASK 4.1: Database ORM Layer
**Owner:** Full-Stack Dev | **Duration:** 1 day | **Priority:** CRITICAL

### Microtasks

#### 4.1.1 Create SQLAlchemy Models
```python
# File: src/api/database.py

from sqlalchemy import Column, Integer, Float, String, DateTime
from geoalchemy2 import Geography

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    trust_score = Column(Float, default=0.5)
    total_reports = Column(Integer, default=0)

class FloodReport(Base):
    __tablename__ = 'flood_reports'
    report_id = Column(Integer, primary_key=True)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    depth_meters = Column(Float)
    validation_status = Column(String(20))
    final_score = Column(Float)
```

#### 4.1.2 Create DatabaseManager Class
- [ ] `add_user(username, email)` → user_id
- [ ] `add_flood_report(user_id, lat, lon, depth, timestamp)` → report_id
- [ ] `update_report_validation(report_id, validation_result)`
- [ ] `get_reports_for_validation(status, limit)`
- [ ] `get_validated_reports_for_mapping(min_score)`

#### 4.1.3 Create Database Functions
```sql
-- File: scripts/database_functions.sql

CREATE FUNCTION get_reports_within_radius(
    center_lat REAL, center_lon REAL, radius_meters INTEGER
) RETURNS TABLE(...);

CREATE FUNCTION get_user_leaderboard(limit_count INTEGER);
```

---

## 📝 TASK 4.2: Pydantic Schemas
**Owner:** Full-Stack Dev | **Duration:** 0.5 days | **Priority:** HIGH

### Microtasks

#### 4.2.1 Create Request/Response Models
```python
# File: src/api/models.py

class FloodReportCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    latitude: float = Field(..., ge=19.5, le=21.5)  # Odisha bounds
    longitude: float = Field(..., ge=84.5, le=87.0)
    depth_meters: float = Field(..., ge=0, le=10)
    timestamp: datetime
    description: Optional[str] = Field(None, max_length=500)

class ValidationResponse(BaseModel):
    report_id: int
    final_score: float
    decision: str  # 'ACCEPT' or 'REVIEW_NEEDED'
    validation_status: str
    layer_scores: Dict[str, float]
```

---

## 📝 TASK 4.3: FastAPI Application
**Owner:** Full-Stack Dev | **Duration:** 2 days | **Priority:** CRITICAL

### Microtasks

#### 4.3.1 Initialize FastAPI App
```python
# File: src/api/main.py

app = FastAPI(
    title="Odisha Flood Validation API",
    description="AI/ML-Enhanced Crowdsourced Flood Validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

#### 4.3.2 User Endpoints
- [ ] `POST /users` - Create new user account
- [ ] `GET /users/{user_id}` - Get user info and stats

#### 4.3.3 Report Endpoints
- [ ] `POST /reports` - Submit and validate flood report
- [ ] `GET /reports/{report_id}` - Get detailed report
- [ ] `GET /reports/nearby/{lat}/{lon}` - Find reports in radius

#### 4.3.4 Validation Endpoints
- [ ] `POST /validate/batch` - Batch validate pending reports

#### 4.3.5 Analytics Endpoints
- [ ] `GET /analytics/stats` - System statistics
- [ ] `GET /analytics/leaderboard` - Top contributors

#### 4.3.6 Start API Server
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📝 TASK 4.4: API Testing
**Owner:** Full-Stack Dev | **Duration:** 0.5 days | **Priority:** HIGH

### Microtasks

#### 4.4.1 Create Test Script
```bash
# File: scripts/test_api.sh

# Health check
curl -X GET "http://localhost:8000/"

# Create user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_citizen", "email": "citizen@example.com"}'

# Submit flood report
curl -X POST "http://localhost:8000/reports" \
  -d '{"user_id": 1, "latitude": 20.4625, "longitude": 85.8830, "depth_meters": 1.5, "timestamp": "2019-05-03T14:30:00"}'
```

#### 4.4.2 Automated Tests
```python
# File: tests/test_api.py
from fastapi.testclient import TestClient

def test_create_user():
    response = client.post("/users", json={...})
    assert response.status_code == 201
```

---

## 📝 TASK 4.5: React Web Dashboard
**Owner:** Full-Stack Dev | **Duration:** 3 days | **Priority:** HIGH

### Microtasks

#### 4.5.1 Initialize React Project
```bash
cd src/frontend
npx create-react-app web-dashboard
cd web-dashboard

# Install dependencies
npm install mapbox-gl @mapbox/mapbox-gl-draw
npm install axios react-query
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install recharts date-fns
npm install leaflet react-leaflet
```

#### 4.5.2 Environment Configuration
```env
# .env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
```

#### 4.5.3 Create FloodMap Component
```jsx
// File: src/components/FloodMap.jsx

// Features:
// - Mapbox GL with satellite imagery
// - 3D terrain visualization
// - Color-coded validation status (green/yellow/red)
// - Cluster visualization for dense reports
// - Popup with report details
// - Legend component
```

#### 4.5.4 Create StatsDashboard Component
```jsx
// File: src/components/StatsDashboard.jsx

// Features:
// - Summary cards: Total, Validated, Flagged, Avg Score
// - LineChart: Reports over time
// - PieChart: Validation status distribution
// - BarChart: Top contributors (leaderboard)
```

#### 4.5.5 Create Main App Structure
```jsx
// File: src/App.js

// Tab structure:
// - Dashboard (stats)
// - Map View (interactive map)
// - Validation Queue (pending reports)
```

#### 4.5.6 Run Dashboard
```bash
cd src/frontend/web-dashboard
npm start
# Opens http://localhost:3000
```

---

## 📝 TASK 4.6: Mobile PWA Development
**Owner:** Full-Stack Dev | **Duration:** 3 days | **Priority:** HIGH

### Microtasks

#### 4.6.1 Service Worker Setup
```javascript
// File: public/service-worker.js

const CACHE_NAME = 'flood-validator-v1.0';

// Install: Cache static assets
self.addEventListener('install', ...);

// Fetch: Network first for API, cache first for static
self.addEventListener('fetch', ...);

// Sync: Background sync for queued reports
self.addEventListener('sync', ...);
```

#### 4.6.2 PWA Manifest
```json
// File: public/manifest.json
{
  "short_name": "Flood Validator",
  "name": "Odisha Flood Validation System",
  "display": "standalone",
  "theme_color": "#1976d2",
  "orientation": "portrait"
}
```

#### 4.6.3 Offline Report Form
```jsx
// File: src/components/OfflineReportForm.jsx

// Features:
// - GPS location auto-detect
// - Depth input with validation
// - Photo capture with camera
// - Online/offline indicator
// - Queue counter when offline
// - Auto-sync when online
```

#### 4.6.4 IndexedDB Queue
```javascript
// Store reports locally when offline
const db = indexedDB.open('FloodReportsDB', 1);

// Queue structure:
// { id, data, timestamp, synced: false }
```

#### 4.6.5 Background Sync
```javascript
// Register sync when report submitted offline
const registration = await navigator.serviceWorker.ready;
await registration.sync.register('sync-reports');
```

---

## 📝 TASK 4.7: Offline Sync Architecture
**Owner:** Full-Stack Dev | **Duration:** 1 day | **Priority:** MEDIUM

### Microtasks

#### 4.7.1 Create Sync Manager
```python
# File: src/api/sync_manager.py

class OfflineSyncManager:
    def add_to_queue(self, report_data) -> int
    def get_pending_reports(self) -> List[Dict]
    def mark_synced(self, queue_id, server_report_id)
    def sync_with_server(self, api_url, auth_token)
```

#### 4.7.2 API Sync Endpoint
```python
@app.post("/sync/batch")
async def sync_offline_reports(reports: List[FloodReportCreate]):
    """Bulk sync offline reports when connectivity restored."""
```

---

## 📝 TASK 4.8: Time-Lapse Visualization
**Owner:** Full-Stack Dev | **Duration:** 1 day | **Priority:** MEDIUM

### Microtasks

#### 4.8.1 Create TimeLapseViewer Component
```jsx
// File: src/components/TimeLapseViewer.jsx

// Features:
// - Heatmap layer showing flood evolution
// - Play/pause/seek controls
// - Time step slider
// - 1 second per hour playback speed
```

---

## ✅ Phase Completion Checklist

### Backend
- [ ] API running on port 8000
- [ ] All endpoints tested and working
- [ ] Database operations verified
- [ ] Validation integrated with API

### Web Dashboard
- [ ] Map displays with reports color-coded
- [ ] Stats dashboard with real-time updates
- [ ] Responsive design for all screens

### Mobile PWA
- [ ] Installable on mobile devices
- [ ] Works offline (report submission)
- [ ] Auto-syncs when online
- [ ] GPS location capture working
- [ ] Photo capture working

---

## 🔗 Dependencies for Next Phase
- ✅ API ready for experiment data loading
- ✅ Dashboard ready for result visualization
- ⏳ Experiments will use API for batch validation

---

## 📊 Performance Targets

| Component | Metric | Target |
|-----------|--------|--------|
| API | Response time | < 200ms |
| API | Concurrent requests | 100 |
| Dashboard | Initial load | < 3 seconds |
| Dashboard | Map render | < 2 seconds |
| PWA | Offline queue | 500+ reports |
| PWA | Sync time | < 5 seconds per report |

---

## 🧪 Demo Scenarios

### Scenario 1: Online Report Submission
1. Open mobile PWA
2. Allow GPS access
3. Enter flood depth
4. Submit → See validation result in 2 seconds

### Scenario 2: Offline Queue
1. Turn on airplane mode
2. Submit 3 reports → Queue shows "3 pending"
3. Turn off airplane mode → Auto-sync
4. See "Synced!" confirmation

### Scenario 3: Dashboard Exploration
1. Open web dashboard
2. View system stats
3. Explore map with clustered reports
4. Click report → See validation details

---

*Phase 4 Last Updated: December 30, 2025*
