"""
Weather service using Open-Meteo (Free, No API Key).
Fetches historical and forecast weather data for flood validation.
"""

import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    # Open-Meteo endpoints
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    # Archive API requires dates at least 5 days in the past
    ARCHIVE_DELAY_DAYS = 5

    def get_current_weather(self, lat: float, lon: float) -> dict:
        """Fetch current weather context (precipitation, soil moisture)."""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "precipitation,rain,showers",
                "hourly": "precipitation_probability,precipitation",
                "timezone": "auto",
                "forecast_days": 1
            }
            response = requests.get(self.FORECAST_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant metrics
            current = data.get('current', {})
            return {
                "rainfall_mm": current.get('precipitation', 0.0),
                "is_raining": current.get('precipitation', 0.0) > 0.5,
                "timestamp": current.get('time'),
                "source": "open-meteo-forecast"
            }
        except Exception as e:
            logger.error(f"Weather API failed: {e}")
            return self._fallback_weather()

    def get_rainfall_history(self, lat: float, lon: float, days: int = 2) -> dict:
        """
        Fetch past rainfall for 'Antecedent Moisture Condition' (AMC).
        
        Uses forecast API for recent data (< 5 days), archive API for older data.
        """
        try:
            # For recent days, use forecast API with past_days parameter
            if days <= 7:
                return self._get_recent_rainfall(lat, lon, days)
            else:
                return self._get_historical_rainfall(lat, lon, days)
        except Exception as e:
            logger.error(f"Rainfall history fetch failed: {e}")
            return self._fallback_rainfall()

    def _get_recent_rainfall(self, lat: float, lon: float, days: int) -> dict:
        """Use forecast API with past_days for recent rainfall (up to 7 days)."""
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum",
                "timezone": "auto",
                "past_days": min(days, 7),
                "forecast_days": 1
            }
            response = requests.get(self.FORECAST_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            daily_values = data.get('daily', {}).get('precipitation_sum', [])
            # Sum up the past days (exclude today's forecast)
            past_values = daily_values[:-1] if len(daily_values) > 1 else daily_values
            total_rainfall = sum(x for x in past_values if x is not None)
            
            return {
                "total_rainfall_mm": total_rainfall,
                "days_analyzed": len(past_values),
                "risk_level": self._assess_risk(total_rainfall),
                "source": "open-meteo-forecast"
            }
        except Exception as e:
            logger.error(f"Recent rainfall API failed: {e}")
            return self._fallback_rainfall()

    def _get_historical_rainfall(self, lat: float, lon: float, days: int) -> dict:
        """Use archive API for historical data (> 5 days ago)."""
        try:
            # Archive API requires dates at least 5 days in the past
            end_date = datetime.now() - timedelta(days=self.ARCHIVE_DELAY_DAYS)
            start_date = end_date - timedelta(days=days)
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "precipitation_sum",
                "timezone": "auto"
            }
            response = requests.get(self.ARCHIVE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            daily_sum = data.get('daily', {}).get('precipitation_sum', [])
            total_rainfall = sum(x for x in daily_sum if x is not None)
            
            return {
                "total_rainfall_mm": total_rainfall,
                "days_analyzed": len(daily_sum),
                "risk_level": self._assess_risk(total_rainfall),
                "source": "open-meteo-archive"
            }
        except Exception as e:
            logger.error(f"Historical rainfall API failed: {e}")
            return self._fallback_rainfall()

    def _assess_risk(self, rainfall_mm: float) -> str:
        """Assess flood risk based on cumulative rainfall."""
        if rainfall_mm > 100:
            return "Extreme"
        elif rainfall_mm > 50:
            return "High"
        elif rainfall_mm > 20:
            return "Moderate"
        elif rainfall_mm > 5:
            return "Low"
        else:
            return "Minimal"

    def _fallback_weather(self) -> dict:
        """Fallback response when API fails."""
        return {
            "rainfall_mm": 0.0,
            "is_raining": False,
            "timestamp": None,
            "source": "fallback"
        }

    def _fallback_rainfall(self) -> dict:
        """Fallback response for rainfall history."""
        return {
            "total_rainfall_mm": 0.0,
            "days_analyzed": 0,
            "risk_level": "Unknown",
            "source": "fallback"
        }


# Singleton instance
weather_service = WeatherService()


if __name__ == "__main__":
    # Test the weather service
    print("🌧️ Weather Service Test")
    
    # Test coordinates (Cuttack, Odisha)
    lat, lon = 20.4625, 85.8830
    
    print(f"\n📍 Location: ({lat}, {lon})")
    
    # Current weather
    current = weather_service.get_current_weather(lat, lon)
    print(f"☁️ Current: {current}")
    
    # Recent rainfall
    rainfall = weather_service.get_rainfall_history(lat, lon, days=2)
    print(f"🌧️ Rainfall (2 days): {rainfall}")
