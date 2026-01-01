"""
Unified evaluation script for ML models vs Rule-Based Baseline.

Compares:
1. Layer 1: Random Forest (Physical) vs Rule-Based Layer 1
2. Layer 2: XGBoost (Statistical) vs Rule-Based Layer 2
3. Layer 3: Reputation (Not ML yet) vs Rule-Based Layer 3
4. Final: LightGBM Ensemble vs Weighted Average Rule
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import classification_report, f1_score, accuracy_score

# Load ML Models
from src.ml.models.random_forest import PhysicalPlausibilityModel
from src.ml.models.xgboost_model import StatisticalConsensusModel
from src.ml.models.lightgbm_ensemble import EnsembleValidator

def evaluate_physical_layer():
    print("\n🏔️ EVALUATING LAYER 1: PHYSICAL PLAUSIBILITY")
    print("-" * 50)
    
    # Load test data
    df = pd.read_csv("data/ml_training/physical_features.csv")
    X = df.drop('is_flood', axis=1)
    y_true = df['is_flood']
    
    # 1. ML Model (Random Forest)
    try:
        rf_model = PhysicalPlausibilityModel.load("models/rf_physical_plausibility.pkl")
        y_pred_ml = rf_model.predict(X)
        f1_ml = f1_score(y_true, y_pred_ml)
        print(f"Random Forest F1: {f1_ml:.4f}")
    except Exception as e:
        print(f"ML Model Failed: {e}")
        f1_ml = 0

    # 2. Rule-Based (Heuristic)
    # Rule: IF HAND < 10m AND Slope < 30 deg -> Valid
    y_pred_rule = []
    for _, row in X.iterrows():
        is_valid = (row['hand'] < 10) and (row['slope'] < 30)
        y_pred_rule.append(is_valid)
    
    f1_rule = f1_score(y_true, y_pred_rule)
    print(f"Rule-Based F1:    {f1_rule:.4f}")
    print(f"Improvement:      {f1_ml - f1_rule:+.4f}")


def evaluate_statistical_layer():
    print("\n📊 EVALUATING LAYER 2: STATISTICAL CONSENSUS")
    print("-" * 50)
    
    df = pd.read_csv("data/ml_training/statistical_features.csv")
    X = df.drop('is_flood', axis=1)
    y_true = df['is_flood']
    
    # 1. ML Model (XGBoost)
    try:
        xgb_model = StatisticalConsensusModel.load("models/xgb_statistical_consensus.json")
        y_pred_ml = xgb_model.predict(X)
        f1_ml = f1_score(y_true, y_pred_ml)
        print(f"XGBoost F1:       {f1_ml:.4f}")
    except Exception as e:
        print(f"ML Model Failed: {e}")
        f1_ml = 0

    # 2. Rule-Based
    # Rule: IF neighbor_count >= 3 OR rainfall_24h > 50 -> Valid
    y_pred_rule = []
    for _, row in X.iterrows():
        is_valid = (row['neighbor_count'] >= 3) or (row['rainfall_24h'] > 50)
        y_pred_rule.append(is_valid)
        
    f1_rule = f1_score(y_true, y_pred_rule)
    print(f"Rule-Based F1:    {f1_rule:.4f}")
    print(f"Improvement:      {f1_ml - f1_rule:+.4f}")


def evaluate_final_ensemble():
    print("\n🧠 EVALUATING FINAL DECISION: ENSEMBLE vs WEIGHTED AVG")
    print("-" * 50)
    
    df = pd.read_csv("data/ml_training/ensemble_features.csv")
    X = df.drop('is_flood', axis=1)
    y_true = df['is_flood']
    
    # 1. ML Model (LightGBM)
    try:
        lgb_model = EnsembleValidator.load("models/lgb_ensemble.txt")
        y_pred_ml = lgb_model.predict(X)
        f1_ml = f1_score(y_true, y_pred_ml)
        print(f"LightGBM F1:      {f1_ml:.4f}")
    except Exception as e:
        print(f"ML Model Failed: {e}")
        f1_ml = 0
        
    # 2. Rule-Based (Weighted Average)
    # Score = 0.4*Phys + 0.4*Stat + 0.2*Rep
    # Threshold = 0.6
    y_pred_rule = []
    for _, row in X.iterrows():
        score = (0.4 * row['physical_score']) + \
                (0.4 * row['consensus_score']) + \
                (0.2 * row['reputation_score'])
        y_pred_rule.append(score >= 0.6)
        
    f1_rule = f1_score(y_true, y_pred_rule)
    print(f"Weighted Avg F1:  {f1_rule:.4f}")
    print(f"Improvement:      {f1_ml - f1_rule:+.4f}")


if __name__ == "__main__":
    evaluate_physical_layer()
    evaluate_statistical_layer()
    evaluate_final_ensemble()
