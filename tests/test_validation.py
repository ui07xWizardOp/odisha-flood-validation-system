import pytest
from datetime import datetime
import pandas as pd
from src.validation.validator import FloodReportValidator
from src.validation.layer1_physical import PhysicalValidator

# Mock features for testing without actual rasters
MOCK_FEATURES_FLOODABLE = {
    'hand': 2.0,          # Low HAND (good)
    'slope': 1.5,         # Flat slope (good)
    'elevation_diff_from_neighbors': -0.5 # Slightly low-lying (good)
}

MOCK_FEATURES_IMPOSSIBLE = {
    'hand': 15.0,         # High HAND (bad)
    'slope': 35.0,        # Steep slope (bad)
    'elevation_diff_from_neighbors': 12.0 # Local peak (bad)
}

def test_physical_validator_plausible():
    """Test Layer 1 with plausible flood conditions."""
    validator = PhysicalValidator()
    result = validator.validate(20.5, 85.5, 1.0, MOCK_FEATURES_FLOODABLE)
    
    # Should be high score
    assert result['layer1_score'] > 0.8
    assert result['hand_score'] == 1.0

def test_physical_validator_impossible():
    """Test Layer 1 with impossible flood conditions."""
    validator = PhysicalValidator()
    result = validator.validate(20.5, 85.5, 1.0, MOCK_FEATURES_IMPOSSIBLE)
    
    # Should be low score
    assert result['layer1_score'] < 0.3
    assert result['slope_score'] == 0.0

def test_full_validator_pipeline():
    """Integration test for the full validator."""
    # We need to patch FeatureExtractor because we might not have rasters
    # Check src/validation/validator.py to see how to inject mock or use unittest.mock
    
    from unittest.mock import MagicMock
    
    validator = FloodReportValidator()
    validator.extractor.extract_all_features = MagicMock(return_value=MOCK_FEATURES_FLOODABLE)
    validator.layer3.get_trust_score = MagicMock(return_value=0.8) # High trust user
    
    result = validator.validate_report(
        report_id=1, user_id=1, lat=20.5, lon=85.5, depth=1.0, timestamp=datetime.now(),
        rainfall_24h=50.0 # Some rain
    )
    
    assert result['status'] == 'validated'
    assert result['final_score'] > 0.7
    print(f"\nFinal Score: {result['final_score']}")

if __name__ == "__main__":
    # Manual run
    try:
        test_physical_validator_plausible()
        print("✅ test_physical_validator_plausible passed")
        test_physical_validator_impossible()
        print("✅ test_physical_validator_impossible passed")
        test_full_validator_pipeline()
        print("✅ test_full_validator_pipeline passed")
    except Exception as e:
        print(f"❌ Tests failed: {e}")
