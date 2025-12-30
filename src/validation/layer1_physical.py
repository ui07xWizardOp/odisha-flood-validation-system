from typing import Dict, Any

class PhysicalValidator:
    """
    Layer 1: Physical Plausibility Validation.
    Checks if a flood report is physically plausible given the terrain.
    """
    
    # Thresholds based on domain knowledge / paper specs
    MAX_HAND_THRESHOLD_M = 10.0      # Likely safe from flood
    SUSPICIOUS_HAND_THRESHOLD_M = 5.0 # Unlikely to flood unless severe
    
    STEEP_SLOPE_DEG = 15.0  # Water doesn't stand on steep slopes
    MAX_SLOPE_DEG = 30.0   # Impossible for standing water
    
    LOCAL_HIGH_DIFF_M = 5.0 # If 5m higher than everything around 100m, unlikely to be flooded first
    
    def validate(self, lat: float, lon: float, reported_depth: float, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate based on physical terrain features.
        
        Args:
            lat, lon: Coordinates
            reported_depth: User reported flood depth (m)
            features: Dictionary from FeatureExtractor
            
        Returns:
            Dict containing 'layer1_score' (0.0 to 1.0) and component scores.
        """
        
        # 1. HAND Check: Height Above Nearest Drainage
        # Lower HAND = Higher Flood Probability -> Higher Trust Score for Positive Report
        hand = features.get('hand', 0.0)
        
        if hand > self.MAX_HAND_THRESHOLD_M:
            hand_score = 0.1 # Very unlikely to be flooded
        elif hand > self.SUSPICIOUS_HAND_THRESHOLD_M:
            hand_score = 0.4 # Suspicious
        elif hand < 1.0:
            hand_score = 1.0 # Very plausible (near river level)
        else:
            # Linear scaling between 1m and 5m
            # HAND=1 -> 1.0, HAND=5 -> 0.4
            hand_score = 1.0 - (0.15 * (hand - 1.0))
            
        # 2. Slope Check
        # Flatter slope = More likely to retain water
        slope = features.get('slope', 0.0)
        
        if slope > self.MAX_SLOPE_DEG:
            slope_score = 0.0 # Impossible
        elif slope > self.STEEP_SLOPE_DEG:
            slope_score = 0.3 # Unlikely
        else:
            # Slope 0 -> 1.0, Slope 15 -> 0.3
            slope_score = 1.0 - (0.046 * slope)
            
        # 3. Local Elevation Context Check
        # Compare point elevation to neighborhood mean
        elev_diff = features.get('elevation_diff_from_neighbors', 0.0)
        
        if elev_diff > self.LOCAL_HIGH_DIFF_M: 
            # Point is a local peak/mound
            elev_score = 0.2
        elif elev_diff < -2.0:
            # Point is a local depression (sink/lowland) -> High flood risk
            elev_score = 1.0
        else:
            # Neutral context
            elev_score = 0.8
            
        # Weighted Aggregation for Layer 1
        # Weights: HAND (40%), Elevation Context (40%), Slope (20%)
        layer1_score = (0.4 * hand_score) + (0.4 * elev_score) + (0.2 * slope_score)
        
        # Clip score
        layer1_score = max(0.0, min(1.0, layer1_score))
        
        return {
            'layer1_score': round(layer1_score, 3),
            'hand_score': round(hand_score, 3),
            'slope_score': round(slope_score, 3),
            'elevation_score': round(elev_score, 3),
            'features_used': features
        }
