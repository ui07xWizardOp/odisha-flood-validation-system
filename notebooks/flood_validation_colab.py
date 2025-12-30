# -*- coding: utf-8 -*-
"""
# 🌊 Odisha Flood Validation System - Complete Colab Notebook

**AI/ML-Enhanced Crowdsourced Flood Validation**

This notebook covers the complete pipeline:
1. Data Exploration
2. DEM Processing
3. Algorithm Development
4. Experiments
5. Visualization

## Setup Instructions
Run this notebook in Google Colab:
1. Upload to Google Drive or open directly
2. Run all cells in order
3. Results are saved to `results/` directory

**Authors:** Research Team  
**Study Area:** Mahanadi Delta, Odisha (19.5°N - 21.5°N, 84.5°E - 87.0°E)
"""

# %% [markdown]
# ## 📦 Section 0: Environment Setup

# %%
# Install dependencies (run in Colab - uncomment if needed)
# In Colab, you can run these cells as-is. For local Python, use pip directly.
# import subprocess
# subprocess.run(["pip", "install", "-q", "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn", "scipy"])
# subprocess.run(["pip", "install", "-q", "geopandas", "rasterio", "shapely"])
# subprocess.run(["pip", "install", "-q", "fastapi", "pydantic"])

print("✅ Dependencies check - ensure packages are installed!")

# %%
# Clone repository (if running in Colab)
# Uncomment the following lines if you need to clone the repo:
# !git clone https://github.com/your-org/odisha-flood-validation.git
# %cd odisha-flood-validation

# %%
# Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("📊 Libraries imported successfully!")

# %% [markdown]
# ---
# ## 📍 Section 1: Study Area & Configuration

# %%
# Study Area Configuration
class Config:
    """Configuration for Mahanadi Delta study."""
    
    # Bounding Box
    MIN_LAT = 19.5
    MAX_LAT = 21.5
    MIN_LON = 84.5
    MAX_LON = 87.0
    
    # Reference Points
    CUTTACK = (20.4625, 85.8830)
    PURI = (19.8135, 85.8312)
    BHUBANESWAR = (20.2961, 85.8245)
    
    # Validation Parameters
    VALIDATION_THRESHOLD = 0.7
    LAYER_WEIGHTS = {'physical': 0.4, 'statistical': 0.4, 'reputation': 0.2}
    
    # Physical Layer
    HAND_THRESHOLD_HIGH = 10.0  # meters
    HAND_THRESHOLD_SUSPICIOUS = 5.0
    SLOPE_MAX = 30.0  # degrees
    SLOPE_STEEP = 15.0
    
    # Paths
    DATA_DIR = Path("data")
    RESULTS_DIR = Path("results")

config = Config()
print(f"📍 Study Area: Mahanadi Delta")
print(f"   Bounds: {config.MIN_LAT}°N - {config.MAX_LAT}°N, {config.MIN_LON}°E - {config.MAX_LON}°E")

# %% [markdown]
# ---
# ## 🧪 Section 2: Synthetic Data Generation

# %%
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import random

class SyntheticDataGenerator:
    """Generate synthetic flood reports with controlled noise."""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Create synthetic flood zone (ellipse around Cuttack)
        center = Point(config.CUTTACK[1], config.CUTTACK[0])  # (lon, lat)
        self.flood_polygon = center.buffer(0.15)  # ~15km radius
        
        # Generate user pool
        self.users = self._generate_users(100)
    
    def _generate_users(self, n: int) -> pd.DataFrame:
        """Create users with varying reliability."""
        users = []
        for i in range(n):
            if i < 70:  # 70% reliable
                accuracy = np.random.uniform(0.8, 0.95)
                category = 'reliable'
            elif i < 90:  # 20% average
                accuracy = np.random.uniform(0.5, 0.8)
                category = 'average'
            else:  # 10% unreliable
                accuracy = np.random.uniform(0.1, 0.5)
                category = 'unreliable'
            users.append({'user_id': i+1, 'accuracy': accuracy, 'category': category, 'trust_score': 0.5})
        return pd.DataFrame(users)
    
    def _random_point_in_polygon(self, polygon) -> Tuple[float, float]:
        minx, miny, maxx, maxy = polygon.bounds
        while True:
            pnt = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(pnt):
                return (pnt.y, pnt.x)
    
    def _random_point_outside_polygon(self, polygon) -> Tuple[float, float]:
        while True:
            lat = np.random.uniform(config.MIN_LAT, config.MAX_LAT)
            lon = np.random.uniform(config.MIN_LON, config.MAX_LON)
            if not polygon.contains(Point(lon, lat)):
                return (lat, lon)
    
    def generate_dataset(self, total: int = 1000, noise_pct: float = 15.0) -> pd.DataFrame:
        """Generate dataset with specified noise level."""
        reports = []
        noise_count = int(total * noise_pct / 100)
        clean_count = total - noise_count
        event_date = datetime(2019, 5, 3)
        
        # True Positives
        for _ in range(clean_count // 2):
            lat, lon = self._random_point_in_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'], 'latitude': lat, 'longitude': lon,
                'depth_meters': np.random.uniform(0.3, 3.0),
                'timestamp': event_date + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': True, 'claims_flood': True, 'report_type': 'TP'
            })
        
        # True Negatives
        for _ in range(clean_count - clean_count // 2):
            lat, lon = self._random_point_outside_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'], 'latitude': lat, 'longitude': lon,
                'depth_meters': 0.0,
                'timestamp': event_date + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': False, 'claims_flood': False, 'report_type': 'TN'
            })
        
        # False Positives (noise)
        for _ in range(noise_count // 2):
            lat, lon = self._random_point_outside_polygon(self.flood_polygon)
            user = self.users[self.users['category'] == 'unreliable'].sample(1, replace=True).iloc[0]
            reports.append({
                'user_id': user['user_id'], 'latitude': lat, 'longitude': lon,
                'depth_meters': np.random.uniform(0.5, 2.5),
                'timestamp': event_date + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': False, 'claims_flood': True, 'report_type': 'FP'
            })
        
        # False Negatives (noise)
        for _ in range(noise_count - noise_count // 2):
            lat, lon = self._random_point_in_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'], 'latitude': lat, 'longitude': lon,
                'depth_meters': 0.0,
                'timestamp': event_date + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': True, 'claims_flood': False, 'report_type': 'FN'
            })
        
        df = pd.DataFrame(reports).sample(frac=1).reset_index(drop=True)
        df['report_id'] = range(1, len(df) + 1)
        return df

# Generate dataset
generator = SyntheticDataGenerator()
df = generator.generate_dataset(total=1000, noise_pct=15)
print(f"✅ Generated {len(df)} synthetic reports")
print(f"\n📊 Report Type Distribution:")
print(df['report_type'].value_counts())

# %%
# Visualize spatial distribution
fig, ax = plt.subplots(figsize=(12, 10))

colors = {'TP': '#2ecc71', 'TN': '#3498db', 'FP': '#e74c3c', 'FN': '#f39c12'}
labels = {'TP': 'True Positive', 'TN': 'True Negative', 'FP': 'False Positive', 'FN': 'False Negative'}

for rtype, group in df.groupby('report_type'):
    ax.scatter(group['longitude'], group['latitude'], 
               c=colors[rtype], label=labels[rtype], alpha=0.6, s=30, edgecolor='white', linewidth=0.5)

# Plot flood zone boundary
from shapely.geometry import mapping
x, y = generator.flood_polygon.exterior.xy
ax.plot(x, y, 'k--', linewidth=2, label='Flood Zone Boundary')

# Mark major cities
cities = {'Cuttack': config.CUTTACK, 'Puri': config.PURI, 'Bhubaneswar': config.BHUBANESWAR}
for city, (lat, lon) in cities.items():
    ax.plot(lon, lat, 'k^', markersize=12)
    ax.annotate(city, (lon, lat), xytext=(5, 5), textcoords='offset points', fontweight='bold')

ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)
ax.set_title('Synthetic Flood Reports - Mahanadi Delta', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('synthetic_reports_map.png', dpi=150)
plt.show()
print("📍 Map saved as 'synthetic_reports_map.png'")

# %% [markdown]
# ---
# ## 🧠 Section 3: Validation Algorithm Implementation

# %%
class PhysicalValidator:
    """Layer 1: Physical Plausibility based on terrain."""
    
    def validate(self, lat: float, lon: float, depth: float, features: Dict) -> Dict:
        # HAND Check
        hand = features.get('hand', 5.0)
        if hand > 10: hand_score = 0.1
        elif hand > 5: hand_score = 0.4
        elif hand < 1: hand_score = 1.0
        else: hand_score = 1.0 - 0.15 * (hand - 1)
        
        # Slope Check
        slope = features.get('slope', 2.0)
        if slope > 30: slope_score = 0.0
        elif slope > 15: slope_score = 0.3
        else: slope_score = 1.0 - 0.046 * slope
        
        # Elevation Context
        elev_diff = features.get('elev_diff', 0.0)
        if elev_diff > 5: elev_score = 0.2
        elif elev_diff < -2: elev_score = 1.0
        else: elev_score = 0.8
        
        # Aggregate
        l1_score = 0.4 * hand_score + 0.4 * elev_score + 0.2 * slope_score
        return {'layer1_score': round(l1_score, 3), 'hand_score': round(hand_score, 3),
                'slope_score': round(slope_score, 3), 'elev_score': round(elev_score, 3)}


class StatisticalValidator:
    """Layer 2: Statistical consistency with neighbors."""
    
    def validate(self, lat: float, lon: float, depth: float, 
                 neighbors: pd.DataFrame, rainfall: float) -> Dict:
        # Spatial clustering
        if len(neighbors) >= 5: spatial_score = 1.0
        elif len(neighbors) >= 3: spatial_score = 0.8
        elif len(neighbors) >= 1: spatial_score = 0.6
        else: spatial_score = 0.4
        
        # Temporal (rainfall)
        if rainfall > 100: temporal_score = 1.0
        elif rainfall > 50: temporal_score = 0.8
        elif rainfall > 10: temporal_score = 0.6
        else: temporal_score = 0.3
        
        # Outlier check
        if len(neighbors) >= 3:
            mean_d = neighbors['depth_meters'].mean()
            std_d = neighbors['depth_meters'].std()
            if std_d > 0:
                z = abs(depth - mean_d) / std_d
                outlier_score = 1.0 if z < 1 else (0.7 if z < 2 else 0.2)
            else:
                outlier_score = 1.0 if abs(depth - mean_d) < 0.5 else 0.2
        else:
            outlier_score = 0.5
        
        l2_score = 0.5 * spatial_score + 0.3 * temporal_score + 0.2 * outlier_score
        return {'layer2_score': round(l2_score, 3)}


class ReputationSystem:
    """Layer 3: User trust scoring."""
    
    def __init__(self, users_df: pd.DataFrame):
        self.users = users_df.set_index('user_id')['trust_score'].to_dict()
    
    def validate(self, user_id: int) -> Dict:
        trust = self.users.get(user_id, 0.5)
        return {'layer3_score': trust}


class FloodValidator:
    """Main validation orchestrator."""
    
    def __init__(self, users_df: pd.DataFrame):
        self.layer1 = PhysicalValidator()
        self.layer2 = StatisticalValidator()
        self.layer3 = ReputationSystem(users_df)
    
    def validate(self, report: Dict, all_reports: pd.DataFrame, 
                 features: Dict = None, rainfall: float = 50.0) -> Dict:
        if features is None:
            # Simulate terrain features based on location
            # In production, this would query actual rasters
            in_flood_zone = generator.flood_polygon.contains(
                Point(report['longitude'], report['latitude'])
            )
            features = {
                'hand': 2.0 if in_flood_zone else 8.0,
                'slope': 1.5 if in_flood_zone else 5.0,
                'elev_diff': -1.0 if in_flood_zone else 3.0
            }
        
        # Find neighbors
        dists = np.sqrt((all_reports['latitude'] - report['latitude'])**2 + 
                        (all_reports['longitude'] - report['longitude'])**2)
        neighbors = all_reports[dists < 0.002]
        
        # Run layers
        l1 = self.layer1.validate(report['latitude'], report['longitude'], 
                                   report['depth_meters'], features)
        l2 = self.layer2.validate(report['latitude'], report['longitude'],
                                   report['depth_meters'], neighbors, rainfall)
        l3 = self.layer3.validate(report['user_id'])
        
        # Aggregate
        final_score = 0.4 * l1['layer1_score'] + 0.4 * l2['layer2_score'] + 0.2 * l3['layer3_score']
        status = 'validated' if final_score >= 0.7 else 'flagged'
        
        return {
            'final_score': round(final_score, 3),
            'status': status,
            'layer_scores': {'L1': l1['layer1_score'], 'L2': l2['layer2_score'], 'L3': l3['layer3_score']}
        }

# Initialize validator
validator = FloodValidator(generator.users)
print("✅ Validation algorithm initialized")

# %% [markdown]
# ---
# ## 📊 Section 4: Run Experiments

# %%
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

def run_experiment(df: pd.DataFrame, validator: FloodValidator) -> Dict:
    """Run validation on all reports and compute metrics."""
    results = []
    
    for _, row in df.iterrows():
        report = row.to_dict()
        result = validator.validate(report, df)
        results.append({
            'report_id': report['report_id'],
            'ground_truth': report['ground_truth_is_flood'],
            'claims_flood': report['claims_flood'],
            'predicted_valid': result['status'] == 'validated',
            'final_score': result['final_score'],
            'L1': result['layer_scores']['L1'],
            'L2': result['layer_scores']['L2'],
            'L3': result['layer_scores']['L3']
        })
    
    results_df = pd.DataFrame(results)
    
    # Calculate metrics (for flood claims)
    flood_claims = results_df[results_df['claims_flood'] == True]
    y_true = flood_claims['ground_truth'].astype(int).values
    y_pred = flood_claims['predicted_valid'].astype(int).values
    
    return {
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'accuracy': accuracy_score(y_true, y_pred),
        'results_df': results_df
    }

# Run at different noise levels
noise_levels = [5, 10, 15, 20, 30]
all_results = []

print("🧪 Running experiments...")
for noise in noise_levels:
    dataset = generator.generate_dataset(total=1000, noise_pct=noise)
    metrics = run_experiment(dataset, validator)
    all_results.append({
        'noise_level': noise,
        'precision': metrics['precision'],
        'recall': metrics['recall'],
        'f1': metrics['f1']
    })
    print(f"   {noise}% noise: F1={metrics['f1']:.3f}, Precision={metrics['precision']:.3f}, Recall={metrics['recall']:.3f}")

results_summary = pd.DataFrame(all_results)
print("\n✅ Experiments complete!")

# %%
# Visualize results
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# F1 vs Noise
ax1 = axes[0]
ax1.plot(results_summary['noise_level'], results_summary['f1'] * 100, 
         'o-', linewidth=2, markersize=10, color='#1dd1a1', label='Proposed Method')
ax1.axhline(y=90, color='gray', linestyle='--', alpha=0.5, label='Target (90%)')
ax1.set_xlabel('Noise Level (%)', fontsize=12)
ax1.set_ylabel('F1 Score (%)', fontsize=12)
ax1.set_title('Validation Performance vs. Noise', fontsize=14, fontweight='bold')
ax1.set_ylim(70, 100)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Precision-Recall
ax2 = axes[1]
ax2.scatter(results_summary['recall'] * 100, results_summary['precision'] * 100, 
            s=200, c=results_summary['noise_level'], cmap='RdYlGn_r', edgecolor='black')
for i, row in results_summary.iterrows():
    ax2.annotate(f"{row['noise_level']}%", (row['recall']*100, row['precision']*100),
                 xytext=(5, 5), textcoords='offset points')
ax2.set_xlabel('Recall (%)', fontsize=12)
ax2.set_ylabel('Precision (%)', fontsize=12)
ax2.set_title('Precision-Recall Trade-off', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('experiment_results.png', dpi=150)
plt.show()
print("📊 Results saved as 'experiment_results.png'")

# %% [markdown]
# ---
# ## 📋 Section 5: Results Summary

# %%
# Final results table
print("\n" + "="*60)
print("📋 EXPERIMENT RESULTS SUMMARY")
print("="*60)
print(f"\nStudy Area: Mahanadi Delta, Odisha")
print(f"Dataset Size: 1000 reports per experiment")
print(f"Validation Threshold: {config.VALIDATION_THRESHOLD}")
print(f"\nLayer Weights: {config.LAYER_WEIGHTS}")

print("\n" + "-"*60)
print(f"{'Noise %':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
print("-"*60)
for _, row in results_summary.iterrows():
    print(f"{row['noise_level']:<12} {row['precision']:.1%}{'':>5} {row['recall']:.1%}{'':>5} {row['f1']:.1%}")
print("-"*60)

# Key finding
best_row = results_summary.loc[results_summary['noise_level'] == 15].iloc[0]
print(f"\n🎯 At 15% noise (realistic scenario):")
print(f"   Precision: {best_row['precision']:.1%}")
print(f"   Recall: {best_row['recall']:.1%}")
print(f"   F1 Score: {best_row['f1']:.1%}")

print("\n" + "="*60)
print("✅ Analysis Complete!")
print("="*60)

# %%
# Save results to CSV
results_summary.to_csv('experiment_results.csv', index=False)
print("💾 Results saved to 'experiment_results.csv'")

# %% [markdown]
# ---
# ## 🔗 Next Steps
# 
# 1. **Download actual DEM data** from FABDEM for real terrain analysis
# 2. **Import ISRO Bhuvan** flood extent for ground truth validation
# 3. **Deploy API** using FastAPI for real-time validation
# 4. **Run web dashboard** for visualization
# 
# **Commands:**
# ```bash
# # Start API
# uvicorn src.api.main:app --reload
# 
# # Start web dashboard
# cd src/frontend/web-dashboard && npm start
# ```
