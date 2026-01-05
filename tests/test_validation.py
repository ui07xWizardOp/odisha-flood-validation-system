import pytest
from datetime import datetime
import pandas as pd
from src.validation.validator import FloodReportValidator
from src.validation.layer1_physical import PhysicalValidator

# Mock features for testing without actual rasters
MOCK_FEATURES_FLOODABLE = {
    'hand': 0.5,          # Very low HAND -> hand_score = 1.0
    'slope': 1.5,         # Flat slope (good)
    'elevation_diff_from_neighbors': -3.0  # Depression -> elev_score = 1.0
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
    
    # Should be high score (HAND < 1m -> hand_score = 1.0)
    assert result['layer1_score'] > 0.8, f"Expected > 0.8, got {result['layer1_score']}"
    assert result['hand_score'] == 1.0, f"Expected 1.0, got {result['hand_score']}"

def test_physical_validator_impossible():
    """Test Layer 1 with impossible flood conditions."""
    validator = PhysicalValidator()
    result = validator.validate(20.5, 85.5, 1.0, MOCK_FEATURES_IMPOSSIBLE)
    
    # Should be low score (slope > 30 -> slope_score = 0.0)
    assert result['layer1_score'] < 0.3, f"Expected < 0.3, got {result['layer1_score']}"
    assert result['slope_score'] == 0.0, f"Expected 0.0, got {result['slope_score']}"

def test_full_validator_pipeline():
    """Integration test for the full 5-layer validator."""
    from unittest.mock import MagicMock, patch
    
    # Mock external services to avoid network calls
    with patch('src.validation.validator.weather_service') as mock_weather, \
         patch('src.validation.validator.geo_service') as mock_geo, \
         patch('src.validation.validator.social_service') as mock_social:
        
        # Configure mocks
        mock_weather.get_current_weather.return_value = {'rainfall_mm': 50.0}
        mock_geo.check_ground_truth.return_value = {'in_flood_zone': True}
        mock_social.get_social_context.return_value = {'buzz_score': 0.7, 'recent_headlines': []}
        
        validator = FloodReportValidator()
        validator.extractor.extract_all_features = MagicMock(return_value=MOCK_FEATURES_FLOODABLE)
        
        result = validator.validate_report(
            report_id=1, user_id=1, lat=20.5, lon=85.5, depth=1.0, timestamp=datetime.now(),
            rainfall_24h=50.0  # Explicitly pass rainfall
        )
        
        # With good features + ground truth boost, should validate
        assert result['final_score'] > 0.5, f"Expected > 0.5, got {result['final_score']}"
        print(f"\\nFinal Score: {result['final_score']}")

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
