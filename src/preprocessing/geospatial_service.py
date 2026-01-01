"""
Geospatial service for ground truth validation.
Manages:
1. Simulated Bhuvan Flood Layers (GeoJSON) - Zero Cost
2. OpenStreetMap Context (via Overpass API or local cache) - Free
"""

import logging
import json
from shapely.geometry import Point, shape
from pathlib import Path

logger = logging.getLogger(__name__)

class GeospatialService:
    def __init__(self):
        self.flood_zones = []
        self._load_mock_bhuvan_data()
        
    def _load_mock_bhuvan_data(self):
        """
        Load simulated Bhuvan flood extent polygons.
        In production, this would load actual .shp/.geojson files downloaded from Bhuvan.
        """
        try:
            # Create a mock flood zone around Cuttack/Mahanadi for testing
            mock_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"risk": "High", "source": "Bhuvan-2024"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [85.80, 20.45], [85.95, 20.45], 
                                [85.95, 20.55], [85.80, 20.55], 
                                [85.80, 20.45]
                            ]]
                        }
                    }
                ]
            }
            
            for feature in mock_data['features']:
                geom = shape(feature['geometry'])
                self.flood_zones.append({
                    'geometry': geom,
                    'properties': feature['properties']
                })
            logger.info(f"Loaded {len(self.flood_zones)} flood zones (Simulated Bhuvan)")
            
        except Exception as e:
            logger.error(f"Failed to load geospatial data: {e}")

    def check_ground_truth(self, lat: float, lon: float) -> dict:
        """Check if point falls within official flood layers."""
        point = Point(lon, lat)
        
        for zone in self.flood_zones:
            if zone['geometry'].contains(point):
                return {
                    "in_flood_zone": True,
                    "source": zone['properties']['source'],
                    "risk_level": zone['properties']['risk']
                }
        
        return {
            "in_flood_zone": False,
            "source": None,
            "risk_level": "None"
        }

    def get_nearest_river_distance(self, lat: float, lon: float) -> float:
        """
        Estimate distance to river using static river geometries.
        Replace with actual OSM river network query in future.
        """
        # Mock Mahanadi location line approximation
        # Ideally using Shapely distance to MultiLineString of rivers
        return 0.5  # Placeholder: 500m

# Singleton
geo_service = GeospatialService()
