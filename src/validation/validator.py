from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from src.preprocessing.feature_extractor import FeatureExtractor
from src.validation.layer1_physical import PhysicalValidator
from src.validation.layer2_statistical import StatisticalValidator
from src.validation.layer3_reputation import ReputationSystem

class FloodReportValidator:
    """
    Main Orchestrator for the 3-Layer Validation System.
    """
    
    VALIDATION_THRESHOLD = 0.7
    
    def __init__(self):
        print("Initializing Validation System...")
        self.extractor = FeatureExtractor()
        self.layer1 = PhysicalValidator()
        self.layer2 = StatisticalValidator()
        self.layer3 = ReputationSystem()
        
    def validate_report(self, 
                        report_id: int,
                        user_id: int, 
                        lat: float, 
                        lon: float, 
                        depth: float, 
                        timestamp: datetime,
                        recent_reports: pd.DataFrame = pd.DataFrame(),
                        rainfall_24h: float = 0.0) -> Dict[str, Any]:
        """
        Runs the full validation pipeline for a single report.
        """
        
        # Step 0: Extract Geospatial Features
        features = self.extractor.extract_all_features(lat, lon)
        
        # Step 1: Physical Plausibility (Layer 1)
        l1_result = self.layer1.validate(lat, lon, depth, features)
        
        # Step 2: Statistical Consistency (Layer 2)
        l2_result = self.layer2.validate(lat, lon, depth, timestamp, recent_reports, rainfall_24h)
        
        # Step 3: Reputation (Layer 3)
        l3_result = self.layer3.validate(user_id)
        
        # Step 4: Weighted Aggregation
        # Weights: L1=0.4, L2=0.4, L3=0.2
        final_score = (
            0.4 * l1_result['layer1_score'] +
            0.4 * l2_result['layer2_score'] +
            0.2 * l3_result['layer3_score']
        )
        
        status = 'validated' if final_score >= self.VALIDATION_THRESHOLD else 'flagged'
        
        return {
            'report_id': report_id,
            'status': status,
            'final_score': round(final_score, 3),
            'details': {
                'physical': l1_result,
                'statistical': l2_result,
                'reputation': l3_result,
                'features': features
            }
        }

if __name__ == "__main__":
    # Example Usage
    validator = FloodReportValidator()
    result = validator.validate_report(
        report_id=101,
        user_id=1,
        lat=20.4625, lon=85.8830, # Cuttack
        depth=1.5,
        timestamp=datetime.now()
    )
    print(result)
