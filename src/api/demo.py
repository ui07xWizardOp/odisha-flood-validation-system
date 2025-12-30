"""
Lightweight API Demo for Testing.

This is a simplified version that works without heavy dependencies.
Run with: py -3 -m uvicorn src.api.demo:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random

app = FastAPI(
    title="Odisha Flood Validation API (Demo)",
    description="Lightweight demo version for testing",
    version="1.0.0-demo"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Schemas =============

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str]
    trust_score: float = 0.5
    total_reports: int = 0

class FloodReportCreate(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    depth_meters: float
    timestamp: Optional[datetime] = None
    description: Optional[str] = None

class ValidationResult(BaseModel):
    report_id: int
    final_score: float
    status: str
    layer_scores: dict

# ============= In-Memory Storage =============

users_db = {}
reports_db = {}
user_counter = 1
report_counter = 1

# ============= Mock Validator =============

def mock_validate_report(lat: float, lon: float, depth: float, user_trust: float) -> dict:
    """
    Simulates the 3-layer validation algorithm.
    In production, this would use actual DEM/HAND rasters.
    """
    # Layer 1: Physical (mock based on location)
    # Cuttack area (flood-prone): higher score
    in_flood_zone = (20.0 < lat < 21.0) and (85.5 < lon < 86.5)
    l1_score = random.uniform(0.7, 0.95) if in_flood_zone else random.uniform(0.2, 0.5)
    
    # Layer 2: Statistical (mock)
    l2_score = random.uniform(0.6, 0.9)
    
    # Layer 3: Reputation
    l3_score = user_trust
    
    # Aggregate (40% L1 + 40% L2 + 20% L3)
    final_score = 0.4 * l1_score + 0.4 * l2_score + 0.2 * l3_score
    status = "validated" if final_score >= 0.7 else "flagged"
    
    return {
        "final_score": round(final_score, 3),
        "status": status,
        "layer_scores": {
            "L1_physical": round(l1_score, 3),
            "L2_statistical": round(l2_score, 3),
            "L3_reputation": round(l3_score, 3)
        }
    }

# ============= Endpoints =============

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "flood-validation-api-demo",
        "message": "Welcome to the Odisha Flood Validation API! Try /docs for Swagger UI."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "users_count": len(users_db), "reports_count": len(reports_db)}

@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    global user_counter
    
    # Check duplicate
    for u in users_db.values():
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already registered")
    
    user_id = user_counter
    user_counter += 1
    
    users_db[user_id] = {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "trust_score": 0.5,
        "total_reports": 0,
        "verified_reports": 0
    }
    
    return users_db[user_id]

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/reports", status_code=201)
def submit_flood_report(report: FloodReportCreate):
    global report_counter
    
    # Check user exists
    if report.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[report.user_id]
    
    # Validate the report
    validation = mock_validate_report(
        report.latitude,
        report.longitude,
        report.depth_meters,
        user["trust_score"]
    )
    
    report_id = report_counter
    report_counter += 1
    
    # Store report
    reports_db[report_id] = {
        "report_id": report_id,
        "user_id": report.user_id,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "depth_meters": report.depth_meters,
        "timestamp": (report.timestamp or datetime.now()).isoformat(),
        "description": report.description,
        "validation_status": validation["status"],
        "final_score": validation["final_score"],
        **validation["layer_scores"]
    }
    
    # Update user stats
    user["total_reports"] += 1
    if validation["status"] == "validated":
        user["verified_reports"] += 1
        user["trust_score"] = min(1.0, user["trust_score"] + 0.05)
    
    return {
        "report_id": report_id,
        "validation": validation,
        "message": f"Report {validation['status']} with score {validation['final_score']}"
    }

@app.get("/reports")
def get_reports(skip: int = 0, limit: int = 50, status: Optional[str] = None):
    reports = list(reports_db.values())
    
    if status:
        reports = [r for r in reports if r["validation_status"] == status]
    
    return reports[skip:skip+limit]

@app.get("/reports/{report_id}")
def get_report(report_id: int):
    if report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    return reports_db[report_id]

@app.get("/stats")
def get_stats():
    """Get system statistics."""
    total = len(reports_db)
    validated = sum(1 for r in reports_db.values() if r["validation_status"] == "validated")
    flagged = total - validated
    avg_score = sum(r["final_score"] for r in reports_db.values()) / max(total, 1)
    
    return {
        "total_reports": total,
        "validated_reports": validated,
        "flagged_reports": flagged,
        "average_score": round(avg_score, 3),
        "total_users": len(users_db)
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Flood Validation API Demo...")
    print("Open http://localhost:8000/docs for Swagger UI")
    uvicorn.run(app, host="0.0.0.0", port=8000)
