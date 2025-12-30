# API Documentation

## Odisha Flood Validation System API

**Base URL:** `http://localhost:8000`  
**Version:** 1.0.0

---

## Authentication

Currently no authentication required for development. Production should use JWT tokens.

---

## Endpoints

### Health Check

```
GET /
```

**Response:**
```json
{
  "status": "ok",
  "service": "flood-validation-api"
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
  "created_at": "2025-12-30T10:00:00Z"
}
```

#### Get User

```
GET /users/{user_id}
```

**Response (200):**
```json
{
  "user_id": 1,
  "username": "citizen_reporter",
  "trust_score": 0.75,
  "total_reports": 10,
  "verified_reports": 8
}
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
  "timestamp": "2025-12-30T10:00:00Z",
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
  "created_at": "2025-12-30T10:00:00Z"
}
```

#### Get Reports

```
GET /reports?skip=0&limit=50
```

**Response (200):**
```json
[
  {
    "report_id": 42,
    "user_id": 1,
    "latitude": 20.4625,
    "longitude": 85.8830,
    "validation_status": "validated",
    "final_score": 0.85
  }
]
```

#### Get Nearby Reports

```
GET /reports/nearby?lat=20.46&lon=85.88&radius_m=1000
```

**Response (200):**
```json
[
  {
    "report_id": 42,
    "distance_m": 150.5,
    "validation_status": "validated"
  }
]
```

---

## Validation Scoring

Reports are validated using a 3-layer algorithm:

| Layer | Weight | Description |
|-------|--------|-------------|
| Physical (L1) | 40% | DEM, HAND, Slope checks |
| Statistical (L2) | 40% | Spatial clustering, temporal consistency |
| Reputation (L3) | 20% | User trust score |

**Final Score** = 0.4×L1 + 0.4×L2 + 0.2×L3

**Threshold:** Score ≥ 0.7 → `validated`, else `flagged`

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request (validation error) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Rate Limits

- Development: No limits
- Production: 100 requests/minute per IP

---

## Example Usage

```bash
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
    "timestamp": "2025-12-30T10:00:00Z"
  }'

# Get nearby reports
curl "http://localhost:8000/reports/nearby?lat=20.46&lon=85.88&radius_m=1000"
```
