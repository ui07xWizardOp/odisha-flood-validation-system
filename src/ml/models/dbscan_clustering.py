"""
DBSCAN Clustering for Layer 2 Statistical Validation.

Replaces fixed-radius neighbor counting with density-based clustering
to identify genuine flood report clusters vs isolated noise.
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SpatialClusterAnalyzer:
    """
    Uses DBSCAN to identify clusters of flood reports.
    Reports in the same cluster are more likely to be genuine.
    """
    
    def __init__(self, eps_km: float = 2.0, min_samples: int = 3):
        """
        Args:
            eps_km: Maximum distance (km) between points in same cluster
            min_samples: Minimum points to form a dense region
        """
        # Convert km to approximate degrees (1 degree ≈ 111 km)
        self.eps_degrees = eps_km / 111.0
        self.min_samples = min_samples
        self.scaler = StandardScaler()
        
    def fit_predict(self, reports: List[Dict]) -> np.ndarray:
        """
        Cluster reports based on spatial proximity.
        
        Args:
            reports: List of report dicts with 'latitude', 'longitude'
            
        Returns:
            Array of cluster labels (-1 = noise/outlier)
        """
        if len(reports) < self.min_samples:
            return np.array([-1] * len(reports))
        
        # Extract coordinates
        coords = np.array([[r['latitude'], r['longitude']] for r in reports])
        
        # DBSCAN clustering
        dbscan = DBSCAN(
            eps=self.eps_degrees,
            min_samples=self.min_samples,
            metric='haversine'  # Spherical distance
        )
        
        # Convert to radians for haversine
        coords_rad = np.radians(coords)
        labels = dbscan.fit_predict(coords_rad)
        
        return labels
    
    def get_cluster_score(self, report: Dict, all_reports: List[Dict]) -> float:
        """
        Calculate validation score based on cluster membership.
        
        Returns:
            Score between 0.0 (isolated/noise) and 1.0 (dense cluster)
        """
        if len(all_reports) < 2:
            return 0.5  # Neutral if no context
            
        # Find report index
        report_idx = None
        for i, r in enumerate(all_reports):
            if r.get('report_id') == report.get('report_id'):
                report_idx = i
                break
        
        if report_idx is None:
            # Report not in list, add it temporarily
            all_reports_with_new = all_reports + [report]
            labels = self.fit_predict(all_reports_with_new)
            label = labels[-1]
        else:
            labels = self.fit_predict(all_reports)
            label = labels[report_idx]
        
        # Noise points get low score
        if label == -1:
            return 0.2
        
        # Count cluster size
        cluster_size = np.sum(labels == label)
        
        # Score based on cluster density
        if cluster_size >= 10:
            return 1.0
        elif cluster_size >= 5:
            return 0.85
        elif cluster_size >= 3:
            return 0.7
        else:
            return 0.5
    
    def analyze_clusters(self, reports: List[Dict]) -> Dict:
        """
        Get cluster statistics for all reports.
        """
        if not reports:
            return {"n_clusters": 0, "n_noise": 0, "clusters": []}
            
        labels = self.fit_predict(reports)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        clusters = []
        for cluster_id in set(labels):
            if cluster_id == -1:
                continue
            cluster_reports = [r for r, l in zip(reports, labels) if l == cluster_id]
            clusters.append({
                "cluster_id": int(cluster_id),
                "size": len(cluster_reports),
                "center": {
                    "lat": np.mean([r['latitude'] for r in cluster_reports]),
                    "lon": np.mean([r['longitude'] for r in cluster_reports])
                }
            })
        
        return {
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "clusters": clusters
        }


# Singleton instance
spatial_analyzer = SpatialClusterAnalyzer(eps_km=2.0, min_samples=3)


if __name__ == "__main__":
    # Test with sample data
    test_reports = [
        {"report_id": 1, "latitude": 20.46, "longitude": 85.88},
        {"report_id": 2, "latitude": 20.47, "longitude": 85.89},
        {"report_id": 3, "latitude": 20.45, "longitude": 85.87},
        {"report_id": 4, "latitude": 20.46, "longitude": 85.88},
        {"report_id": 5, "latitude": 21.50, "longitude": 86.50},  # Outlier
    ]
    
    analyzer = SpatialClusterAnalyzer()
    result = analyzer.analyze_clusters(test_reports)
    print(f"Clusters found: {result['n_clusters']}")
    print(f"Noise points: {result['n_noise']}")
    
    # Test score for a report
    score = analyzer.get_cluster_score(test_reports[0], test_reports)
    print(f"Cluster score for report 1: {score}")
