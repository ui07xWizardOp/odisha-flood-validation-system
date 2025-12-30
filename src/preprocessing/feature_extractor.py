import rasterio
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List

class FeatureExtractor:
    """
    Extracts geospatial features (Elevation, HAND, Slope) for specific coordinates
    using the processed rasters.
    """
    
    def __init__(self, 
                 dem_path: str = "data/processed/mahanadi_dem_30m.tif",
                 hand_path: str = "data/processed/mahanadi_hand.tif",
                 slope_path: str = "data/processed/mahanadi_slope.tif"):
        
        self.dem_path = Path(dem_path)
        self.hand_path = Path(hand_path)
        self.slope_path = Path(slope_path)
        
        self.datasets = {}
        
    def _open_dataset(self, path: Path):
        """Lazy loader for raster datasets."""
        if path not in self.datasets:
            if path.exists():
                self.datasets[path] = rasterio.open(path)
            else:
                # print(f"Warning: Raster {path} not found. Feature extraction will return None/0.")
                return None
        return self.datasets[path]

    def get_value_at_point(self, raster_path: Path, lat: float, lon: float) -> Optional[float]:
        """Sample a single raster at a coordinate."""
        src = self._open_dataset(raster_path)
        if src is None:
            return 0.0 # Default fallback safe value for missing data
            
        try:
            # sample() expects list of (x, y) coords
            # Note: rasterio.sample returns a generator
            vals = list(src.sample([(lon, lat)]))
            val = vals[0][0]
            
            # Check for nodata
            if src.nodata is not None and val == src.nodata:
                return None
            return float(val)
        except Exception as e:
            print(f"Error extracting value at {lat}, {lon}: {e}")
            return None

    def get_neighborhood_stats(self, lat: float, lon: float, radius_m: int = 100) -> Dict[str, float]:
        """
        Calculates statistics (mean, std) for elevation in a neighborhood.
        Note: Exact radius sampling in rasterio is complex without window read.
        Approximating 100m radius as ~3x3 or 5x5 pixel window (assuming ~30m resolution).
        """
        src = self._open_dataset(self.dem_path)
        if src is None:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}

        try:
            # 100m radius ~ 3-4 pixels (at 30m res). Window size 7x7 covers ~210m diam
            row, col = src.index(lon, lat)
            window_size = 3  # +/- 3 pixels -> 7x7 window
            
            window = rasterio.windows.Window(
                col - window_size, row - window_size, 
                window_size * 2 + 1, window_size * 2 + 1
            )
            
            data = src.read(1, window=window)
            
            # Filter nodata
            if src.nodata is not None:
                valid_data = data[data != src.nodata]
            else:
                valid_data = data.flatten()

            if len(valid_data) == 0:
                return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}

            return {
                'mean': float(np.mean(valid_data)),
                'std': float(np.std(valid_data)),
                'min': float(np.min(valid_data)),
                'max': float(np.max(valid_data))
            }
            
        except Exception:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}

    def extract_all_features(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Extracts all relevant geospatial features for validation.
        """
        elevation = self.get_value_at_point(self.dem_path, lat, lon)
        hand = self.get_value_at_point(self.hand_path, lat, lon)
        slope = self.get_value_at_point(self.slope_path, lat, lon)
        
        # Neighborhood stats
        nb_stats = self.get_neighborhood_stats(lat, lon, radius_m=100)
        
        # Derived feature: Elevation difference from local mean
        # Positive diff = higher than surroundings (hill)
        # Negative diff = lower than surroundings (depression)
        if elevation is not None:
            elev_diff = elevation - nb_stats['mean']
        else:
            elev_diff = 0.0

        return {
            'elevation': elevation if elevation is not None else 0.0,
            'hand': hand if hand is not None else 0.0,
            'slope': slope if slope is not None else 0.0,
            'elevation_neighborhood_mean': nb_stats['mean'],
            'elevation_neighborhood_std': nb_stats['std'],
            'elevation_diff_from_neighbors': elev_diff
        }

    def close(self):
        """Close input datasets."""
        for src in self.datasets.values():
            src.close()
