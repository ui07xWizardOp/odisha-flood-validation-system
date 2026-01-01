"""
Training data generator for ML models.

Generates labeled datasets with:
- Physical features (HAND, slope, elevation)
- Statistical features (neighbor count, depth variance)
- Temporal features (rainfall, river levels)
- Ground truth labels
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

class MLTrainingDataGenerator:
    """Generate training data for ML models."""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.output_dir = Path("data/ml_training")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_physical_features(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate synthetic physical features for training Random Forest.
        
        Features:
        - hand: Height Above Nearest Drainage (meters)
        - slope: Terrain slope (degrees)
        - elevation: Absolute elevation (meters)
        - dist_to_river: Distance to nearest river (km)
        - land_use: Categorical (0=urban, 1=forest, 2=agriculture, 3=water)
        """
        data = []
        
        for i in range(n_samples):
            # Generate true positives (actual floods)
            if i < n_samples * 0.6:  # 60% true floods
                hand = np.random.gamma(2, 1.5)  # Low HAND (0-5m typical)
                slope = np.random.gamma(1.5, 2)  # Low slope
                elevation = np.random.uniform(0, 20)
                dist_to_river = np.random.exponential(0.5)  # Close to river
                land_use = np.random.choice([0, 2, 3], p=[0.3, 0.5, 0.2])  # Urban/agri/water
                is_flood = True
                
            # Generate true negatives (no flood)
            else:
                hand = np.random.uniform(5, 30)  # High HAND
                slope = np.random.uniform(5, 45)  # Steep
                elevation = np.random.uniform(20, 100)
                dist_to_river = np.random.uniform(2, 15)
                land_use = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
                is_flood = False
            
            data.append({
                'hand': hand,
                'slope': slope,
                'elevation': elevation,
                'dist_to_river': dist_to_river,
                'land_use': land_use,
                'is_flood': is_flood
            })
        
        df = pd.DataFrame(data)
        return df
    
    def generate_statistical_features(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate features for XGBoost statistical consensus model.
        
        Features:
        - neighbor_count: Number of reports within 5km
        - median_neighbor_depth: Median depth of neighbors
        - depth_variance: Variance of neighbor depths
        - rainfall_24h: Rainfall in last 24 hours (mm)
        - rainfall_48h: Rainfall in last 48 hours (mm)
        - user_trust_score: User reputation (0-1)
        """
        data = []
        
        for i in range(n_samples):
            # True positives
            if i < n_samples * 0.6:
                neighbor_count = np.random.poisson(8)  # High clustering
                median_neighbor_depth = np.random.gamma(2, 0.5)
                depth_variance = np.random.gamma(1, 0.2)
                rainfall_24h = np.random.gamma(5, 20)  # Heavy rain
                rainfall_48h = np.random.gamma(8, 25)
                user_trust_score = np.random.beta(8, 2)  # Reliable users
                is_flood = True
            
            # True negatives
            else:
                neighbor_count = np.random.poisson(2)  # Isolated reports
                median_neighbor_depth = np.random.uniform(0, 0.3)
                depth_variance = np.random.uniform(0, 0.1)
                rainfall_24h = np.random.gamma(2, 5)  # Low rain
                rainfall_48h = np.random.gamma(3, 8)
                user_trust_score = np.random.beta(2, 8)  # Unreliable
                is_flood = False
            
            data.append({
                'neighbor_count': neighbor_count,
                'median_neighbor_depth': median_neighbor_depth,
                'depth_variance': depth_variance,
                'rainfall_24h': rainfall_24h,
                'rainfall_48h': rainfall_48h,
                'user_trust_score': user_trust_score,
                'is_flood': is_flood
            })
        
        df = pd.DataFrame(data)
        return df
    
    def generate_ensemble_features(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate features for LightGBM ensemble.
        
        Features are outputs from Layer 1 (RF) and Layer 2 (XGB) models.
        """
        data = []
        
        for i in range(n_samples):
            if i < n_samples * 0.6:
                # True floods - high scores from all layers
                physical_score = np.random.beta(8, 2)
                consensus_score = np.random.beta(7, 2)
                temporal_score = np.random.beta(6, 3)
                reputation_score = np.random.beta(7, 2)
                is_flood = True
            else:
                # False - low scores
                physical_score = np.random.beta(2, 8)
                consensus_score = np.random.beta(2, 7)
                temporal_score = np.random.beta(3, 6)
                reputation_score = np.random.beta(2, 7)
                is_flood = False
            
            data.append({
                'physical_score': physical_score,
                'consensus_score': consensus_score,
                'temporal_score': temporal_score,
                'reputation_score': reputation_score,
                'is_flood': is_flood
            })
        
        df = pd.DataFrame(data)
        return df
    
    def generate_all(self, n_samples: int = 5000):
        """Generate all training datasets and save to CSV."""
        
        print(f"🔄 Generating {n_samples} training samples...")
        
        # Physical features for Random Forest
        physical_df = self.generate_physical_features(n_samples)
        physical_path = self.output_dir / "physical_features.csv"
        physical_df.to_csv(physical_path, index=False)
        print(f"✅ Saved physical features: {physical_path}")
        
        # Statistical features for XGBoost
        statistical_df = self.generate_statistical_features(n_samples)
        statistical_path = self.output_dir / "statistical_features.csv"
        statistical_df.to_csv(statistical_path, index=False)
        print(f"✅ Saved statistical features: {statistical_path}")
        
        # Ensemble features for LightGBM
        ensemble_df = self.generate_ensemble_features(n_samples)
        ensemble_path = self.output_dir / "ensemble_features.csv"
        ensemble_df.to_csv(ensemble_path, index=False)
        print(f"✅ Saved ensemble features: {ensemble_path}")
        
        # Save metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'n_samples': n_samples,
            'train_test_split': 0.8,
            'random_seed': 42
        }
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n📊 Dataset statistics:")
        print(f"   Physical features: {physical_df['is_flood'].sum()} floods / {len(physical_df)} total")
        print(f"   Statistical features: {statistical_df['is_flood'].sum()} floods / {len(statistical_df)} total")
        print(f"   Ensemble features: {ensemble_df['is_flood'].sum()} floods / {len(ensemble_df)} total")
        
        return physical_path, statistical_path, ensemble_path


if __name__ == "__main__":
    generator = MLTrainingDataGenerator()
    generator.generate_all(n_samples=10000)
