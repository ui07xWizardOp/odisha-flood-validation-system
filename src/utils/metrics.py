import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, accuracy_score
from shapely.geometry import Point
from shapely.ops import unary_union
from typing import Dict, Any

class ValidationMetrics:
    """
    Calculates classification and spatial metrics for validation experiments.
    """
    
    @staticmethod
    def calculate_classification_metrics(y_true: np.ndarray, 
                                         y_pred: np.ndarray, 
                                         y_scores: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate standard classification metrics.
        
        Args:
            y_true: Ground truth labels (1=flood, 0=no flood)
            y_pred: Predicted labels
            y_scores: Continuous prediction scores for AUC
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0)
        }
        
        # Specificity: TN / (TN + FP)
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        # AUC (if scores available)
        if y_scores is not None and len(np.unique(y_true)) > 1:
            try:
                metrics['auc'] = roc_auc_score(y_true, y_scores)
            except:
                metrics['auc'] = 0.5
        else:
            metrics['auc'] = 0.5
            
        return metrics

    @staticmethod
    def calculate_iou(validated_reports: pd.DataFrame, 
                      ground_truth_polygon,
                      buffer_deg: float = 0.01) -> float:
        """
        Calculate Intersection over Union between predicted flood extent
        and ground truth polygon.
        
        Args:
            validated_reports: DataFrame with lat/lon of validated flood reports
            ground_truth_polygon: Shapely Polygon of actual flood
            buffer_deg: Buffer around each point (degrees, ~1km)
        """
        if len(validated_reports) == 0:
            return 0.0
            
        # Create predicted polygon from buffered points
        points = [Point(row['longitude'], row['latitude']).buffer(buffer_deg) 
                  for _, row in validated_reports.iterrows()]
        
        if not points:
            return 0.0
            
        predicted_polygon = unary_union(points)
        
        # Calculate IoU
        intersection = predicted_polygon.intersection(ground_truth_polygon).area
        union = predicted_polygon.union(ground_truth_polygon).area
        
        if union == 0:
            return 0.0
            
        return intersection / union

    @staticmethod
    def calculate_depth_error(predicted_depths: np.ndarray, 
                              true_depths: np.ndarray) -> Dict[str, float]:
        """
        Calculate depth estimation error metrics.
        """
        errors = np.abs(predicted_depths - true_depths)
        return {
            'mae': np.mean(errors),
            'rmse': np.sqrt(np.mean(errors ** 2)),
            'max_error': np.max(errors)
        }
