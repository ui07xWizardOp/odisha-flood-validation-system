from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from src.api import models, schemas
from src.api.database import get_db, engine, DATABASE_URL
from src.validation.validator import FloodReportValidator

# Check if we are using PostGIS
_use_postgis = "sqlite" not in DATABASE_URL.lower()

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

# Startup Event: Seed Default User
@app.on_event("startup")
def seed_default_user():
    db = next(get_db())
    try:
        default_user = db.query(models.User).filter(models.User.user_id == 1).first()
        if not default_user:
            print("[INFO] Seeding default guest user (ID: 1)...")
            guest = models.User(
                username="guest_user",
                email="guest@floodvalidation.local",
                trust_score=0.5
            )
            db.add(guest)
            db.commit()
    except Exception as e:
        print(f"[WARN] User seeding failed (normal if DB not init): {e}")

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

@app.get("/health")
def health_check_alias():
    return {"status": "ok", "service": "flood-validation-api"}

@app.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """
    Return basic system statistics for the dashboard.
    """
    total_users = db.query(models.User).count()
    total_reports = db.query(models.FloodReport).count()
    validated_reports = db.query(models.FloodReport).filter(models.FloodReport.validation_status == 'validated').count()
    
    return {
        "total_reports": total_reports,
        "validated_reports": validated_reports,
        "active_users": total_users,
        "system_status": "Operational",
        "last_updated": datetime.now()
    }

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

    # 3. Run Validation Logic (ML-Enhanced 5-Layer)
    validation_result = validator_service.validate_report(
        report_id=0,  # Placeholder
        user_id=report.user_id,
        lat=report.latitude,
        lon=report.longitude,
        depth=report.depth_meters,
        timestamp=report.timestamp,
        recent_reports=recent_df,
        rainfall_24h=None  # Will be fetched by validator
    )
    
    # 4. Save to Database
    from sqlalchemy import func
    
    # Build location value based on database type
    if _use_postgis:
        location_value = func.ST_SetSRID(func.ST_MakePoint(report.longitude, report.latitude), 4326)
    else:
        # For SQLite, store as WKT string
        location_value = f"POINT({report.longitude} {report.latitude})"
    
    # Extract scores from new 5-layer structure
    details = validation_result.get('details', {})
    physical_score = details.get('physical', {}).get('layer1_score', 0.5)
    statistical_score = details.get('statistical', {}).get('layer2_score', 0.5)
    reputation_score = details.get('reputation', {}).get('layer3_score', 0.5)
    
    db_report = models.FloodReport(
        user_id=report.user_id,
        location=location_value,
        latitude=report.latitude,
        longitude=report.longitude,
        depth_meters=report.depth_meters,
        timestamp=report.timestamp,
        description=report.description,
        
        # Validation Results
        validation_status=validation_result['status'],
        final_score=validation_result['final_score'],
        
        physical_score=physical_score,
        statistical_score=statistical_score,
        reputation_score=reputation_score,
        
        validated_at=datetime.now()
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # 5. Return with full validation details
    return db_report

@app.get("/reports", response_model=List[schemas.FloodReportResponse])
def get_reports(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    reports = db.query(models.FloodReport).order_by(models.FloodReport.timestamp.desc()).offset(skip).limit(limit).all()
    return reports

@app.get("/reports/nearby", response_model=List[schemas.FloodReportResponse])
def get_nearby_reports(lat: float, lon: float, radius_m: int = 1000, db: Session = Depends(get_db)):
    """
    Get reports within X meters of a point.
    Uses PostGIS if available, otherwise falls back to simple bounding box.
    """
    from sqlalchemy import func
    
    if _use_postgis:
        # PostGIS spatial query
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        reports = db.query(models.FloodReport).filter(
            func.ST_DWithin(models.FloodReport.location, point, radius_m)
        ).all()
    else:
        # SQLite fallback: simple bounding box approximation
        # 1 degree latitude ~ 111km, 1 degree longitude varies
        lat_delta = radius_m / 111000.0  # Rough approximation
        lon_delta = radius_m / (111000.0 * abs(max(0.01, abs(lat))))  # Adjust for latitude
        
        reports = db.query(models.FloodReport).filter(
            models.FloodReport.latitude.between(lat - lat_delta, lat + lat_delta),
            models.FloodReport.longitude.between(lon - lon_delta, lon + lon_delta)
        ).all()
    
    return reports

# ==========================================
# Photo Validation Endpoint (Computer Vision)
# ==========================================

from fastapi import File, UploadFile
from src.ml.models.image_classifier import flood_classifier

class PhotoValidationResponse(schemas.BaseModel):
    valid: bool
    is_flood_detected: bool
    confidence: float
    water_coverage: float
    model_used: str
    validation_score: float

@app.post("/validate-photo", response_model=PhotoValidationResponse)
async def validate_flood_photo(file: UploadFile = File(...)):
    """
    Validate a user-submitted flood photo using Computer Vision.
    
    Returns:
        - is_flood_detected: Whether the image shows flooding
        - confidence: Model confidence (0-1)
        - water_coverage: Estimated water ratio in image
        - validation_score: Overall score for validation boost
    """
    # Read image bytes
    contents = await file.read()
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG)"
        )
    
    # Run CV validation
    result = flood_classifier.validate_image(contents)
    
    return PhotoValidationResponse(
        valid=result.get("valid", False),
        is_flood_detected=result.get("is_flood_detected", False),
        confidence=result.get("confidence", 0.0),
        water_coverage=result.get("water_coverage", 0.0),
        model_used=result.get("model_used", "Unknown"),
        validation_score=result.get("score", 0.0)
    )


# ==========================================
# One-Shot Image Report Endpoint
# ==========================================

from src.preprocessing.exif_service import exif_service

class ImageReportResponse(schemas.BaseModel):
    report_id: int
    extracted_location: dict
    cv_result: dict
    validation_status: str
    final_score: float
    message: str

@app.post("/reports/from-image", response_model=ImageReportResponse)
async def submit_report_from_image(
    file: UploadFile = File(...),
    user_id: int = 1,
    depth_meters: float = 1.0,
    description: str = "",
    db: Session = Depends(get_db)
):
    """
    One-shot flood report submission from a geotagged image.
    
    Extracts GPS coordinates from EXIF, validates with CV, and creates report.
    
    Args:
        file: Geotagged image (JPEG with GPS EXIF)
        user_id: Reporter ID
        depth_meters: Observed flood depth (optional, default 1.0m)
        description: Optional description
    
    Returns:
        Complete report with extracted location and validation results
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG)")
    
    # Verify user exists
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Read image bytes
    contents = await file.read()
    
    # Extract GPS from EXIF
    geotag = exif_service.extract_geotag(contents)
    
    if not geotag["success"]:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract GPS from image: {geotag['error']}"
        )
    
    lat = geotag["latitude"]
    lon = geotag["longitude"]
    timestamp = geotag["timestamp"] or datetime.now().isoformat()
    
    # Run CV validation
    cv_result = flood_classifier.validate_image(contents)
    
    # Run full validation pipeline
    import pandas as pd
    recent_reports = db.query(models.FloodReport).order_by(
        models.FloodReport.timestamp.desc()
    ).limit(100).all()
    
    recent_df = pd.DataFrame([{
        'lat': r.latitude, 'lon': r.longitude,
        'depth': r.depth_meters, 'timestamp': r.timestamp
    } for r in recent_reports]) if recent_reports else pd.DataFrame()
    
    validation_result = validator_service.validate_report(
        report_id=0,
        user_id=user_id,
        lat=lat,
        lon=lon,
        depth=depth_meters,
        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp, str) else timestamp,
        recent_reports=recent_df,
        rainfall_24h=None,
        image_bytes=contents  # Pass image for L5 validation
    )
    
    # Save to database
    from sqlalchemy import func
    
    if _use_postgis:
        location_value = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    else:
        location_value = f"POINT({lon} {lat})"
    
    details = validation_result.get('details', {})
    
    db_report = models.FloodReport(
        user_id=user_id,
        location=location_value,
        latitude=lat,
        longitude=lon,
        depth_meters=depth_meters,
        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if isinstance(timestamp, str) else datetime.now(),
        description=description or f"Photo report from {geotag.get('device_model', 'Unknown')}",
        validation_status=validation_result['status'],
        final_score=validation_result['final_score'],
        physical_score=details.get('physical', {}).get('layer1_score', 0.5),
        statistical_score=details.get('statistical', {}).get('layer2_score', 0.5),
        reputation_score=details.get('reputation', {}).get('layer3_score', 0.5),
        validated_at=datetime.now()
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return ImageReportResponse(
        report_id=db_report.report_id,
        extracted_location={
            "latitude": lat,
            "longitude": lon,
            "altitude": geotag.get("altitude"),
            "in_odisha_bounds": geotag.get("in_odisha_bounds", False),
            "device": geotag.get("device_model")
        },
        cv_result={
            "is_flood": cv_result.get("is_flood_detected", False),
            "confidence": cv_result.get("confidence", 0.0),
            "water_coverage": cv_result.get("water_coverage", 0.0)
        },
        validation_status=validation_result['status'],
        final_score=validation_result['final_score'],
        message=f"Report created from geotagged image at ({lat:.4f}, {lon:.4f})"
    )
