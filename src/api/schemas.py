from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime

# ==========================================
# User Schemas
# ==========================================

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    user_id: int
    trust_score: float
    total_reports: int
    verified_reports: int
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# Flood Report Schemas
# ==========================================

class FloodReportBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    depth_meters: float = Field(..., ge=0, le=20, description="Observed flood depth in meters")
    description: Optional[str] = None
    timestamp: datetime

    @field_validator('latitude')
    def validate_lat(cls, v):
        # Optional: Strict check for Odisha bounds if needed
        # if not (19.0 <= v <= 22.5): raise ValueError("Latitude outside Odisha")
        return v

class FloodReportCreate(FloodReportBase):
    user_id: int = Field(..., description="ID of the reporting user")
    location_accuracy_m: Optional[float] = 10.0
    photo_url: Optional[str] = None

class ValidationDetails(BaseModel):
    layer1_score: Optional[float] = None
    layer2_score: Optional[float] = None
    layer3_score: Optional[float] = None
    features: Optional[Dict[str, float]] = None

class FloodReportResponse(FloodReportBase):
    report_id: int
    user_id: int
    
    validation_status: str
    final_score: Optional[float] = None
    
    # Nested scores
    physical_score: Optional[float] = None
    statistical_score: Optional[float] = None
    reputation_score: Optional[float] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# Validation Response (Detailed)
# ==========================================

class ValidationResponse(BaseModel):
    report_id: int
    status: str
    final_score: float
    details: Optional[Dict[str, Any]] = None # Flexible dict for detailed layer breakdown
    timestamp: datetime = Field(default_factory=datetime.now)
