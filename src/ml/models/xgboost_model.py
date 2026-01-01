"""
XGBoost model for statistical consensus validation (Layer 2).

Analyzes spatial clustering, temporal patterns, and social features.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import json
from pathlib import Path


class StatisticalConsensusModel:
    """XGBoost classifier for statistical validation."""
    
    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1, 
                 max_depth: int = 6, random_state: int = 42):
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            eval_metric='logloss'
        )
        self.feature_names = [
            'neighbor_count', 'median_neighbor_depth', 'depth_variance',
            'rainfall_24h', 'rainfall_48h', 'user_trust_score'
        ]
        self.trained = False
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, 
              X_val: pd.DataFrame = None, y_val: pd.Series = None):
        """Train XGBoost with optional early stopping."""
        print("⚡ Training XGBoost (Statistical Consensus)...")
        
        # Simplified training
        self.model.fit(
            X_train[self.feature_names], y_train,
            verbose=False
        )
        self.trained = True
        
        # Feature importance
        importances = self.model.feature_importances_
        for name, importance in zip(self.feature_names, importances):
            print(f"   {name}: {importance:.3f}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict flood probability."""
        if not self.trained:
            raise ValueError("Model not trained.")
        return self.model.predict_proba(X[self.feature_names])[:, 1]
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary flood label."""
        return self.model.predict(X[self.feature_names])
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate model performance."""
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
        print("\n📊 XGBoost Evaluation:")
        print(classification_report(y_test, y_pred, target_names=['No Flood', 'Flood']))
        
        cm = confusion_matrix(y_test, y_pred)
        print(f"Confusion Matrix:\n{cm}")
        
        auc = roc_auc_score(y_test, y_proba)
        print(f"ROC-AUC: {auc:.3f}")
        
        return {
            'confusion_matrix': cm.tolist(),
            'roc_auc': auc,
            'feature_importances': dict(zip(self.feature_names, self.model.feature_importances_.tolist()))
        }
    
    def save(self, path: str):
        """Save model to JSON format."""
        if not self.trained:
            raise ValueError("Cannot save untrained model.")
        
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.model.save_model(model_path)
        print(f"✅ Model saved: {model_path}")
    
    @classmethod
    def load(cls, path: str):
        """Load trained model."""
        instance = cls()
        instance.model = xgb.XGBClassifier()
        instance.model.load_model(path)
        instance.trained = True
        return instance


def train_xgboost(data_path: str, output_path: str):
    """Main training pipeline for XGBoost."""
    
    # Load data
    print(f"📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    X = df.drop('is_flood', axis=1)
    y = df['is_flood']
    
    # Train/val/test split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp
    )
    
    print(f"📊 Training set: {len(X_train)} samples")
    print(f"📊 Validation set: {len(X_val)} samples")
    print(f"📊 Test set: {len(X_test)} samples")
    
    # Train
    model = StatisticalConsensusModel()
    model.train(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Save
    model.save(output_path)
    
    # Save metrics
    metrics_path = Path(output_path).parent / "xgb_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n✅ Training complete! Model saved to {output_path}")
    return model


if __name__ == "__main__":
    data_path = "data/ml_training/statistical_features.csv"
    output_path = "models/xgb_statistical_consensus.json"
    
    train_xgboost(data_path, output_path)
