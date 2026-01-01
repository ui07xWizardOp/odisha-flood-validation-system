"""
FloodReportValidator - ML-Enhanced 5-Layer Validation System.

Layers:
1. Physical Plausibility (Random Forest / Rule-based)
2. Statistical Consistency (DBSCAN Clustering)
3. Reputation (Bayesian Trust)
4. Social Context (NewsAPI)
5. Visual Verification (Computer Vision) - Optional

Weight aggregation uses a trained neural network instead of hardcoded values.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Core validation layers
from src.preprocessing.feature_extractor import FeatureExtractor
from src.validation.layer1_physical import PhysicalValidator
from src.validation.layer2_statistical import StatisticalValidator
from src.validation.layer3_reputation import ReputationSystem

# Zero-Cost Data Services
from src.preprocessing.weather_service import weather_service
from src.preprocessing.geospatial_service import geo_service
from src.preprocessing.social_service import social_service

# ML Models
from src.ml.models.dbscan_clustering import spatial_analyzer
from src.ml.models.weight_network import WeightLearningNetwork
from src.ml.models.image_classifier import flood_classifier

logger = logging.getLogger(__name__)


class FloodReportValidator:
    """
    Main Orchestrator for the 5-Layer ML-Enhanced Validation System.
    """
    
    VALIDATION_THRESHOLD = 0.7
    WEIGHT_MODEL_PATH = "models/weight_network.json"
    
    def __init__(self, use_ml_weights: bool = True):
        """
        Initialize the validation system.
        
        Args:
            use_ml_weights: If True, use learned weights. If False, use defaults.
        """
        print("🚀 Initializing ML-Enhanced Validation System...")
        
        # Core Feature Extraction
        self.extractor = FeatureExtractor()
        
        # Traditional Layers
        self.layer1 = PhysicalValidator()
        self.layer2_rule = StatisticalValidator()
        self.layer3 = ReputationSystem()
        
        # ML Components
        self.dbscan = spatial_analyzer
        self.weight_network = self._load_weight_network(use_ml_weights)
        self.image_classifier = flood_classifier
        
        # Report cache for DBSCAN context
        self.recent_reports_cache: List[Dict] = []
        
        print("✅ Validation System Ready")
        print(f"   Learned Weights: {self.weight_network.get_weights()}")
        
    def _load_weight_network(self, use_ml: bool) -> WeightLearningNetwork:
        """Load trained weight network or create default."""
        if use_ml and Path(self.WEIGHT_MODEL_PATH).exists():
            try:
                return WeightLearningNetwork.load(self.WEIGHT_MODEL_PATH)
            except Exception as e:
                logger.warning(f"Failed to load weight model: {e}")
        
        # Default weights (uniform)
        return WeightLearningNetwork(n_layers=4)
        
    def validate_report(self, 
                        report_id: int,
                        user_id: int, 
                        lat: float, 
                        lon: float, 
                        depth: float, 
                        timestamp: datetime,
                        recent_reports: pd.DataFrame = None,
                        rainfall_24h: float = None,
                        image_bytes: bytes = None) -> Dict[str, Any]:
        """
        Runs the full 5-layer ML-enhanced validation pipeline.
        
        Args:
            report_id: Unique report identifier
            user_id: User who submitted the report
            lat, lon: Location coordinates
            depth: Reported water depth (meters)
            timestamp: Report submission time
            recent_reports: Optional DataFrame of recent reports for context
            rainfall_24h: Optional rainfall override (fetched if None)
            image_bytes: Optional photo for CV validation
            
        Returns:
            Dict with validation result, scores, and details
        """
        
        # ==========================================
        # Step 0: Feature Extraction
        # ==========================================
        features = self.extractor.extract_all_features(lat, lon)
        
        # Fetch real-time weather if not provided
        if rainfall_24h is None:
            weather = weather_service.get_current_weather(lat, lon)
            rainfall_24h = weather.get('rainfall_mm', 0.0) if weather else 0.0
        
        # ==========================================
        # Layer 1: Physical Plausibility
        # ==========================================
        l1_result = self.layer1.validate(lat, lon, depth, features)
        l1_score = l1_result.get('layer1_score', 0.5)
        
        # Boost from official ground truth
        ground_truth = geo_service.check_ground_truth(lat, lon)
        if ground_truth.get('in_flood_zone'):
            l1_score = min(l1_score + 0.2, 1.0)
            l1_result['zone_boost'] = True
        
        # ==========================================
        # Layer 2: Statistical Consistency (DBSCAN)
        # ==========================================
        # Build report dict for DBSCAN
        current_report = {
            'report_id': report_id,
            'latitude': lat,
            'longitude': lon,
            'depth': depth,
            'timestamp': timestamp
        }
        
        # Use DBSCAN for cluster-based validation
        if recent_reports is not None and len(recent_reports) > 0:
            reports_list = recent_reports.to_dict('records')
            for r in reports_list:
                r['latitude'] = r.get('lat', r.get('latitude', 0))
                r['longitude'] = r.get('lon', r.get('longitude', 0))
        else:
            reports_list = self.recent_reports_cache.copy()
        
        dbscan_score = self.dbscan.get_cluster_score(current_report, reports_list)
        
        # Also run traditional statistical check
        l2_result_rule = self.layer2_rule.validate(
            lat, lon, depth, timestamp, 
            recent_reports if recent_reports is not None else pd.DataFrame(),
            rainfall_24h
        )
        
        # Combine DBSCAN and rule-based (weighted average)
        l2_score = 0.6 * dbscan_score + 0.4 * l2_result_rule.get('layer2_score', 0.5)
        
        l2_result = {
            'layer2_score': round(l2_score, 3),
            'dbscan_score': round(dbscan_score, 3),
            'rule_score': l2_result_rule.get('layer2_score', 0.5),
            'cluster_analysis': self.dbscan.analyze_clusters(reports_list) if reports_list else {}
        }
        
        # ==========================================
        # Layer 3: Reputation
        # ==========================================
        l3_result = self.layer3.validate(user_id)
        l3_score = l3_result.get('layer3_score', 0.5)
        
        # ==========================================
        # Layer 4: Social Context
        # ==========================================
        social_ctx = social_service.get_social_context("Odisha")
        l4_score = social_ctx.get('buzz_score', 0.0)
        
        l4_result = {
            'layer4_score': round(l4_score, 3),
            'headlines': social_ctx.get('recent_headlines', []),
            'source': social_ctx.get('source', 'None')
        }
        
        # ==========================================
        # Layer 5: Visual Verification (Optional)
        # ==========================================
        l5_result = {'layer5_score': 0.5, 'applied': False}  # Neutral if no image
        
        if image_bytes:
            cv_result = self.image_classifier.validate_image(image_bytes)
            if cv_result.get('valid'):
                l5_score = cv_result.get('score', 0.5)
                l5_result = {
                    'layer5_score': round(l5_score, 3),
                    'is_flood': cv_result.get('is_flood_detected', False),
                    'water_coverage': cv_result.get('water_coverage', 0.0),
                    'applied': True
                }
        
        # ==========================================
        # Weighted Aggregation (Neural Network)
        # ==========================================
        layer_scores = np.array([l1_score, l2_score, l3_score, l4_score])
        
        final_score = float(self.weight_network.forward(layer_scores))
        
        # Apply photo boost if strong positive signal
        if l5_result.get('applied') and l5_result.get('is_flood'):
            final_score = min(final_score + 0.1, 1.0)
        
        status = 'validated' if final_score >= self.VALIDATION_THRESHOLD else 'flagged'
        
        # Update cache for future DBSCAN context
        self.recent_reports_cache.append(current_report)
        if len(self.recent_reports_cache) > 500:
            self.recent_reports_cache = self.recent_reports_cache[-500:]
        
        return {
            'report_id': report_id,
            'status': status,
            'final_score': round(final_score, 3),
            'learned_weights': self.weight_network.get_weights(),
            'details': {
                'physical': {**l1_result, 'layer1_score': round(l1_score, 3)},
                'statistical': l2_result,
                'reputation': l3_result,
                'social': l4_result,
                'visual': l5_result,
                'features': features,
                'rainfall_24h': rainfall_24h,
                'ground_truth': ground_truth
            }
        }


if __name__ == "__main__":
    # Example Usage
    validator = FloodReportValidator(use_ml_weights=True)
    
    result = validator.validate_report(
        report_id=101,
        user_id=1,
        lat=20.4625, lon=85.8830,  # Cuttack
        depth=1.5,
        timestamp=datetime.now()
    )
    
    print("\n📊 Validation Result:")
    print(f"   Status: {result['status']}")
    print(f"   Final Score: {result['final_score']}")
    print(f"   Weights: {result['learned_weights']}")
