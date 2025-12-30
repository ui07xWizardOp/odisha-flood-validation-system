from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from src.api import models, schemas
from src.api.database import get_db, engine
from src.validation.validator import FloodReportValidator

# Initialize Validator Orchestrator
# (This loads large rasters, so done once at startup)
validator_service = FloodReportValidator()

# Create tables if not exist (handled by Alembic/SQL usually, but here for dev convenience)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Odisha Flood Validation System API",
    description="AI/ML-enhanced backend for validating crowdsourced flood reports.",
    version="1.0.0"
)

# CORS Security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "flood-validation-api"}

# ==========================================
# User Endpoints
# ==========================================

@app.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        trust_score=0.5 # Default trust
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ==========================================
# Report Endpoints
# ==========================================

@app.post("/reports", response_model=schemas.FloodReportResponse, status_code=201)
def submit_report(report: schemas.FloodReportCreate, db: Session = Depends(get_db)):
    """
    Submit and real-time validate a flood report.
    """
    # 1. Verify User
    user = db.query(models.User).filter(models.User.user_id == report.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Get Recent Reports (for Layer 2 Statistical Check)
    # Simple query: Get last 100 reports
    # TODO: Optimize with PostGIS ST_DWithin query for nearby only
    recent_reports_q = db.query(models.FloodReport).order_by(models.FloodReport.timestamp.desc()).limit(100).all()
    
    # Convert to DataFrame for Validator
    import pandas as pd
    if recent_reports_q:
        recent_df = pd.DataFrame([{
            'lat': r.latitude,
            'lon': r.longitude,
            'depth': r.depth_meters,
            'timestamp': r.timestamp
        } for r in recent_reports_q])
    else:
        recent_df = pd.DataFrame()

    # 3. Run Validation Logic
    validation_result = validator_service.validate_report(
        report_id=0, # Placeholder
        user_id=report.user_id,
        lat=report.latitude,
        lon=report.longitude,
        depth=report.depth_meters,
        timestamp=report.timestamp,
        recent_reports=recent_df,
        rainfall_24h=0.0 # TODO: Connect to live rainfall API
    )
    
    # 4. Save to Database
    # Use ST_SetSRID(ST_MakePoint(lon, lat), 4326) for PostGIS
    from sqlalchemy import func
    
    db_report = models.FloodReport(
        user_id=report.user_id,
        location=func.ST_SetSRID(func.ST_MakePoint(report.longitude, report.latitude), 4326),
        latitude=report.latitude,
        longitude=report.longitude,
        depth_meters=report.depth_meters,
        timestamp=report.timestamp,
        description=report.description,
        
        # Validation Results
        validation_status=validation_result['status'],
        final_score=validation_result['final_score'],
        
        physical_score=validation_result['details']['physical']['layer1_score'],
        statistical_score=validation_result['details']['statistical']['layer2_score'],
        reputation_score=validation_result['details']['reputation']['layer3_score'],
        
        validated_at=datetime.now()
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # 5. Save Metadata
    # (Simplified for brevity, full impl would unpack validation_result['details'])
    
    return db_report

@app.get("/reports", response_model=List[schemas.FloodReportResponse])
def get_reports(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    reports = db.query(models.FloodReport).order_by(models.FloodReport.timestamp.desc()).offset(skip).limit(limit).all()
    return reports

@app.get("/reports/nearby", response_model=List[schemas.FloodReportResponse])
def get_nearby_reports(lat: float, lon: float, radius_m: int = 1000, db: Session = Depends(get_db)):
    """
    Get reports within X meters of a point using PostGIS.
    """
    # ST_DWithin(geography_column, point, distance_meters)
    # Point is ST_SetSRID(ST_MakePoint(lon, lat), 4326)
    
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    
    reports = db.query(models.FloodReport).filter(
        func.ST_DWithin(models.FloodReport.location, point, radius_m)
    ).all()
    
    return reports
