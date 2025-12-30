import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from typing import Dict, Any, List
from datetime import datetime, timedelta

class StatisticalValidator:
    """
    Layer 2: Statistical Consistency Validation.
    Checks spatial clustering, temporal consistency, and outlier detection.
    """
    
    def validate(self, 
                 lat: float, 
                 lon: float, 
                 depth: float, 
                 timestamp: datetime,
                 recent_reports: pd.DataFrame, 
                 rainfall_24h: float) -> Dict[str, Any]:
        """
        Validate based on statistical patterns.
        
        Args:
            lat, lon: Report location
            depth: Reported depth (m)
            timestamp: Report time
            recent_reports: DataFrame of recent reports (cols: lat, lon, depth, timestamp)
            rainfall_24h: Accumulated rainfall in last 24h at location (mm)
            
        Returns:
            Dict with 'layer2_score' and components.
        """
        
        # 1. Spatial Consistency (Clustering)
        # Logic: Does this report fall into a cluster of other reports?
        spatial_score = self._check_spatial_clustering(lat, lon, recent_reports)
        
        # 2. Temporal Consistency
        # Logic: Is the report consistent with recent rainfall?
        temporal_score = self._check_temporal_consistency(rainfall_24h)
        
        # 3. Outlier Detection
        # Logic: Is the depth value anomalous compared to neighbors?
        outlier_score = self._check_outlier(lat, lon, depth, recent_reports)
        
        # Weighted Aggregation
        # Spatial (50%), Temporal (30%), Outlier (20%)
        layer2_score = (0.5 * spatial_score) + (0.3 * temporal_score) + (0.2 * outlier_score)
        
        return {
            'layer2_score': round(layer2_score, 3),
            'spatial_score': round(spatial_score, 3),
            'temporal_score': round(temporal_score, 3),
            'outlier_score': round(outlier_score, 3)
        }

    def _check_spatial_clustering(self, lat: float, lon: float, reports: pd.DataFrame) -> float:
        """
        Uses simple radius neighbor check (lighter than full DBSCAN for single point online validation).
        """
        if reports.empty:
            return 0.5 # Neutral if no data
            
        # Calculate Haversine distances approx (or Euclidean for small area)
        # 1 deg lat ~ 111 km. 
        # Radius 200m ~ 0.002 deg roughly
        
        # Euclidean approximation for speed
        dists = np.sqrt((reports.lat - lat)**2 + (reports.lon - lon)**2)
        
        # Threshold: 0.002 degrees (~220m)
        nearby = reports[dists < 0.002]
        count = len(nearby)
        
        if count >= 5:
            return 1.0 # Strong cluster
        elif count >= 3:
            return 0.8
        elif count >= 1:
            return 0.6
        else:
            return 0.4 # Isolated report

    def _check_temporal_consistency(self, rainfall_mm: float) -> float:
        """
        Checks if significant rainfall occurred.
        """
        if rainfall_mm > 100.0:
            return 1.0
        elif rainfall_mm > 50.0:
            return 0.8
        elif rainfall_mm > 10.0:
            return 0.6
        elif rainfall_mm > 0.0:
            return 0.4
        else:
            return 0.2 # Flood reported with 0 rain? Suspicious (unless river flood)

    def _check_outlier(self, lat: float, lon: float, depth: float, reports: pd.DataFrame) -> float:
        """
        Checks if depth is an outlier among nearby reports.
        """
        if reports.empty:
            return 0.5
            
        # Get nearby reports to compare depth
        dists = np.sqrt((reports.lat - lat)**2 + (reports.lon - lon)**2)
        nearby = reports[dists < 0.005] # ~500m
        
        if len(nearby) < 3:
            return 0.5 # Not enough data to judge outlier
            
        mean_depth = nearby.depth.mean()
        std_depth = nearby.depth.std()
        
        if std_depth == 0:
            return 1.0 if abs(depth - mean_depth) < 0.5 else 0.2
            
        z_score = abs(depth - mean_depth) / std_depth
        
        if z_score < 1.0:
            return 1.0 # Consistent
        elif z_score < 2.0:
            return 0.7
        else:
            return 0.2 # Anomalous depth
