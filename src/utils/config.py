"""
Configuration Management for Odisha Flood Validation System.

Centralizes all environment variables, constants, and settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # ==========================================
    # Database Configuration
    # ==========================================
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "flood_validation")
    DB_USER = os.getenv("DB_USER", "flood_admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "flood_secure_password_2024")
    
    @classmethod
    def get_database_url(cls) -> str:
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    # ==========================================
    # API Configuration
    # ==========================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev-secret-key-change-in-production")
    
    # ==========================================
    # External API Keys
    # ==========================================
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
    MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "")
    
    # ==========================================
    # Study Area Configuration (Mahanadi Delta)
    # ==========================================
    ODISHA_BBOX = {
        "min_lat": 19.5,
        "max_lat": 21.5,
        "min_lon": 84.5,
        "max_lon": 87.0
    }
    
    # Reference points
    CUTTACK_CENTER = (20.4625, 85.8830)  # lat, lon
    PURI_CENTER = (19.8135, 85.8312)
    BHUBANESWAR_CENTER = (20.2961, 85.8245)
    
    # ==========================================
    # Validation Algorithm Parameters
    # ==========================================
    VALIDATION_THRESHOLD = 0.7  # Score >= 0.7 = validated
    
    LAYER_WEIGHTS = {
        "physical": 0.4,
        "statistical": 0.4,
        "reputation": 0.2
    }
    
    # Physical Layer (Layer 1)
    MAX_HAND_THRESHOLD_M = 10.0      # Above this = unlikely flood
    SUSPICIOUS_HAND_THRESHOLD_M = 5.0
    STEEP_SLOPE_DEG = 15.0
    MAX_SLOPE_DEG = 30.0
    LOCAL_HIGH_DIFF_M = 5.0
    
    # Statistical Layer (Layer 2)
    SPATIAL_RADIUS_DEG = 0.002  # ~220m at equator
    MIN_CLUSTER_SIZE = 3
    
    # Reputation Layer (Layer 3)
    TRUST_INCREMENT = 0.1
    TRUST_DECREMENT = 0.15
    INITIAL_TRUST = 0.5
    
    # ==========================================
    # Data Paths
    # ==========================================
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
    RESULTS_DIR = PROJECT_ROOT / "results"
    
    # Raster paths (relative to PROCESSED_DATA_DIR)
    DEM_PATH = PROCESSED_DATA_DIR / "mahanadi_dem_30m.tif"
    HAND_PATH = PROCESSED_DATA_DIR / "mahanadi_hand.tif"
    SLOPE_PATH = PROCESSED_DATA_DIR / "mahanadi_slope.tif"
    
    # ==========================================
    # Disaster Keywords for Social Media
    # ==========================================
    DISASTER_KEYWORDS = [
        "flood", "flooding", "water logging", "cyclone fani",
        "mahanadi", "cuttack flood", "puri flood", "odisha disaster",
        "stranded", "rescue", "waterlogged", "submerged",
        "heavy rain", "embankment breach", "river overflow"
    ]
    
    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """Return all config as dictionary."""
        return {
            key: getattr(cls, key) 
            for key in dir(cls) 
            if not key.startswith('_') and key.isupper()
        }


# Singleton instance
config = Config()
