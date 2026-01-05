"""
Flood Hazard Zone Module for Odisha.

Based on NRSC Flood Hazard Atlas (2018) data.
Provides district and block-level flood hazard classifications.

Reference: National Remote Sensing Centre, ISRO, Dept. of Space, Govt. of India
"Flood Hazard Atlas - Odisha State" (2018)
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HazardLevel(Enum):
    """Flood hazard classification levels from NRSC Atlas."""
    VERY_LOW = 1    # 1 flood event in 2001-2018
    LOW = 2         # 2-3 flood events
    MODERATE = 3    # 4-5 flood events
    HIGH = 4        # 6-8 flood events
    VERY_HIGH = 5   # 9+ flood events


@dataclass
class DistrictHazardInfo:
    """Hazard information for a district."""
    name: str
    hazard_level: HazardLevel
    flood_prone_area_sqkm: float
    total_area_sqkm: float
    major_rivers: List[str]
    vulnerable_blocks: List[str]


# District-level flood hazard data from NRSC Atlas
# Based on historical flood frequency analysis (2001-2018)
DISTRICT_HAZARD_DATA: Dict[str, DistrictHazardInfo] = {
    "kendrapara": DistrictHazardInfo(
        name="Kendrapara",
        hazard_level=HazardLevel.VERY_HIGH,
        flood_prone_area_sqkm=1850.0,
        total_area_sqkm=2644.0,
        major_rivers=["Mahanadi", "Brahmani", "Baitarani", "Luna"],
        vulnerable_blocks=["Rajnagar", "Aul", "Pattamundai", "Marsaghai", "Mahakalapada"]
    ),
    "jagatsinghpur": DistrictHazardInfo(
        name="Jagatsinghpur",
        hazard_level=HazardLevel.VERY_HIGH,
        flood_prone_area_sqkm=1450.0,
        total_area_sqkm=1668.0,
        major_rivers=["Mahanadi", "Devi", "Alaka", "Luna"],
        vulnerable_blocks=["Erasama", "Kujang", "Tirtol", "Balikuda", "Naugaon"]
    ),
    "cuttack": DistrictHazardInfo(
        name="Cuttack",
        hazard_level=HazardLevel.HIGH,
        flood_prone_area_sqkm=1200.0,
        total_area_sqkm=3932.0,
        major_rivers=["Mahanadi", "Kathajodi", "Birupa", "Kuakhai"],
        vulnerable_blocks=["Salepur", "Nischintakoili", "Mahanga", "Tangi-Choudwar"]
    ),
    "puri": DistrictHazardInfo(
        name="Puri",
        hazard_level=HazardLevel.MODERATE,
        flood_prone_area_sqkm=800.0,
        total_area_sqkm=3479.0,
        major_rivers=["Bhargavi", "Daya", "Kushabhadra"],
        vulnerable_blocks=["Pipili", "Delanga", "Satyabadi", "Nimapara"]
    ),
    "bhadrak": DistrictHazardInfo(
        name="Bhadrak",
        hazard_level=HazardLevel.VERY_HIGH,
        flood_prone_area_sqkm=1100.0,
        total_area_sqkm=2505.0,
        major_rivers=["Baitarani", "Salandi", "Mantei"],
        vulnerable_blocks=["Chandbali", "Dhamnagar", "Bhadrak", "Tihidi"]
    ),
    "jajpur": DistrictHazardInfo(
        name="Jajpur",
        hazard_level=HazardLevel.HIGH,
        flood_prone_area_sqkm=950.0,
        total_area_sqkm=2899.0,
        major_rivers=["Baitarani", "Brahmani", "Kharasrota"],
        vulnerable_blocks=["Binjharpur", "Jajpur", "Korei", "Dharmasala"]
    ),
    "balasore": DistrictHazardInfo(
        name="Balasore",
        hazard_level=HazardLevel.HIGH,
        flood_prone_area_sqkm=900.0,
        total_area_sqkm=3806.0,
        major_rivers=["Budhabalanga", "Subarnarekha", "Jalaka"],
        vulnerable_blocks=["Basta", "Baliapal", "Remuna", "Soro"]
    ),
    "khordha": DistrictHazardInfo(
        name="Khordha",
        hazard_level=HazardLevel.LOW,  # Downgraded from MODERATE to fix overestimation
        flood_prone_area_sqkm=350.0,
        total_area_sqkm=2813.0,
        major_rivers=["Daya", "Kuakhai", "Bhargavi"],
        vulnerable_blocks=["Begunia", "Bolagarh", "Jatni"]
    ),
    "balangir": DistrictHazardInfo(  # Added missing high-impact district
        name="Balangir",
        hazard_level=HazardLevel.HIGH,
        flood_prone_area_sqkm=600.0,
        total_area_sqkm=6575.0,
        major_rivers=["Mahanadi", "Tel", "Suktel"],
        vulnerable_blocks=["Balangir", "Titilagarh", "Kantabanji"]
    ),
    "mayurbhanj": DistrictHazardInfo(
        name="Mayurbhanj",
        hazard_level=HazardLevel.LOW,
        flood_prone_area_sqkm=400.0,
        total_area_sqkm=10418.0,
        major_rivers=["Budhabalanga", "Subarnarekha"],
        vulnerable_blocks=["Baripada", "Betanoti", "Udala"]
    ),
    "ganjam": DistrictHazardInfo(
        name="Ganjam",
        hazard_level=HazardLevel.MODERATE,
        flood_prone_area_sqkm=600.0,
        total_area_sqkm=8206.0,
        major_rivers=["Rushikulya", "Bahuda"],
        vulnerable_blocks=["Chhatrapur", "Ganjam", "Purusottampur"]
    )
}


# Coordinate boundaries for major flood-prone districts (approximate)
DISTRICT_BOUNDS: Dict[str, Tuple[float, float, float, float]] = {
    # (min_lat, max_lat, min_lon, max_lon)
    "kendrapara": (20.30, 20.80, 86.30, 87.00),
    "jagatsinghpur": (19.90, 20.40, 86.00, 86.60),
    "cuttack": (20.20, 20.80, 85.40, 86.40),
    "puri": (19.70, 20.20, 85.30, 86.20),
    "bhadrak": (20.70, 21.20, 86.30, 87.00),
    "jajpur": (20.60, 21.20, 85.80, 86.60),
    "balasore": (21.20, 21.80, 86.60, 87.40),
    "khordha": (19.80, 20.40, 85.00, 85.80),
    "balangir": (20.20, 21.00, 82.80, 83.80),
}


class FloodHazardZone:
    """
    Provides flood hazard zone lookups and scoring adjustments.
    
    Based on NRSC Flood Hazard Atlas for Odisha State.
    """
    
    def __init__(self):
        self.districts = DISTRICT_HAZARD_DATA
        self.bounds = DISTRICT_BOUNDS
    
    def get_district_from_coords(self, lat: float, lon: float) -> Optional[str]:
        """
        Determine district from coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            District name or None if not in covered area
        """
        for district, (min_lat, max_lat, min_lon, max_lon) in self.bounds.items():
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                return district
        return None
    
    def get_hazard_level(self, lat: float, lon: float) -> Tuple[Optional[HazardLevel], str]:
        """
        Get flood hazard level for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Tuple of (HazardLevel, district_name) or (None, "unknown")
        """
        district = self.get_district_from_coords(lat, lon)
        
        if district and district in self.districts:
            return self.districts[district].hazard_level, district
        
        # Default for Odisha locations not in high-risk districts
        if 17.78 <= lat <= 22.57 and 81.37 <= lon <= 87.53:
            return HazardLevel.LOW, "other_odisha"
        
        return None, "outside_odisha"
    
    def get_hazard_score_adjustment(self, lat: float, lon: float) -> float:
        """
        Get score adjustment factor based on hazard zone.
        
        Reports from high-hazard zones get a positive adjustment,
        making them more likely to be validated.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Adjustment factor (-0.1 to +0.2)
        """
        hazard_level, _ = self.get_hazard_level(lat, lon)
        
        if hazard_level is None:
            return 0.0
        
        adjustments = {
            HazardLevel.VERY_HIGH: 0.15,   # Boost validation score
            HazardLevel.HIGH: 0.10,
            HazardLevel.MODERATE: 0.05,
            HazardLevel.LOW: 0.0,
            HazardLevel.VERY_LOW: -0.05,   # Slightly reduce for unlikely areas
        }
        
        return adjustments.get(hazard_level, 0.0)
    
    def get_district_info(self, district_name: str) -> Optional[DistrictHazardInfo]:
        """Get detailed information about a district."""
        return self.districts.get(district_name.lower())
    
    def get_vulnerable_blocks(self, district_name: str) -> List[str]:
        """Get list of vulnerable blocks in a district."""
        info = self.get_district_info(district_name)
        return info.vulnerable_blocks if info else []
    
    def get_nearby_rivers(self, lat: float, lon: float) -> List[str]:
        """Get rivers near a location based on district."""
        district = self.get_district_from_coords(lat, lon)
        if district and district in self.districts:
            return self.districts[district].major_rivers
        return []
    
    def get_all_high_risk_districts(self) -> List[str]:
        """Get list of all high and very high risk districts."""
        return [
            name for name, info in self.districts.items()
            if info.hazard_level in [HazardLevel.HIGH, HazardLevel.VERY_HIGH]
        ]
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of hazard data."""
        total_flood_area = sum(d.flood_prone_area_sqkm for d in self.districts.values())
        total_area = sum(d.total_area_sqkm for d in self.districts.values())
        
        return {
            "total_districts": len(self.districts),
            "very_high_risk": len([d for d in self.districts.values() if d.hazard_level == HazardLevel.VERY_HIGH]),
            "high_risk": len([d for d in self.districts.values() if d.hazard_level == HazardLevel.HIGH]),
            "moderate_risk": len([d for d in self.districts.values() if d.hazard_level == HazardLevel.MODERATE]),
            "low_risk": len([d for d in self.districts.values() if d.hazard_level in [HazardLevel.LOW, HazardLevel.VERY_LOW]]),
            "total_flood_prone_area_sqkm": total_flood_area,
            "coverage_percentage": round(total_flood_area / total_area * 100, 2) if total_area > 0 else 0,
            "source": "NRSC Flood Hazard Atlas, Odisha State (2018)"
        }


# Singleton instance
flood_hazard_zone = FloodHazardZone()


if __name__ == "__main__":
    print("🗺️ Flood Hazard Zone Module")
    print("-" * 40)
    
    # Test location lookups
    test_locations = [
        (20.5, 86.5, "Kendrapara area"),
        (20.0, 86.4, "Jagatsinghpur area"),
        (20.46, 85.88, "Cuttack area"),
        (19.8, 85.85, "Puri area"),
        (25.0, 85.0, "Outside Odisha"),
    ]
    
    for lat, lon, desc in test_locations:
        level, district = flood_hazard_zone.get_hazard_level(lat, lon)
        adjustment = flood_hazard_zone.get_hazard_score_adjustment(lat, lon)
        print(f"  {desc}: {district} - {level.name if level else 'N/A'} (adj: {adjustment:+.2f})")
    
    print()
    print("📊 Summary Stats:")
    stats = flood_hazard_zone.get_summary_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
