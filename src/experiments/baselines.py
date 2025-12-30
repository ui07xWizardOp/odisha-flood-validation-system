import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List

class NoValidationBaseline:
    """
    Baseline 1: Accept all reports without any validation.
    This represents what happens without a validation system.
    """
    
    def validate_batch(self, reports: pd.DataFrame) -> pd.DataFrame:
        reports = reports.copy()
        reports['predicted_valid'] = True
        reports['validation_score'] = 1.0
        reports['method'] = 'no_validation'
        return reports


class RandomBaseline:
    """
    Baseline 2: Random validation (sanity check).
    Randomly accepts 70% of reports.
    """
    
    def __init__(self, accept_rate: float = 0.7, seed: int = 42):
        self.accept_rate = accept_rate
        np.random.seed(seed)
    
    def validate_batch(self, reports: pd.DataFrame) -> pd.DataFrame:
        reports = reports.copy()
        reports['validation_score'] = np.random.uniform(0, 1, len(reports))
        reports['predicted_valid'] = reports['validation_score'] >= (1 - self.accept_rate)
        reports['method'] = 'random'
        return reports


class DEMOnlyBaseline:
    """
    Baseline 3: DEM/Physical layer only (no consensus or reputation).
    Uses only elevation-based heuristics.
    """
    
    # Simple heuristic thresholds (would need real DEM in production)
    ELEVATION_THRESHOLD = 50  # Locations above 50m unlikely to flood
    
    def __init__(self, feature_extractor=None):
        self.feature_extractor = feature_extractor
    
    def validate_batch(self, reports: pd.DataFrame) -> pd.DataFrame:
        reports = reports.copy()
        scores = []
        
        for _, row in reports.iterrows():
            if self.feature_extractor:
                features = self.feature_extractor.extract_all_features(row['latitude'], row['longitude'])
                # Lower elevation = more plausible
                # HAND < 5 = plausible, HAND > 10 = implausible
                hand = features.get('hand', 5.0)
                if hand < 5:
                    score = 0.9
                elif hand < 10:
                    score = 0.6
                else:
                    score = 0.2
            else:
                # Mock scoring based on latitude (just for testing without rasters)
                # Northern parts of study area (higher lat) tend to be higher elevation
                normalized_lat = (row['latitude'] - 19.5) / 2.0  # 0-1 scale
                score = 1.0 - (normalized_lat * 0.5)  # Higher lat -> lower score
                
            scores.append(score)
        
        reports['validation_score'] = scores
        reports['predicted_valid'] = reports['validation_score'] >= 0.7
        reports['method'] = 'dem_only'
        return reports


class PureMLBaseline:
    """
    Baseline 4: Pure ML approach (Isolation Forest).
    Uses only statistical anomaly detection without domain knowledge.
    """
    
    def __init__(self, contamination: float = 0.15):
        self.contamination = contamination
        self.model = IsolationForest(contamination=contamination, random_state=42)
    
    def validate_batch(self, reports: pd.DataFrame) -> pd.DataFrame:
        reports = reports.copy()
        
        # Features for Isolation Forest
        features = reports[['latitude', 'longitude', 'depth_meters']].values
        
        # Fit and predict
        self.model.fit(features)
        predictions = self.model.predict(features)  # 1 = normal, -1 = anomaly
        scores = self.model.decision_function(features)  # Raw scores
        
        # Normalize scores to 0-1
        min_s, max_s = scores.min(), scores.max()
        if max_s - min_s > 0:
            normalized_scores = (scores - min_s) / (max_s - min_s)
        else:
            normalized_scores = np.ones_like(scores) * 0.5
            
        reports['validation_score'] = normalized_scores
        reports['predicted_valid'] = predictions == 1
        reports['method'] = 'pure_ml'
        return reports


def get_baseline_validator(method_name: str):
    """Factory function to get baseline by name."""
    methods = {
        'no_validation': NoValidationBaseline,
        'random': RandomBaseline,
        'dem_only': DEMOnlyBaseline,
        'pure_ml': PureMLBaseline
    }
    if method_name not in methods:
        raise ValueError(f"Unknown method: {method_name}. Available: {list(methods.keys())}")
    return methods[method_name]()
