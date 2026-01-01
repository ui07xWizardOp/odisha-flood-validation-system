from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import os

# Conditional import for geoalchemy2 (only available with PostGIS)
_db_url = os.getenv("DATABASE_URL", "")
_use_postgis = _db_url and "YOUR_SECURE_PASSWORD_HERE" not in _db_url and "sqlite" not in _db_url.lower()

if _use_postgis:
    from geoalchemy2 import Geography
else:
    Geography = None  # SQLite fallback

from src.api.database import Base

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255))
    phone_hash = Column(String(64))
    
    # Trust System
    trust_score = Column(Float, default=0.5)
    trust_alpha = Column(Float, default=1.0)
    trust_beta = Column(Float, default=1.0)
    
    # Stats
    total_reports = Column(Integer, default=0)
    verified_reports = Column(Integer, default=0)
    flagged_reports = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True))
    
    # Relationships
    reports = relationship("FloodReport", back_populates="user")

class FloodReport(Base):
    __tablename__ = 'flood_reports'
    
    report_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete="SET NULL"))
    
    # Geospatial
    # SRID 4326 is WGS84 (Lat/Lon)
    # Note: location column requires PostGIS. For SQLite, we store as WKT string.
    if _use_postgis:
        location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    else:
        location = Column(String(255), nullable=True)  # Store as WKT for SQLite
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_accuracy_m = Column(Float)
    
    # Report Data
    depth_meters = Column(Float)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    photo_url = Column(Text)
    source = Column(String(50), default='mobile_app')
    
    # Validation
    validation_status = Column(String(20), default='pending', index=True) 
    # 'pending', 'validated', 'flagged', 'rejected'
    
    final_score = Column(Float) # 0.0 to 1.0
    
    physical_score = Column(Float)
    statistical_score = Column(Float)
    reputation_score = Column(Float)
    
    # Metadata
    is_synthetic = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    validated_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="reports")
    metadata_rel = relationship("ValidationMetadata", back_populates="report", uselist=False)

class ValidationMetadata(Base):
    __tablename__ = 'validation_metadata'
    
    validation_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey('flood_reports.report_id', ondelete="CASCADE"))
    
    # Detailed inputs logged for full traceability
    elevation = Column(Float)
    elevation_neighborhood_mean = Column(Float)
    hand_value = Column(Float)
    slope_degrees = Column(Float)
    
    rainfall_24h_mm = Column(Float)
    neighbor_count = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    report = relationship("FloodReport", back_populates="metadata_rel")

class GroundTruth(Base):
    __tablename__ = 'ground_truth'
    
    truth_id = Column(Integer, primary_key=True)
    event_name = Column(String(100), nullable=False)
    event_date = Column(DateTime(timezone=True))
    # Note: flood_extent requires PostGIS. For SQLite, store as WKT string.
    if _use_postgis:
        flood_extent = Column(Geography(geometry_type='MULTIPOLYGON', srid=4326))
    else:
        flood_extent = Column(Text, nullable=True)  # Store as WKT for SQLite
    created_at = Column(DateTime(timezone=True), server_default=func.now())
