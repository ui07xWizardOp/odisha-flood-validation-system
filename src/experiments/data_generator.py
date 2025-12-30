import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Optional

class SyntheticDataGenerator:
    """
    Generates synthetic crowd-sourced flood reports with controlled noise levels.
    Used for experimental validation of the 3-layer algorithm.
    """
    
    # Odisha/Mahanadi Delta bounds
    LAT_MIN = 19.5
    LAT_MAX = 21.5
    LON_MIN = 84.5
    LON_MAX = 87.0
    
    # Flood event reference (Cyclone Fani 2019)
    EVENT_DATE = datetime(2019, 5, 3)
    
    def __init__(self, ground_truth_polygon: Optional[Polygon] = None, seed: int = 42):
        """
        Args:
            ground_truth_polygon: Shapely Polygon of actual flooded area.
                                  If None, uses a synthetic ellipse.
            seed: Random seed for reproducibility.
        """
        np.random.seed(seed)
        random.seed(seed)
        
        if ground_truth_polygon is None:
            # Create a synthetic flood zone (ellipse around Cuttack)
            center = (85.88, 20.46)  # Cuttack (lon, lat)
            self.flood_polygon = Point(center).buffer(0.15)  # ~15km radius
        else:
            self.flood_polygon = ground_truth_polygon
            
        # Simulated user pool
        self.users = self._generate_users(100)

    def _generate_users(self, n_users: int) -> pd.DataFrame:
        """
        Create a pool of users with varying reliability.
        70% reliable, 20% average, 10% unreliable.
        """
        users = []
        for i in range(n_users):
            if i < 70:
                accuracy = np.random.uniform(0.8, 0.95)
                category = 'reliable'
            elif i < 90:
                accuracy = np.random.uniform(0.5, 0.8)
                category = 'average'
            else:
                accuracy = np.random.uniform(0.1, 0.5)
                category = 'unreliable'
                
            users.append({
                'user_id': i + 1,
                'accuracy': accuracy,
                'category': category,
                'trust_score': 0.5  # Initial trust
            })
        return pd.DataFrame(users)

    def _random_point_in_polygon(self, polygon: Polygon) -> Tuple[float, float]:
        """Generate a random point inside a polygon."""
        minx, miny, maxx, maxy = polygon.bounds
        while True:
            pnt = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(pnt):
                return (pnt.y, pnt.x)  # (lat, lon)

    def _random_point_outside_polygon(self, polygon: Polygon) -> Tuple[float, float]:
        """Generate a random point outside the polygon but within study area."""
        while True:
            lat = np.random.uniform(self.LAT_MIN, self.LAT_MAX)
            lon = np.random.uniform(self.LON_MIN, self.LON_MAX)
            pnt = Point(lon, lat)
            if not polygon.contains(pnt):
                return (lat, lon)

    def generate_dataset(self, 
                         total_reports: int = 1000, 
                         noise_percentage: float = 15.0) -> pd.DataFrame:
        """
        Generate a dataset with specified noise level.
        
        Args:
            total_reports: Total number of reports to generate.
            noise_percentage: Percentage of reports that are incorrect (0-100).
            
        Returns:
            DataFrame with columns: user_id, lat, lon, depth, timestamp, 
                                    ground_truth_is_flood, claims_flood
        """
        reports = []
        noise_count = int(total_reports * noise_percentage / 100)
        clean_count = total_reports - noise_count
        
        # True Positives: Inside flood zone, claims flood (correct)
        tp_count = clean_count // 2
        for _ in range(tp_count):
            lat, lon = self._random_point_in_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'],
                'latitude': lat,
                'longitude': lon,
                'depth_meters': np.random.uniform(0.3, 3.0),
                'timestamp': self.EVENT_DATE + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': True,
                'claims_flood': True,
                'report_type': 'TP'
            })
        
        # True Negatives: Outside flood zone, does NOT claim flood (correct)
        tn_count = clean_count - tp_count
        for _ in range(tn_count):
            lat, lon = self._random_point_outside_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'],
                'latitude': lat,
                'longitude': lon,
                'depth_meters': 0.0,
                'timestamp': self.EVENT_DATE + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': False,
                'claims_flood': False,
                'report_type': 'TN'
            })
        
        # False Positives (Noise): Outside flood zone, FALSELY claims flood
        fp_count = noise_count // 2
        for _ in range(fp_count):
            lat, lon = self._random_point_outside_polygon(self.flood_polygon)
            # Unreliable users more likely to submit FP
            user = self.users[self.users['category'] == 'unreliable'].sample(1, replace=True).iloc[0]
            reports.append({
                'user_id': user['user_id'],
                'latitude': lat,
                'longitude': lon,
                'depth_meters': np.random.uniform(0.5, 2.5),  # Fake depth
                'timestamp': self.EVENT_DATE + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': False,
                'claims_flood': True,
                'report_type': 'FP'
            })
        
        # False Negatives (Noise): Inside flood zone, FAILS to report
        fn_count = noise_count - fp_count
        for _ in range(fn_count):
            lat, lon = self._random_point_in_polygon(self.flood_polygon)
            user = self.users.sample(1).iloc[0]
            reports.append({
                'user_id': user['user_id'],
                'latitude': lat,
                'longitude': lon,
                'depth_meters': 0.0,  # Claims no flood
                'timestamp': self.EVENT_DATE + timedelta(hours=np.random.randint(-12, 48)),
                'ground_truth_is_flood': True,
                'claims_flood': False,
                'report_type': 'FN'
            })
        
        df = pd.DataFrame(reports)
        df = df.sample(frac=1).reset_index(drop=True)  # Shuffle
        df['report_id'] = range(1, len(df) + 1)
        
        return df

    def generate_all_datasets(self, output_dir: str = "data/synthetic"):
        """Generate datasets at multiple noise levels."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for noise in [5, 10, 15, 20, 30]:
            df = self.generate_dataset(total_reports=1000, noise_percentage=noise)
            path = f"{output_dir}/crowd_reports_noise_{noise}pct.csv"
            df.to_csv(path, index=False)
            print(f"Generated: {path} ({len(df)} reports)")
            
        return True


if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    generator.generate_all_datasets()
