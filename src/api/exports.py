"""
Export Module for Flood Validation API.

Provides endpoints for exporting reports in various formats:
- CSV for spreadsheet/government agency use
- GeoJSON for GIS software (QGIS, ArcGIS)
"""

import csv
import io
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api import models

router = APIRouter(prefix="/reports/export", tags=["exports"])


@router.get("/csv")
def export_reports_csv(
    status: Optional[str] = Query(None, description="Filter by status: validated, flagged, rejected"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db)
):
    """
    Export flood reports as CSV file.
    
    Useful for:
    - Government agencies (OSDMA)
    - Data analysis in Excel
    - Backup purposes
    """
    # Build query
    query = db.query(models.FloodReport)
    
    if status:
        query = query.filter(models.FloodReport.validation_status == status)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(models.FloodReport.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(models.FloodReport.timestamp <= end_dt)
        except ValueError:
            pass
    
    reports = query.order_by(models.FloodReport.timestamp.desc()).limit(limit).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "report_id", "user_id", "latitude", "longitude", "depth_meters",
        "timestamp", "description", "validation_status", "final_score",
        "physical_score", "statistical_score", "reputation_score",
        "created_at", "validated_at"
    ])
    
    # Data rows
    for r in reports:
        writer.writerow([
            r.report_id, r.user_id, r.latitude, r.longitude, r.depth_meters,
            r.timestamp.isoformat() if r.timestamp else "",
            r.description or "",
            r.validation_status, r.final_score,
            r.physical_score, r.statistical_score, r.reputation_score,
            r.created_at.isoformat() if r.created_at else "",
            r.validated_at.isoformat() if r.validated_at else ""
        ])
    
    output.seek(0)
    
    filename = f"flood_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/geojson")
def export_reports_geojson(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db)
):
    """
    Export flood reports as GeoJSON FeatureCollection.
    
    Useful for:
    - GIS software (QGIS, ArcGIS)
    - Web mapping libraries (Leaflet, Mapbox)
    - Spatial analysis tools
    """
    # Build query
    query = db.query(models.FloodReport)
    
    if status:
        query = query.filter(models.FloodReport.validation_status == status)
    
    reports = query.order_by(models.FloodReport.timestamp.desc()).limit(limit).all()
    
    # Build GeoJSON FeatureCollection
    features = []
    
    for r in reports:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r.longitude, r.latitude]  # GeoJSON is [lon, lat]
            },
            "properties": {
                "report_id": r.report_id,
                "user_id": r.user_id,
                "depth_meters": r.depth_meters,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "description": r.description,
                "validation_status": r.validation_status,
                "final_score": r.final_score,
                "physical_score": r.physical_score,
                "statistical_score": r.statistical_score,
                "reputation_score": r.reputation_score
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_features": len(features),
            "exported_at": datetime.now().isoformat(),
            "crs": "EPSG:4326"
        }
    }
    
    filename = f"flood_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
    
    return StreamingResponse(
        iter([json.dumps(geojson, indent=2)]),
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/summary")
def export_summary_stats(
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for reports.
    """
    total = db.query(models.FloodReport).count()
    validated = db.query(models.FloodReport).filter(models.FloodReport.validation_status == 'validated').count()
    flagged = db.query(models.FloodReport).filter(models.FloodReport.validation_status == 'flagged').count()
    rejected = db.query(models.FloodReport).filter(models.FloodReport.validation_status == 'rejected').count()
    pending = db.query(models.FloodReport).filter(models.FloodReport.validation_status == 'pending').count()
    
    return {
        "total_reports": total,
        "validated": validated,
        "flagged": flagged,
        "rejected": rejected,
        "pending": pending,
        "validation_rate": round(validated / total * 100, 2) if total > 0 else 0,
        "exported_at": datetime.now().isoformat()
    }
