"""
EXIF GPS Extraction Service.

Extracts geolocation data from image EXIF metadata for one-shot
flood report submission.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path
import io

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed. EXIF extraction disabled.")


class ExifService:
    """Extract GPS coordinates and metadata from images."""
    
    # Odisha bounds for validation
    ODISHA_BOUNDS = {
        "lat_min": 17.5,
        "lat_max": 22.5,
        "lon_min": 81.5,
        "lon_max": 87.5
    }
    
    def extract_geotag(self, image_data: bytes) -> Dict:
        """
        Extract GPS coordinates and timestamp from image EXIF.
        
        Args:
            image_data: Raw image bytes (JPEG/PNG)
            
        Returns:
            Dict with lat, lon, timestamp, and metadata
        """
        if not PIL_AVAILABLE:
            return self._empty_result("Pillow not installed")
        
        try:
            image = Image.open(io.BytesIO(image_data))
            exif_data = self._get_exif_data(image)
            
            if not exif_data:
                return self._empty_result("No EXIF data found")
            
            # Extract GPS info
            gps_info = exif_data.get("GPSInfo")
            if not gps_info:
                return self._empty_result("No GPS data in image")
            
            # Parse GPS coordinates
            lat = self._get_decimal_coords(
                gps_info.get("GPSLatitude"),
                gps_info.get("GPSLatitudeRef", "N")
            )
            lon = self._get_decimal_coords(
                gps_info.get("GPSLongitude"),
                gps_info.get("GPSLongitudeRef", "E")
            )
            
            if lat is None or lon is None:
                return self._empty_result("Could not parse GPS coordinates")
            
            # Extract timestamp
            timestamp = self._parse_exif_datetime(
                exif_data.get("DateTimeOriginal") or 
                exif_data.get("DateTime")
            )
            
            # Validate within Odisha bounds
            in_bounds = self._validate_odisha_bounds(lat, lon)
            
            return {
                "success": True,
                "latitude": lat,
                "longitude": lon,
                "altitude": self._get_altitude(gps_info),
                "timestamp": timestamp,
                "in_odisha_bounds": in_bounds,
                "device_model": exif_data.get("Model", "Unknown"),
                "image_width": image.width,
                "image_height": image.height,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"EXIF extraction failed: {e}")
            return self._empty_result(str(e))
    
    def _get_exif_data(self, image: Image.Image) -> Dict:
        """Extract and decode EXIF data from image."""
        exif_raw = image._getexif()
        if not exif_raw:
            return {}
        
        exif_data = {}
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, tag_id)
            
            if tag == "GPSInfo":
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag] = gps_value
                exif_data[tag] = gps_data
            else:
                exif_data[tag] = value
        
        return exif_data
    
    def _get_decimal_coords(self, coords, ref: str) -> Optional[float]:
        """Convert EXIF GPS coordinates to decimal degrees."""
        if not coords:
            return None
        
        try:
            # Coords are typically (degrees, minutes, seconds) tuples
            if hasattr(coords[0], 'numerator'):
                # IFDRational format
                degrees = float(coords[0])
                minutes = float(coords[1])
                seconds = float(coords[2])
            else:
                degrees, minutes, seconds = coords
            
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            if ref in ['S', 'W']:
                decimal = -decimal
            
            return round(decimal, 6)
            
        except Exception as e:
            logger.error(f"Coordinate parsing error: {e}")
            return None
    
    def _get_altitude(self, gps_info: Dict) -> Optional[float]:
        """Extract altitude from GPS info."""
        alt = gps_info.get("GPSAltitude")
        if alt:
            try:
                return float(alt)
            except:
                pass
        return None
    
    def _parse_exif_datetime(self, dt_string: str) -> Optional[str]:
        """Parse EXIF datetime string to ISO format."""
        if not dt_string:
            return None
        
        try:
            # EXIF format: "YYYY:MM:DD HH:MM:SS"
            dt = datetime.strptime(dt_string, "%Y:%m:%d %H:%M:%S")
            return dt.isoformat()
        except:
            return None
    
    def _validate_odisha_bounds(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within Odisha bounds."""
        bounds = self.ODISHA_BOUNDS
        return (
            bounds["lat_min"] <= lat <= bounds["lat_max"] and
            bounds["lon_min"] <= lon <= bounds["lon_max"]
        )
    
    def _empty_result(self, error: str) -> Dict:
        """Return empty result with error message."""
        return {
            "success": False,
            "latitude": None,
            "longitude": None,
            "altitude": None,
            "timestamp": None,
            "in_odisha_bounds": False,
            "device_model": None,
            "image_width": None,
            "image_height": None,
            "error": error
        }


# Singleton instance
exif_service = ExifService()


if __name__ == "__main__":
    print("📸 EXIF GPS Extraction Service")
    print(f"   Pillow available: {PIL_AVAILABLE}")
    
    # Test with a sample result
    result = exif_service._empty_result("Test mode")
    print(f"   Empty result format: {result.keys()}")
