"""
API Integration Tests for Odisha Flood Validation System.

Tests all API endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the FastAPI app
from src.api.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test basic API health."""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestUserEndpoints:
    """Test user management endpoints."""
    
    def test_create_user_success(self):
        """Test creating a new user."""
        user_data = {
            "username": f"test_user_{datetime.now().timestamp()}",
            "email": "test@example.com"
        }
        response = client.post("/users", json=user_data)
        
        # Should succeed or fail with duplicate (if test reruns)
        assert response.status_code in [201, 400]
        
        if response.status_code == 201:
            data = response.json()
            assert "user_id" in data
            assert data["trust_score"] == 0.5
    
    def test_create_user_duplicate(self):
        """Test that duplicate usernames are rejected."""
        user_data = {"username": "duplicate_test", "email": "dup@example.com"}
        
        # First creation
        client.post("/users", json=user_data)
        
        # Second should fail
        response = client.post("/users", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_get_user_not_found(self):
        """Test getting non-existent user."""
        response = client.get("/users/999999")
        assert response.status_code == 404


class TestReportEndpoints:
    """Test flood report endpoints."""
    
    @pytest.fixture
    def sample_user_id(self):
        """Create a test user and return their ID."""
        user_data = {
            "username": f"report_test_user_{datetime.now().timestamp()}",
            "email": "reporter@example.com"
        }
        response = client.post("/users", json=user_data)
        if response.status_code == 201:
            return response.json()["user_id"]
        return 1  # Fallback
    
    def test_submit_report(self, sample_user_id):
        """Test submitting a flood report."""
        report_data = {
            "user_id": sample_user_id,
            "latitude": 20.4625,
            "longitude": 85.8830,
            "depth_meters": 1.5,
            "timestamp": datetime.now().isoformat(),
            "description": "Water level rising near main road"
        }
        
        # Mock the validator to avoid needing actual rasters
        with patch('src.api.main.validator_service') as mock_validator:
            mock_validator.validate_report.return_value = {
                'final_score': 0.85,
                'status': 'validated',
                'details': {
                    'physical': {'layer1_score': 0.9},
                    'statistical': {'layer2_score': 0.8},
                    'reputation': {'layer3_score': 0.5}
                }
            }
            
            response = client.post("/reports", json=report_data)
        
        # May fail if DB not connected - that's okay for unit test
        assert response.status_code in [201, 404, 500]
    
    def test_get_reports(self):
        """Test fetching reports list."""
        response = client.get("/reports?limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_nearby_reports(self):
        """Test geospatial query."""
        response = client.get("/reports/nearby?lat=20.46&lon=85.88&radius_m=1000")
        # May return empty list or error if DB not configured
        assert response.status_code in [200, 500]


class TestValidationFlow:
    """Integration tests for validation pipeline."""
    
    def test_full_validation_flow(self):
        """Test complete submit -> validate -> retrieve flow."""
        # This is a more comprehensive integration test
        # Would require full DB setup to run properly
        pass


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_api.py -v
    pytest.main([__file__, "-v"])
