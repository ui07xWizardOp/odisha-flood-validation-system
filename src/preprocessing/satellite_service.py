"""
Satellite Integration Service for ISRO Bhuvan.

Provides access to:
- SAR (Synthetic Aperture Radar) flood extent imagery
- Comparison of user reports against satellite observations
- Ground truth validation from remote sensing
"""

import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SatelliteService:
    """
    Integration with ISRO Bhuvan and other satellite data sources.
    
    Provides WMS/WMTS layers for flood extent visualization
    and validation against satellite observations.
    """
    
    # ISRO Bhuvan WMS endpoints
    BHUVAN_WMS = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"
    BHUVAN_FLOOD_LAYER = "flood_extent_sar"
    
    # Open-source alternatives
    COPERNICUS_EMS = "https://emergency.copernicus.eu/mapping/list-of-emergencies-702"
    SENTINEL_HUB = "https://services.sentinel-hub.com/ogc/wms"
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
    
    def get_flood_extent_layer(self, bbox: Tuple[float, float, float, float]) -> Dict:
        """
        Get flood extent layer metadata for a bounding box.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            Dict with layer URLs and metadata
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # WMS GetMap URL
        wms_url = self._build_wms_url(bbox, width=512, height=512)
        
        return {
            "wms_url": wms_url,
            "layer_name": self.BHUVAN_FLOOD_LAYER,
            "bbox": bbox,
            "crs": "EPSG:4326",
            "format": "image/png",
            "available": True,
            "source": "ISRO Bhuvan"
        }
    
    def _build_wms_url(self, bbox: Tuple, width: int = 512, height: int = 512) -> str:
        """Build WMS GetMap URL."""
        params = {
            "service": "WMS",
            "version": "1.1.1",
            "request": "GetMap",
            "layers": self.BHUVAN_FLOOD_LAYER,
            "bbox": ",".join(map(str, bbox)),
            "width": width,
            "height": height,
            "srs": "EPSG:4326",
            "format": "image/png",
            "transparent": "true"
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.BHUVAN_WMS}?{query}"
    
    def check_satellite_coverage(self, lat: float, lon: float, 
                                  date: Optional[datetime] = None) -> Dict:
        """
        Check if satellite data is available for a location and date.
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Date to check (default: today)
            
        Returns:
            Dict with coverage status and available imagery
        """
        if date is None:
            date = datetime.now()
        
        # Check Odisha bounds
        if not self._is_in_odisha(lat, lon):
            return {
                "covered": False,
                "reason": "Location outside Odisha state boundary",
                "lat": lat,
                "lon": lon
            }
        
        # Simulate satellite pass check
        # In production, this would query actual satellite schedules
        return {
            "covered": True,
            "satellites": ["Sentinel-1", "RISAT-2B"],
            "last_acquisition": (date - timedelta(days=2)).isoformat(),
            "next_acquisition": (date + timedelta(days=1)).isoformat(),
            "flood_detected": self._mock_flood_detection(lat, lon),
            "confidence": 0.75
        }
    
    def _is_in_odisha(self, lat: float, lon: float) -> bool:
        """Check if point is within Odisha bounding box."""
        # Odisha approximate bounds
        return (17.78 <= lat <= 22.57) and (81.37 <= lon <= 87.53)
    
    def _mock_flood_detection(self, lat: float, lon: float) -> bool:
        """
        Mock flood detection based on location.
        In production, this would analyze SAR imagery.
        """
        # Areas with high flood probability
        flood_prone_zones = [
            (20.3, 86.5),  # Kendrapara
            (20.0, 86.4),  # Jagatsinghpur
            (20.5, 85.8),  # Cuttack
            (20.9, 86.2),  # Bhadrak
        ]
        
        for zone_lat, zone_lon in flood_prone_zones:
            distance = ((lat - zone_lat) ** 2 + (lon - zone_lon) ** 2) ** 0.5
            if distance < 0.3:  # Within ~30km
                return True
        
        return False
    
    def validate_against_satellite(self, lat: float, lon: float, 
                                   user_claimed_flood: bool) -> Dict:
        """
        Compare user report against satellite observations.
        
        Args:
            lat: Latitude of report
            lon: Longitude of report
            user_claimed_flood: Whether user reported flooding
            
        Returns:
            Dict with validation result and confidence
        """
        coverage = self.check_satellite_coverage(lat, lon)
        
        if not coverage.get("covered"):
            return {
                "validated": None,
                "confidence": 0.0,
                "reason": "No satellite coverage",
                "satellite_detected": None
            }
        
        satellite_flood = coverage.get("flood_detected", False)
        
        # Agreement analysis
        if user_claimed_flood and satellite_flood:
            return {
                "validated": True,
                "confidence": 0.9,
                "reason": "User report confirmed by satellite imagery",
                "satellite_detected": True,
                "agreement": "match"
            }
        elif not user_claimed_flood and not satellite_flood:
            return {
                "validated": True,
                "confidence": 0.85,
                "reason": "No flood - consistent with satellite data",
                "satellite_detected": False,
                "agreement": "match"
            }
        elif user_claimed_flood and not satellite_flood:
            return {
                "validated": False,
                "confidence": 0.6,
                "reason": "Flood not detected in recent satellite imagery (may be timing difference)",
                "satellite_detected": False,
                "agreement": "user_only"
            }
        else:  # Satellite shows flood but user didn't report
            return {
                "validated": None,
                "confidence": 0.5,
                "reason": "Satellite shows potential flooding",
                "satellite_detected": True,
                "agreement": "satellite_only"
            }
    
    def get_recent_flood_events(self, state: str = "Odisha", 
                                 days: int = 30) -> Dict:
        """
        Get recent flood events from satellite monitoring.
        
        Returns:
            Dict with list of detected flood events
        """
        # In production, this would query Copernicus EMS or Bhuvan
        return {
            "state": state,
            "period_days": days,
            "events": [
                {
                    "event_id": "FL-OD-2024-001",
                    "date": "2024-07-15",
                    "affected_districts": ["Kendrapara", "Jagatsinghpur"],
                    "severity": "moderate",
                    "source": "Sentinel-1 SAR"
                },
                {
                    "event_id": "FL-OD-2024-002",
                    "date": "2024-08-20",
                    "affected_districts": ["Cuttack", "Puri"],
                    "severity": "high",
                    "source": "RISAT-2B SAR"
                }
            ],
            "source": "simulated"
        }


# Singleton instance
satellite_service = SatelliteService()


if __name__ == "__main__":
    print("🛰️ Satellite Integration Service")
    
    # Test coverage check
    result = satellite_service.check_satellite_coverage(20.5, 85.8)
    print(f"   Coverage check: {result}")
    
    # Test validation
    validation = satellite_service.validate_against_satellite(20.3, 86.5, True)
    print(f"   Validation: {validation}")
