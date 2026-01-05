"""
Temporal Analysis Module for Flood Event Detection.

Analyzes time-series patterns in flood reports to:
- Detect flood events (start, peak, end)
- Predict flood spread patterns
- Identify seasonal trends
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import scipy for signal processing
try:
    from scipy import signal
    from scipy.stats import zscore
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("SciPy not available. Some temporal analysis features disabled.")


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in flood reports.
    
    Features:
    - Event detection (clustering reports into flood events)
    - Trend analysis (daily, weekly, seasonal)
    - Spread pattern prediction
    """
    
    def __init__(self, event_threshold: float = 5.0, 
                 min_event_reports: int = 3,
                 event_duration_hours: int = 48):
        """
        Args:
            event_threshold: Z-score threshold for event detection
            min_event_reports: Minimum reports to constitute an event
            event_duration_hours: Time window for grouping reports
        """
        self.event_threshold = event_threshold
        self.min_event_reports = min_event_reports
        self.event_duration_hours = event_duration_hours
    
    def analyze_report_sequence(self, reports: List[Dict]) -> Dict:
        """
        Analyze a sequence of flood reports for temporal patterns.
        
        Args:
            reports: List of report dicts with 'timestamp', 'latitude', 'longitude'
            
        Returns:
            Dict with detected events and trends
        """
        if not reports:
            return {"events": [], "trend": None, "summary": "No reports to analyze"}
        
        # Sort by timestamp
        sorted_reports = sorted(reports, key=lambda r: r.get('timestamp', ''))
        
        # Extract time series
        timestamps = []
        for r in sorted_reports:
            ts = r.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    continue
            elif isinstance(ts, datetime):
                pass
            else:
                continue
            timestamps.append(ts)
        
        if not timestamps:
            return {"events": [], "trend": None, "summary": "No valid timestamps"}
        
        # Compute hourly counts
        hourly_counts = self._compute_hourly_counts(timestamps)
        
        # Detect events
        events = self._detect_events(sorted_reports, hourly_counts)
        
        # Analyze trend
        trend = self._analyze_trend(hourly_counts)
        
        return {
            "events": events,
            "trend": trend,
            "total_reports": len(reports),
            "time_span_hours": self._compute_time_span(timestamps),
            "peak_hour": self._find_peak_hour(hourly_counts),
            "summary": f"Detected {len(events)} flood events from {len(reports)} reports"
        }
    
    def _compute_hourly_counts(self, timestamps: List[datetime]) -> Dict[str, int]:
        """Compute report counts per hour."""
        counts = defaultdict(int)
        
        for ts in timestamps:
            hour_key = ts.strftime("%Y-%m-%d %H:00")
            counts[hour_key] += 1
        
        return dict(counts)
    
    def _detect_events(self, reports: List[Dict], 
                       hourly_counts: Dict[str, int]) -> List[Dict]:
        """Detect distinct flood events using clustering."""
        events = []
        current_event_reports = []
        last_timestamp = None
        
        for report in reports:
            ts = report.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    continue
            elif not isinstance(ts, datetime):
                continue
            
            # Check if this report belongs to current event or starts new one
            if last_timestamp is None:
                current_event_reports = [report]
            elif (ts - last_timestamp).total_seconds() / 3600 <= self.event_duration_hours:
                current_event_reports.append(report)
            else:
                # Save current event if it meets threshold
                if len(current_event_reports) >= self.min_event_reports:
                    events.append(self._summarize_event(current_event_reports, len(events) + 1))
                current_event_reports = [report]
            
            last_timestamp = ts
        
        # Don't forget last event
        if len(current_event_reports) >= self.min_event_reports:
            events.append(self._summarize_event(current_event_reports, len(events) + 1))
        
        return events
    
    def _summarize_event(self, reports: List[Dict], event_id: int) -> Dict:
        """Create summary for a detected flood event."""
        timestamps = []
        lats = []
        lons = []
        depths = []
        
        for r in reports:
            ts = r.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    timestamps.append(ts)
                except:
                    pass
            
            if r.get('latitude'):
                lats.append(r['latitude'])
            if r.get('longitude'):
                lons.append(r['longitude'])
            if r.get('depth_meters'):
                depths.append(r['depth_meters'])
        
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        
        return {
            "event_id": f"FL-{event_id:03d}",
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "duration_hours": (end_time - start_time).total_seconds() / 3600 if start_time and end_time else 0,
            "report_count": len(reports),
            "centroid": {
                "lat": np.mean(lats) if lats else None,
                "lon": np.mean(lons) if lons else None
            },
            "avg_depth_meters": np.mean(depths) if depths else None,
            "max_depth_meters": max(depths) if depths else None,
            "severity": self._classify_severity(len(reports), max(depths) if depths else 0)
        }
    
    def _classify_severity(self, report_count: int, max_depth: float) -> str:
        """Classify event severity based on report count and depth."""
        if report_count > 50 or max_depth > 2.0:
            return "critical"
        elif report_count > 20 or max_depth > 1.0:
            return "high"
        elif report_count > 10 or max_depth > 0.5:
            return "moderate"
        else:
            return "low"
    
    def _analyze_trend(self, hourly_counts: Dict[str, int]) -> Dict:
        """Analyze reporting trend."""
        if not hourly_counts:
            return {"direction": "stable", "rate": 0.0}
        
        counts = list(hourly_counts.values())
        
        if len(counts) < 3:
            return {"direction": "insufficient_data", "rate": 0.0}
        
        # Compute simple moving average
        recent = counts[-3:]
        earlier = counts[:3] if len(counts) >= 6 else counts[:len(counts)//2]
        
        recent_avg = np.mean(recent)
        earlier_avg = np.mean(earlier)
        
        if recent_avg > earlier_avg * 1.5:
            direction = "increasing"
        elif recent_avg < earlier_avg * 0.5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        rate = (recent_avg - earlier_avg) / max(earlier_avg, 1)
        
        return {
            "direction": direction,
            "rate": float(rate),
            "recent_avg_per_hour": float(recent_avg),
            "earlier_avg_per_hour": float(earlier_avg)
        }
    
    def _compute_time_span(self, timestamps: List[datetime]) -> float:
        """Compute time span in hours."""
        if len(timestamps) < 2:
            return 0.0
        return (max(timestamps) - min(timestamps)).total_seconds() / 3600
    
    def _find_peak_hour(self, hourly_counts: Dict[str, int]) -> Optional[str]:
        """Find the hour with most reports."""
        if not hourly_counts:
            return None
        return max(hourly_counts, key=hourly_counts.get)
    
    def predict_spread(self, event: Dict, hours_ahead: int = 6) -> Dict:
        """
        Predict flood spread pattern based on event data.
        
        This is a simplified model based on:
        - Current centroid location
        - River network (simulated)
        - Terrain slope (simulated)
        """
        if not event.get('centroid', {}).get('lat'):
            return {"error": "No location data available"}
        
        lat = event['centroid']['lat']
        lon = event['centroid']['lon']
        
        # Simulate downstream spread (simplified)
        # In reality, this would use DEM and river network data
        spread_predictions = []
        
        for hour in range(1, hours_ahead + 1):
            # Simulate movement downstream (roughly east/south in Odisha)
            predicted_lat = lat - 0.01 * hour  # Move south
            predicted_lon = lon + 0.005 * hour  # Move east
            
            spread_predictions.append({
                "hours_ahead": hour,
                "predicted_lat": predicted_lat,
                "predicted_lon": predicted_lon,
                "confidence": max(0.3, 1 - hour * 0.1)  # Decreasing confidence
            })
        
        return {
            "event_id": event.get('event_id'),
            "current_centroid": event.get('centroid'),
            "predictions": spread_predictions,
            "model": "simplified_downstream"
        }
    
    def get_seasonal_analysis(self, reports: List[Dict]) -> Dict:
        """Analyze seasonal patterns in flood reports."""
        monthly_counts = defaultdict(int)
        
        for r in reports:
            ts = r.get('timestamp')
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    continue
            elif not isinstance(ts, datetime):
                continue
            
            month_key = ts.strftime("%B")  # Month name
            monthly_counts[month_key] += 1
        
        # Find peak months
        sorted_months = sorted(monthly_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "monthly_distribution": dict(monthly_counts),
            "peak_month": sorted_months[0][0] if sorted_months else None,
            "monsoon_reports": sum(
                monthly_counts.get(m, 0) 
                for m in ["June", "July", "August", "September"]
            ),
            "total_reports": len(reports)
        }


# Singleton instance
temporal_analyzer = TemporalAnalyzer()


if __name__ == "__main__":
    print("⏱️ Temporal Analysis Module")
    print(f"   SciPy available: {SCIPY_AVAILABLE}")
    
    # Test with mock data
    mock_reports = [
        {"timestamp": "2024-07-15T08:00:00", "latitude": 20.5, "longitude": 85.8, "depth_meters": 0.5},
        {"timestamp": "2024-07-15T09:00:00", "latitude": 20.51, "longitude": 85.81, "depth_meters": 0.8},
        {"timestamp": "2024-07-15T10:00:00", "latitude": 20.52, "longitude": 85.82, "depth_meters": 1.2},
        {"timestamp": "2024-07-15T11:00:00", "latitude": 20.53, "longitude": 85.83, "depth_meters": 1.5},
        {"timestamp": "2024-07-16T08:00:00", "latitude": 20.3, "longitude": 86.5, "depth_meters": 0.3},
    ]
    
    result = temporal_analyzer.analyze_report_sequence(mock_reports)
    print(f"   Analysis: {json.dumps(result, indent=2, default=str)}")
