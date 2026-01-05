"""
Explainable AI (XAI) Module for Flood Validation System.

Uses SHAP (SHapley Additive exPlanations) to explain model predictions.
Provides transparency into why reports are validated/rejected.
"""

import numpy as np
from typing import Dict, Optional, List
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available. Install with: pip install shap")

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ValidationExplainer:
    """
    Explains validation decisions using SHAP values.
    Provides feature importance and per-prediction explanations.
    """
    
    FEATURE_NAMES = [
        "elevation",
        "hand_index",
        "slope",
        "neighbor_count",
        "cluster_density",
        "user_trust_score",
        "rainfall_24h",
        "water_ratio"
    ]
    
    def __init__(self, model=None):
        self.model = model
        self.explainer = None
        
        if SHAP_AVAILABLE and model is not None:
            self._setup_explainer()
    
    def _setup_explainer(self):
        """Initialize SHAP explainer for the model."""
        try:
            if hasattr(self.model, 'predict_proba'):
                # Tree-based model (RF, XGBoost, LightGBM)
                self.explainer = shap.TreeExplainer(self.model)
            else:
                # Fallback to KernelExplainer for other models
                self.explainer = None
            logger.info("SHAP explainer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None
    
    def explain_prediction(self, features: np.ndarray) -> Dict:
        """
        Explain a single prediction using SHAP values.
        
        Args:
            features: 1D or 2D numpy array of feature values
            
        Returns:
            Dict with SHAP values and feature importance
        """
        if not SHAP_AVAILABLE:
            return self._mock_explanation(features)
        
        if self.explainer is None:
            return self._mock_explanation(features)
        
        try:
            # Ensure 2D
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Get SHAP values
            shap_values = self.explainer.shap_values(features)
            
            # Handle binary classification
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Positive class
            
            # Create explanation
            feature_impacts = []
            for i, (name, value, shap_val) in enumerate(
                zip(self.FEATURE_NAMES, features[0], shap_values[0])
            ):
                feature_impacts.append({
                    "feature": name,
                    "value": float(value),
                    "impact": float(shap_val),
                    "direction": "positive" if shap_val > 0 else "negative"
                })
            
            # Sort by absolute impact
            feature_impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
            
            return {
                "base_value": float(self.explainer.expected_value[1]) if isinstance(
                    self.explainer.expected_value, np.ndarray
                ) else float(self.explainer.expected_value),
                "feature_impacts": feature_impacts,
                "top_factors": self._summarize_factors(feature_impacts),
                "shap_available": True
            }
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._mock_explanation(features)
    
    def _mock_explanation(self, features: np.ndarray) -> Dict:
        """Provide a rule-based explanation when SHAP unavailable."""
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        explanations = []
        
        # Rule-based explanations
        if len(features[0]) >= 2:
            hand = features[0][1] if len(features[0]) > 1 else 5.0
            slope = features[0][2] if len(features[0]) > 2 else 10.0
            
            if hand < 5:
                explanations.append({
                    "feature": "hand_index",
                    "value": float(hand),
                    "impact": 0.3,
                    "direction": "positive",
                    "reason": "Low HAND index indicates flood-prone area"
                })
            
            if slope < 10:
                explanations.append({
                    "feature": "slope",
                    "value": float(slope),
                    "impact": 0.2,
                    "direction": "positive",
                    "reason": "Flat terrain allows water accumulation"
                })
        
        return {
            "base_value": 0.5,
            "feature_impacts": explanations,
            "top_factors": ["Rule-based explanation (SHAP not available)"],
            "shap_available": False
        }
    
    def _summarize_factors(self, impacts: List[Dict]) -> List[str]:
        """Generate human-readable summary of top factors."""
        summaries = []
        
        for impact in impacts[:3]:  # Top 3
            direction = "increases" if impact["direction"] == "positive" else "decreases"
            feature = impact["feature"].replace("_", " ").title()
            summaries.append(f"{feature} {direction} validation likelihood")
        
        return summaries
    
    def get_feature_importance(self, X: np.ndarray) -> Dict:
        """
        Get global feature importance from SHAP values.
        
        Args:
            X: Training data (n_samples, n_features)
            
        Returns:
            Dict with feature importance scores
        """
        if not SHAP_AVAILABLE or self.explainer is None:
            # Return fixed importance from model if available
            return self._default_importance()
        
        try:
            shap_values = self.explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            importance = np.abs(shap_values).mean(axis=0)
            
            return {
                name: float(imp) 
                for name, imp in zip(self.FEATURE_NAMES, importance)
            }
            
        except Exception as e:
            logger.error(f"Feature importance calculation failed: {e}")
            return self._default_importance()
    
    def _default_importance(self) -> Dict:
        """Default feature importance (domain knowledge based)."""
        return {
            "hand_index": 0.25,
            "slope": 0.20,
            "elevation": 0.15,
            "neighbor_count": 0.15,
            "user_trust_score": 0.10,
            "rainfall_24h": 0.08,
            "cluster_density": 0.05,
            "water_ratio": 0.02
        }
    
    def save_plot(self, features: np.ndarray, output_path: str) -> bool:
        """
        Generate and save SHAP waterfall plot.
        
        Args:
            features: Feature values for one prediction
            output_path: Path to save the plot
            
        Returns:
            True if plot saved successfully
        """
        if not SHAP_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            logger.warning("SHAP or matplotlib not available for plotting")
            return False
        
        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            shap_values = self.explainer(features)
            
            plt.figure(figsize=(10, 6))
            shap.waterfall_plot(shap_values[0], show=False)
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"SHAP plot saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save SHAP plot: {e}")
            return False


# Singleton instance
validation_explainer = ValidationExplainer()


if __name__ == "__main__":
    print("🔍 XAI Explainer Module")
    print(f"   SHAP available: {SHAP_AVAILABLE}")
    print(f"   Matplotlib available: {MATPLOTLIB_AVAILABLE}")
    
    # Test with mock features
    mock_features = np.array([50.0, 3.0, 2.5, 5, 0.7, 0.6, 30.0, 0.3])
    explanation = validation_explainer.explain_prediction(mock_features)
    print(f"   Mock explanation: {json.dumps(explanation, indent=2)}")
