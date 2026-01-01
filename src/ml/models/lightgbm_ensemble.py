"""
LightGBM ensemble model - combines outputs from all validation layers.

This is the final decision-making model that weighs:
- Layer 1 (Physical): Random Forest score
- Layer 2 (Statistical): XGBoost score  
- Layer 3 (Temporal): LSTM score (or hardcoded for now)
- Layer 4 (Reputation): User trust score
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import json
from pathlib import Path


class EnsembleValidator:
    """LightGBM meta-learner for final validation decision."""
    
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.05, 
                 max_depth: int = 5, random_state: int = 42):
        self.model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            verbose=-1
        )
        self.feature_names = [
            'physical_score', 'consensus_score', 
            'temporal_score', 'reputation_score'
        ]
        self.trained = False
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train the ensemble model."""
        print("💡 Training LightGBM Ensemble...")
        self.model.fit(X_train[self.feature_names], y_train)
        self.trained = True
        
        # Feature importance
        importances = self.model.feature_importances_
        for name, importance in zip(self.feature_names, importances):
            print(f"   {name}: {importance:.3f}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict final validation probability."""
        if not self.trained:
            raise ValueError("Model not trained.")
        return self.model.predict_proba(X[self.feature_names])[:, 1]
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary validation decision."""
        return self.model.predict(X[self.feature_names])
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate ensemble performance."""
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
        print("\n📊 LightGBM Ensemble Evaluation:")
        print(classification_report(y_test, y_pred, target_names=['Invalid', 'Valid']))
        
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
        """Save model to text format."""
        if not self.trained:
            raise ValueError("Cannot save untrained model.")
        
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.model.booster_.save_model(model_path)
        print(f"✅ Model saved: {model_path}")
    
    @classmethod
    def load(cls, path: str):
        """Load trained model."""
        instance = cls()
        instance.model = lgb.Booster(model_file=path)
        instance.trained = True
        return instance


def train_ensemble(data_path: str, output_path: str):
    """Main training pipeline for ensemble model."""
    
    # Load data
    print(f"📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    X = df.drop('is_flood', axis=1)
    y = df['is_flood']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Training set: {len(X_train)} samples ({y_train.sum()} valid)")
    print(f"📊 Test set: {len(X_test)} samples ({y_test.sum()} valid)")
    
    # Train
    model = EnsembleValidator()
    model.train(X_train, y_train)
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Save
    model.save(output_path)
    
    # Save metrics
    metrics_path = Path(output_path).parent / "lgb_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n✅ Training complete! Model saved to {output_path}")
    return model


if __name__ == "__main__":
    data_path = "data/ml_training/ensemble_features.csv"
    output_path = "models/lgb_ensemble.txt"
    
    train_ensemble(data_path, output_path)
