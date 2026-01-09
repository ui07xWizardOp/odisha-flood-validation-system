# API Documentation

## Odisha Flood Validation System API

**Base URL:** `http://localhost:8000`  
**Version:** 2.0.0

---

## Authentication

Currently no authentication required for development. Production should use JWT tokens.

---

## Endpoints

### Validation Fallbacks & Edge Cases

The system is designed to degrade gracefully:

1.  **Missing GPS Data**: If an uploaded image lacks EXIF GPS tags, the system enters **Preview Mode**. The report will be processed for CV analysis but **will not be saved to the database**. The location fields in the response will be `null`.
2.  **Missing CV Model**: If the custom CNN model weights are unavailable, the system automatically falls back to **OpenCV-based water detection** (heuristic analysis) to ensure service continuity.

---

### Health & Stats

#### Health Check
```
GET /
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "flood-validation-api"
}
```

#### System Statistics
```
GET /stats
```

**Response:**
```json
{
  "total_reports": 42,
  "validated_reports": 35,
  "active_users": 15,
  "system_status": "Operational",
  "last_updated": "2026-01-02T10:00:00Z"
}
```

---

### Users

#### Create User
```
POST /users
```

**Request Body:**
```json
{
  "username": "citizen_reporter",
  "email": "user@example.com"
}
```

**Response (201):**
```json
{
  "user_id": 1,
  "username": "citizen_reporter",
  "email": "user@example.com",
  "trust_score": 0.5,
  "total_reports": 0,
  "verified_reports": 0,
  "created_at": "2026-01-02T10:00:00Z"
}
```

#### Get User
```
GET /users/{user_id}
```

---

### Flood Reports

#### Submit Report
```
POST /reports
```

**Request Body:**
```json
{
  "user_id": 1,
  "latitude": 20.4625,
  "longitude": 85.8830,
  "depth_meters": 1.5,
  "timestamp": "2026-01-02T10:00:00Z",
  "description": "Water level rising near main road"
}
```

**Response (201):**
```json
{
  "report_id": 42,
  "user_id": 1,
  "latitude": 20.4625,
  "longitude": 85.8830,
  "depth_meters": 1.5,
  "validation_status": "validated",
  "final_score": 0.85,
  "physical_score": 0.9,
  "statistical_score": 0.8,
  "reputation_score": 0.75,
  "created_at": "2026-01-02T10:00:00Z"
}
```

#### Get Reports
```
GET /reports?skip=0&limit=50
```

#### Get Nearby Reports
```
GET /reports/nearby?lat=20.46&lon=85.88&radius_m=1000
```

---

### Photo Validation (NEW)

#### Validate Flood Photo
```
POST /validate-photo
Content-Type: multipart/form-data
```

**Request:** Upload image file

**Response:**
```json
{
  "valid": true,
  "is_flood_detected": true,
  "confidence": 0.87,
  "water_coverage": 0.45,
  "model_used": "MobileNetV2",
  "validation_score": 0.82
}
```

#### Submit Report from Geotagged Image
```
POST /reports/from-image
Content-Type: multipart/form-data
```

**Form Fields:**
- `file`: Geotagged JPEG image
- `user_id`: Reporter ID (default: 1)
- `depth_meters`: Observed depth (default: 1.0)
- `description`: Optional description

**Response:**
```json
{
  "report_id": 43,
  "extracted_location": {
    "latitude": 20.4625,
    "longitude": 85.8830,
    "altitude": 15.2,
    "in_odisha_bounds": true,
    "device": "iPhone 15 Pro"
  },
  "cv_result": {
    "is_flood": true,
    "confidence": 0.87,
    "water_coverage": 0.45
  },
  "validation_status": "validated",
  "final_score": 0.85,
  "message": "Report created from geotagged image at (20.4625, 85.8830)"
}
```

**Response (Missing GPS - Preview Mode):**
```json
{
  "report_id": 0,
  "extracted_location": {
    "latitude": null,
    "longitude": null,
    "altitude": null,
    "in_odisha_bounds": false,
    "device": null
  },
  "cv_result": {
    "is_flood": true,
    "confidence": 0.82,
    "water_coverage": 0.35
  },
  "validation_status": "pending",
  "final_score": 0.0,
  "message": "Report processed. Location: Missing"
}
```

---

## Validation Scoring (5-Layer ML System)

Reports are validated using a **5-layer ML-enhanced algorithm**:

| Layer | Component | Description |
|-------|-----------|-------------|
| L1 | Physical | Rule-based scoring on DEM, HAND, Slope features |
| L2 | Statistical | DBSCAN clustering + Hybrid consensus |
| L3 | Reputation | Trust increment/decrement (+0.1/-0.15) |
| L4 | Social | NewsData.io flood event correlation |
| L5 | Visual | Hybrid Ensemble (MobileNetV2 + OpenCV) |

**Weight Aggregation:** Neural network learns optimal weights instead of fixed values.

**Threshold:** Final Score ≥ 0.7 → `validated`, else `flagged`

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request (validation error, invalid image) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Example Usage

```bash
# Health check
curl http://localhost:8000/

# Get system stats
curl http://localhost:8000/stats

# Create user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "email": "test@example.com"}'

# Submit flood report
curl -X POST "http://localhost:8000/reports" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "latitude": 20.4625,
    "longitude": 85.8830,
    "depth_meters": 1.5,
    "timestamp": "2026-01-02T10:00:00Z"
  }'

# Validate a photo
curl -X POST "http://localhost:8000/validate-photo" \
  -F "file=@flood_photo.jpg"

# Submit report from geotagged image
curl -X POST "http://localhost:8000/reports/from-image" \
  -F "file=@geotagged_flood.jpg" \
  -F "user_id=1" \
  -F "depth_meters=1.5"

# Get nearby reports
curl "http://localhost:8000/reports/nearby?lat=20.46&lon=85.88&radius_m=1000"
```
