"""
Random Forest model for physical plausibility validation (Layer 1).

Replaces rule-based thresholds with learned decision boundaries.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
from pathlib import Path
import json


class PhysicalPlausibilityModel:
    """Random Forest classifier for terrain-based flood validation."""
    
    def __init__(self, n_estimators: int = 200, max_depth: int = 15, random_state: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=random_state,
            n_jobs=-1,  # Use all CPU cores
            class_weight='balanced'  # Handle class imbalance
        )
        self.feature_names = ['hand', 'slope', 'elevation', 'dist_to_river', 'land_use']
        self.trained = False
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train the Random Forest model."""
        print("🌲 Training Random Forest (Physical Plausibility)...")
        self.model.fit(X_train[self.feature_names], y_train)
        self.trained = True
        
        # Feature importance
        importances = self.model.feature_importances_
        for name, importance in zip(self.feature_names, importances):
            print(f"   {name}: {importance:.3f}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict flood probability."""
        if not self.trained:
            raise ValueError("Model not trained. Call train() first.")
        return self.model.predict_proba(X[self.feature_names])[:, 1]
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary flood label."""
        return self.model.predict(X[self.feature_names])
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate model performance."""
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
        print("\n📊 Random Forest Evaluation:")
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
        """Save trained model to disk."""
        if not self.trained:
            raise ValueError("Cannot save untrained model.")
        
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model, model_path)
        print(f"✅ Model saved: {model_path}")
    
    @classmethod
    def load(cls, path: str):
        """Load trained model from disk."""
        instance = cls()
        instance.model = joblib.load(path)
        instance.trained = True
        return instance


def hyperparameter_tuning(X_train, y_train):
    """Perform grid search for optimal hyperparameters."""
    print("🔍 Running hyperparameter tuning (this may take a few minutes)...")
    
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 15, 20],
        'min_samples_split': [5, 10, 20]
    }
    
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    grid_search = GridSearchCV(
        rf, param_grid, cv=5, scoring='f1', n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train, y_train)
    
    print(f"✅ Best parameters: {grid_search.best_params_}")
    print(f"✅ Best F1-score: {grid_search.best_score_:.3f}")
    
    return grid_search.best_params_


def train_random_forest(data_path: str, output_path: str, tune: bool = False):
    """Main training pipeline."""
    
    # Load data
    print(f"📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    X = df.drop('is_flood', axis=1)
    y = df['is_flood']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📊 Training set: {len(X_train)} samples ({y_train.sum()} floods)")
    print(f"📊 Test set: {len(X_test)} samples ({y_test.sum()} floods)")
    
    # Hyperparameter tuning (optional)
    if tune:
        best_params = hyperparameter_tuning(X_train, y_train)
        model = PhysicalPlausibilityModel(**best_params)
    else:
        model = PhysicalPlausibilityModel()
    
    # Train
    model.train(X_train, y_train)
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Save model
    model.save(output_path)
    
    # Save metrics
    metrics_path = Path(output_path).parent / "rf_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n✅ Training complete! Model saved to {output_path}")
    return model


if __name__ == "__main__":
    # Example usage
    data_path = "data/ml_training/physical_features.csv"
    output_path = "models/rf_physical_plausibility.pkl"
    
    train_random_forest(data_path, output_path, tune=False)
