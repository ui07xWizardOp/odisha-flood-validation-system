"""
Active Learning Pipeline for Flood Validation System.

Enables continuous model improvement through:
- Uncertainty sampling for label selection
- Expert annotation queue for flagged reports
- Model retraining with new annotations
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ActiveLearningPipeline:
    """
    Manages the active learning loop for model improvement.
    
    Flow:
    1. Identify uncertain predictions (flagged reports)
    2. Queue for expert annotation
    3. Collect annotations
    4. Retrain models with new data
    5. Evaluate improvement
    """
    
    def __init__(self, model=None, data_dir: str = "data/active_learning"):
        self.model = model
        self.data_dir = Path(data_dir)
        self.annotation_queue = []
        self.annotations = []
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing annotations
        self._load_annotations()
    
    def _load_annotations(self):
        """Load existing annotations from disk."""
        annotations_file = self.data_dir / "annotations.json"
        if annotations_file.exists():
            with open(annotations_file) as f:
                self.annotations = json.load(f)
            logger.info(f"Loaded {len(self.annotations)} existing annotations")
    
    def _save_annotations(self):
        """Save annotations to disk."""
        annotations_file = self.data_dir / "annotations.json"
        with open(annotations_file, "w") as f:
            json.dump(self.annotations, f, indent=2)
    
    def add_to_queue(self, report_id: int, features: np.ndarray, 
                     prediction_score: float, details: Dict) -> Dict:
        """
        Add a flagged report to the annotation queue.
        
        Args:
            report_id: Database ID of the report
            features: Feature vector used for prediction
            prediction_score: Model's confidence score
            details: Additional report details
            
        Returns:
            Queue entry with priority
        """
        # Calculate uncertainty (closer to 0.5 = more uncertain)
        uncertainty = 1 - abs(prediction_score - 0.5) * 2
        
        entry = {
            "report_id": report_id,
            "features": features.tolist() if isinstance(features, np.ndarray) else features,
            "prediction_score": prediction_score,
            "uncertainty": uncertainty,
            "queued_at": datetime.now().isoformat(),
            "status": "pending",
            "priority": self._calculate_priority(uncertainty, details)
        }
        
        self.annotation_queue.append(entry)
        self._save_queue()
        
        logger.info(f"Added report {report_id} to annotation queue (priority: {entry['priority']:.2f})")
        
        return entry
    
    def _calculate_priority(self, uncertainty: float, details: Dict) -> float:
        """
        Calculate annotation priority based on multiple factors.
        Higher priority = should be annotated first.
        """
        priority = uncertainty * 0.5  # Base: uncertainty
        
        # Boost for reported depth > 1m
        if details.get("depth_meters", 0) > 1.0:
            priority += 0.2
        
        # Boost for recent reports
        # (Implementation would check timestamp)
        priority += 0.1
        
        # Boost for areas with few previous reports
        # (Implementation would check spatial density)
        priority += 0.1
        
        return min(priority, 1.0)
    
    def _save_queue(self):
        """Save annotation queue to disk."""
        queue_file = self.data_dir / "annotation_queue.json"
        with open(queue_file, "w") as f:
            json.dump(self.annotation_queue, f, indent=2)
    
    def get_pending_annotations(self, limit: int = 10) -> List[Dict]:
        """
        Get highest priority pending annotations.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of annotation queue entries
        """
        pending = [e for e in self.annotation_queue if e["status"] == "pending"]
        pending.sort(key=lambda x: x["priority"], reverse=True)
        return pending[:limit]
    
    def submit_annotation(self, report_id: int, label: str, 
                         annotator: str, notes: Optional[str] = None) -> Dict:
        """
        Submit an expert annotation for a queued report.
        
        Args:
            report_id: ID of the report being annotated
            label: "flood" or "not_flood"
            annotator: Username/ID of the annotator
            notes: Optional annotation notes
            
        Returns:
            Annotation record
        """
        # Find and update queue entry
        for entry in self.annotation_queue:
            if entry["report_id"] == report_id:
                entry["status"] = "annotated"
                entry["annotated_at"] = datetime.now().isoformat()
                break
        
        # Create annotation record
        annotation = {
            "report_id": report_id,
            "label": label,
            "annotator": annotator,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        self.annotations.append(annotation)
        self._save_annotations()
        self._save_queue()
        
        logger.info(f"Annotation submitted for report {report_id}: {label}")
        
        return annotation
    
    def get_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get annotated data for model retraining.
        
        Returns:
            Tuple of (features, labels) arrays
        """
        # Match annotations to queue entries for features
        features = []
        labels = []
        
        for annotation in self.annotations:
            report_id = annotation["report_id"]
            
            # Find corresponding queue entry
            for entry in self.annotation_queue:
                if entry["report_id"] == report_id:
                    features.append(entry["features"])
                    labels.append(1 if annotation["label"] == "flood" else 0)
                    break
        
        if not features:
            return np.array([]), np.array([])
        
        return np.array(features), np.array(labels)
    
    def should_retrain(self, min_new_annotations: int = 50) -> bool:
        """
        Determine if model should be retrained.
        
        Args:
            min_new_annotations: Minimum new annotations required
            
        Returns:
            True if retraining is recommended
        """
        new_annotations = len([
            a for a in self.annotations 
            if not a.get("used_for_training", False)
        ])
        
        return new_annotations >= min_new_annotations
    
    def mark_annotations_used(self):
        """Mark all current annotations as used for training."""
        for annotation in self.annotations:
            annotation["used_for_training"] = True
        self._save_annotations()
    
    def get_stats(self) -> Dict:
        """Get active learning pipeline statistics."""
        pending = len([e for e in self.annotation_queue if e["status"] == "pending"])
        annotated = len([e for e in self.annotation_queue if e["status"] == "annotated"])
        
        return {
            "queue_size": len(self.annotation_queue),
            "pending": pending,
            "annotated": annotated,
            "total_annotations": len(self.annotations),
            "unused_annotations": len([
                a for a in self.annotations 
                if not a.get("used_for_training", False)
            ]),
            "ready_for_retraining": self.should_retrain()
        }


# Singleton instance
active_learning = ActiveLearningPipeline()


if __name__ == "__main__":
    print("🔄 Active Learning Pipeline")
    
    # Test adding to queue
    mock_features = np.array([50.0, 3.0, 2.5, 5, 0.7, 0.6, 30.0, 0.3])
    entry = active_learning.add_to_queue(
        report_id=999,
        features=mock_features,
        prediction_score=0.55,
        details={"depth_meters": 1.5}
    )
    print(f"   Added to queue: {entry}")
    
    # Test stats
    stats = active_learning.get_stats()
    print(f"   Pipeline stats: {stats}")
