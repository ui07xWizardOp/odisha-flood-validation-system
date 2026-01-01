"""
Weather service using Open-Meteo (Free, No API Key).
Fetches historical and forecast weather data for flood validation.
"""

import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

    def get_current_weather(self, lat: float, lon: float):
        """Fetch current weather context (precipitation, soil moisture)."""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "precipitation,rain,showers,soil_moisture_0_to_1cm",
                "hourly": "precipitation_probability,soil_moisture_0_to_1cm",
                "timezone": "auto",
                "forecast_days": 1
            }
            response = requests.get(self.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant metrics
            current = data.get('current', {})
            return {
                "rainfall_mm": current.get('precipitation', 0.0),
                "soil_moisture": current.get('soil_moisture_0_to_1cm', 0.0),
                "is_raining": current.get('precipitation', 0.0) > 0.5,
                "timestamp": current.get('time')
            }
        except Exception as e:
            logger.error(f"Weather API failed: {e}")
            return None

    def get_rainfall_history(self, lat: float, lon: float, days: int = 2):
        """Fetch past rainfall for 'Antecedent Moisture Condition' (AMC)."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "precipitation_sum",
                "timezone": "auto"
            }
            response = requests.get(self.HISTORICAL_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            daily_sum = data.get('daily', {}).get('precipitation_sum', [])
            total_rainfall = sum(x for x in daily_sum if x is not None)
            
            return {
                "total_rainfall_48h": total_rainfall,
                "risk_level": "High" if total_rainfall > 50 else "Low"
            }
        except Exception as e:
            logger.error(f"Historical Weather API failed: {e}")
            return {"total_rainfall_48h": 0.0, "risk_level": "Unknown"}

# Singleton instance
weather_service = WeatherService()
