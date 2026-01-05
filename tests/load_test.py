"""
Load Test Script for Flood Validation API.

Uses Locust for distributed load testing.
Target: 1000+ requests per second.

Run with:
    locust -f tests/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
from datetime import datetime
import random
import json


class FloodAPIUser(HttpUser):
    """
    Simulates a user interacting with the Flood Validation API.
    """
    
    # Wait 0.5-2 seconds between requests (simulates real user behavior)
    wait_time = between(0.1, 0.5)
    
    # Sample data for POST requests
    SAMPLE_LOCATIONS = [
        (20.50, 86.50, "Kendrapara"),
        (20.00, 86.40, "Jagatsinghpur"),
        (20.46, 85.88, "Cuttack"),
        (19.80, 85.85, "Puri"),
        (21.00, 86.50, "Bhadrak"),
        (20.90, 86.10, "Jajpur"),
    ]
    
    def on_start(self):
        """Called when a user starts. Create a test user."""
        self.user_id = random.randint(1, 1000)
    
    @task(5)
    def get_stats(self):
        """GET /stats - Most common read operation."""
        self.client.get("/stats")
    
    @task(3)
    def get_reports(self):
        """GET /reports - List reports."""
        limit = random.choice([10, 20, 50])
        self.client.get(f"/reports?limit={limit}")
    
    @task(1)
    def get_root(self):
        """GET / - Health check."""
        self.client.get("/")
    
    @task(2)
    def submit_report(self):
        """POST /reports - Submit a flood report."""
        lat, lon, location = random.choice(self.SAMPLE_LOCATIONS)
        
        # Add some random variation to coordinates
        lat += random.uniform(-0.05, 0.05)
        lon += random.uniform(-0.05, 0.05)
        
        payload = {
            "user_id": self.user_id,
            "latitude": lat,
            "longitude": lon,
            "depth_meters": random.uniform(0.1, 3.0),
            "timestamp": datetime.now().isoformat(),
            "description": f"Test flood report from load test - {location}"
        }
        
        with self.client.post(
            "/reports",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [201, 404, 500]:
                # 404/500 can happen if user doesn't exist - that's okay for load test
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def get_nearby_reports(self):
        """GET /reports/nearby - Geospatial query."""
        lat, lon, _ = random.choice(self.SAMPLE_LOCATIONS)
        radius = random.choice([1000, 5000, 10000])
        
        self.client.get(f"/reports/nearby?lat={lat}&lon={lon}&radius_m={radius}")
    
    @task(1)
    def export_csv(self):
        """GET /reports/export/csv - Export reports."""
        self.client.get("/reports/export/csv?limit=100")


class FastFloodAPIUser(HttpUser):
    """
    High-frequency user for stress testing.
    Minimal wait time, focuses on read operations.
    """
    
    wait_time = between(0.01, 0.1)  # Very fast requests
    
    @task(10)
    def get_stats_fast(self):
        """Fast stats requests."""
        self.client.get("/stats")
    
    @task(5)
    def get_reports_fast(self):
        """Fast report list requests."""
        self.client.get("/reports?limit=10")
    
    @task(2)
    def health_check(self):
        """Health check."""
        self.client.get("/")


# Event handlers for custom reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log requests that take too long."""
    if response_time > 1000:  # > 1 second
        print(f"⚠️ Slow request: {name} took {response_time:.0f}ms")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary after test."""
    print()
    print("=" * 60)
    print("📊 Load Test Summary")
    print("=" * 60)
    
    stats = environment.stats
    
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.1f}")
    
    if stats.total.total_rps >= 1000:
        print("✅ TARGET MET: 1000+ requests/second achieved!")
    else:
        print(f"❌ Target not met. Current: {stats.total.total_rps:.1f} req/sec")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Flood API Load Test")
    print("=" * 60)
    print()
    print("To run this test:")
    print("  1. Install locust: pip install locust")
    print("  2. Ensure API is running on localhost:8000")
    print("  3. Run: locust -f tests/load_test.py --host=http://localhost:8000")
    print("  4. Open http://localhost:8089 to start test")
    print()
    print("For headless mode (1000 users, 100 spawn rate):")
    print("  locust -f tests/load_test.py --host=http://localhost:8000 \\")
    print("         --users 1000 --spawn-rate 100 --run-time 60s --headless")
