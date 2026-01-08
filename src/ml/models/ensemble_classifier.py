"""
Ensemble Flood Classifier - Edge Case Matrix Implementation

Combines multiple signals for robust flood detection:
1. MobileNetV2 CNN (scene classification)
2. HSV Water Detection (blue, brown, green/algae)
3. Texture Variance (water vs building)
4. NDWI Proxy (blue-green ratio for satellite images)
5. Glare Detection (specular highlights)
6. Vertical Reflection Detection (wet asphalt patterns)

Final decision: Weighted voting with edge case handling and detailed reasoning.
"""

import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Try importing required libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    from torchvision import transforms, models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class EnsembleFloodClassifier:
    """
    Ensemble classifier combining multiple detection methods with comprehensive
    edge case handling for robust flood detection.
    
    Edge Cases Handled:
    - False Negatives: Debris occlusion, algae water, clear water on roads
    - False Positives: Wet asphalt reflections, sun glare, night cityscapes
    
    Weights:
    - CNN: 0.45 (trained model)
    - Water Ratio: 0.30 (HSV color detection)
    - Texture: 0.15 (Laplacian variance)
    - NDWI Proxy: 0.10 (blue-green ratio)
    """
    
    # Ensemble weights
    WEIGHTS = {
        'cnn': 0.45,
        'water_ratio': 0.30,
        'texture': 0.15,
        'ndwi': 0.10
    }
    
    # Thresholds
    FLOOD_THRESHOLD = 0.60
    CONFIDENCE_MIN = 0.60
    
    # Edge case thresholds
    DEBRIS_TEXTURE_VARIANCE = 500  # High variance indicates debris
    CLEAR_WATER_TEXTURE_VARIANCE = 100  # Low variance indicates smooth surface
    GLARE_THRESHOLD = 0.15  # Significant glare area
    VERTICAL_REFLECTION_THRESHOLD = 0.6  # Column variance ratio for reflections
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.transform = None
        
        if TORCH_AVAILABLE:
            self._load_model(model_path)
            self._setup_transforms()
    
    def _load_model(self, model_path: Optional[str] = None):
        """Load MobileNetV2 model."""
        try:
            models_dir = Path(__file__).parent.parent.parent.parent / "models"
            
            candidates = [
                models_dir / "mobilenetv2_flood_balanced_final.pth",
                models_dir / "mobilenetv2_flood_final.pth",
                models_dir / "flood_cnn_v2.pth"
            ]
            
            model_path = None
            for candidate in candidates:
                if candidate.exists():
                    model_path = candidate
                    break
            
            if model_path:
                self.model = models.mobilenet_v2(weights=None)
                self.model.classifier = nn.Sequential(
                    nn.Dropout(0.2),
                    nn.Linear(self.model.last_channel, 1),
                    nn.Sigmoid()
                )
                
                checkpoint = torch.load(str(model_path), map_location='cpu')
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)
                
                self.model.eval()
                logger.info(f"Ensemble: Loaded CNN from {model_path.name}")
            else:
                logger.warning("Ensemble: No CNN model found")
                
        except Exception as e:
            logger.error(f"Ensemble: Failed to load model: {e}")
            self.model = None
    
    def _setup_transforms(self):
        """Setup image transforms for CNN."""
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def _fix_orientation(self, img, image_data: bytes):
        """
        Fix image orientation based on EXIF tags (critical for mobile uploads).
        
        OpenCV ignores EXIF orientation, so portrait photos load "sideways."
        This breaks sky detection and reflection analysis.
        
        EXIF Orientation values:
        - 1: Normal
        - 3: Rotate 180°
        - 6: Rotate 90° CW (camera was held in portrait, rotated right)
        - 8: Rotate 90° CCW (camera was held in portrait, rotated left)
        """
        try:
            from PIL import Image as PILImg, ExifTags
            
            pil_img = PILImg.open(io.BytesIO(image_data))
            
            # Find the Orientation tag ID
            orientation_tag = None
            for tag, name in ExifTags.TAGS.items():
                if name == 'Orientation':
                    orientation_tag = tag
                    break
            
            if orientation_tag:
                exif = pil_img._getexif()
                if exif and orientation_tag in exif:
                    orientation = exif[orientation_tag]
                    
                    # Apply rotation to OpenCV image
                    if orientation == 3:   # Upside down
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif orientation == 6: # Rotated 90° CW
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    elif orientation == 8: # Rotated 90° CCW
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        except Exception:
            pass  # If EXIF parsing fails, assume standard orientation
        
        return img
    
    def _decode_image(self, image_data: bytes) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Decode image once and convert to HSV once for performance.
        
        Returns:
            Tuple of (BGR image, HSV image) or (None, None) if decode fails.
        """
        if not CV2_AVAILABLE:
            return None, None
        
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None, None
            
            # Fix EXIF orientation (critical for mobile uploads)
            img = self._fix_orientation(img, image_data)
            
            # Convert to HSV once
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            return img, hsv
        except Exception as e:
            logger.error(f"Image decode failed: {e}")
            return None, None
    
    def _get_cnn_score(self, image_data: bytes) -> float:
        """Get CNN flood probability (0-1)."""
        if not TORCH_AVAILABLE or self.model is None:
            return 0.5
        
        try:
            img = PILImage.open(io.BytesIO(image_data)).convert('RGB')
            tensor = self.transform(img).unsqueeze(0)
            
            with torch.no_grad():
                output = self.model(tensor)
                return output.item()
        except Exception as e:
            logger.error(f"CNN inference failed: {e}")
            return 0.5
    
    def _get_water_ratio(self, image_data: bytes) -> Dict:
        """
        Get water pixel ratio using HSV color detection.
        
        Detects:
        - Blue water (clear/flowing)
        - Brown/muddy water
        - Green/algae water (stagnant)
        
        Uses ADAPTIVE SKY DETECTION to handle drone/nadir shots.
        
        Returns dict with total, blue, brown, green ratios and sky_detected flag.
        """
        if not CV2_AVAILABLE:
            return {'total': 0.0, 'blue': 0.0, 'brown': 0.0, 'green': 0.0, 'sky_detected': False}
        
        try:
            # Use centralized decode with EXIF orientation fix
            img, hsv = self._decode_image(image_data)
            if img is None or hsv is None:
                return {'total': 0.0, 'blue': 0.0, 'brown': 0.0, 'green': 0.0, 'sky_detected': False}
            
            height = img.shape[0]
            
            # ADAPTIVE SKY DETECTION (Hybrid Approach)
            # Sky if:
            # 1. Smooth texture (variance < 300) - Clear sky
            # 2. Blue dominance (>50%) - Cloudy/Textured blue sky
            
            top_region = img[:int(height * 0.3), :]
            gray_top = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
            top_variance = cv2.Laplacian(gray_top, cv2.CV_64F).var()
            
            # Calculate blue density in top 30%
            top_hsv = hsv[:int(height * 0.3), :, :]
            top_blue_mask = cv2.inRange(top_hsv, np.array([85, 50, 40]), np.array([135, 255, 255]))
            top_blue_ratio = np.sum(top_blue_mask > 0) / (top_region.shape[0] * top_region.shape[1])
            
            sky_detected = top_variance < 300 or top_blue_ratio > 0.50
            sky_cutoff = int(height * 0.4) if sky_detected else 0
            
            # Blue water - Apply sky mask only if sky is detected
            blue_mask = cv2.inRange(hsv, np.array([85, 50, 40]), np.array([135, 255, 255]))
            if sky_cutoff > 0:
                blue_mask[:sky_cutoff, :] = 0
            
            # Brown/muddy water (no sky cutoff - brown isn't confused with sky)
            brown_mask1 = cv2.inRange(hsv, np.array([10, 20, 20]), np.array([40, 255, 200]))
            brown_mask2 = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([10, 255, 200]))
            brown_mask3 = cv2.inRange(hsv, np.array([170, 20, 20]), np.array([180, 255, 200]))
            
            # GREEN/ALGAE WATER (Stagnant water detection)
            green_mask = cv2.inRange(hsv, np.array([35, 30, 30]), np.array([85, 255, 200]))
            if sky_cutoff > 0:
                green_mask[:sky_cutoff, :] = 0  # Exclude distant green trees
            
            # Combine all water masks
            water_mask = cv2.bitwise_or(blue_mask, brown_mask1)
            water_mask = cv2.bitwise_or(water_mask, brown_mask2)
            water_mask = cv2.bitwise_or(water_mask, brown_mask3)
            water_mask = cv2.bitwise_or(water_mask, green_mask)
            
            total_pixels = img.shape[0] * img.shape[1]
            
            blue_ratio = np.sum(blue_mask > 0) / total_pixels
            brown_final = cv2.bitwise_or(brown_mask1, cv2.bitwise_or(brown_mask2, brown_mask3))
            brown_ratio = np.sum(brown_final > 0) / total_pixels
            green_ratio = np.sum(green_mask > 0) / total_pixels
            water_ratio = np.sum(water_mask > 0) / total_pixels
            
            return {
                'total': min(float(water_ratio), 1.0),
                'blue': min(float(blue_ratio), 1.0),
                'brown': min(float(brown_ratio), 1.0),
                'green': min(float(green_ratio), 1.0),
                'sky_detected': sky_detected,
                'water_mask': water_mask  # Return for geometric analysis
            }
        except Exception as e:
            logger.error(f"Water ratio failed: {e}")
            return {'total': 0.0, 'blue': 0.0, 'brown': 0.0, 'green': 0.0, 'sky_detected': False}
    
    def _get_texture_score(self, img: np.ndarray) -> Dict:
        """
        Get texture score and raw variance from pre-decoded image.
        
        Args:
            img: Pre-decoded BGR image array (from _decode_image)
        
        Returns:
            Dict with 'score' (0-1, low variance = smooth = water-like)
            and 'variance' (raw Laplacian variance for edge case detection)
        """
        if not CV2_AVAILABLE or img is None:
            return {'score': 0.5, 'variance': 250.0}
        
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            # Normalize: <100 = very smooth (1.0), >500 = very textured (0.0)
            if variance < 100:
                score = 1.0
            elif variance > 500:
                score = 0.0
            else:
                score = 1.0 - (variance - 100) / 400
            
            return {
                'score': score,
                'variance': float(variance)
            }
        except Exception as e:
            logger.error(f"Texture score failed: {e}")
            return {'score': 0.5, 'variance': 250.0}
    
    def _get_ndwi_proxy(self, img: np.ndarray) -> float:
        """
        NDWI proxy using visible bands: (Blue - Red) / (Blue + Red).
        
        Args:
            img: Pre-decoded BGR image array (from _decode_image)
        """
        if not CV2_AVAILABLE or img is None:
            return 0.5
        
        try:
            b, g, r = cv2.split(img)
            b_float = b.astype(float)
            r_float = r.astype(float)
            
            denominator = b_float + r_float
            denominator[denominator == 0] = 1
            
            ndwi_proxy = (b_float - r_float) / denominator
            mean_ndwi = (np.mean(ndwi_proxy) + 1) / 2
            
            return float(mean_ndwi)
        except Exception as e:
            logger.error(f"NDWI proxy failed: {e}")
            return 0.5
    
    def _get_brightness(self, hsv: np.ndarray) -> Dict:
        """
        Get brightness metrics from V channel of pre-decoded HSV.
        
        Args:
            hsv: Pre-decoded HSV image array (from _decode_image)
        
        Returns dict with mean, median brightness.
        """
        if not CV2_AVAILABLE or hsv is None:
            return {'mean': 128.0, 'median': 128.0}
        
        try:
            v_channel = hsv[:, :, 2]
            
            return {
                'mean': float(np.mean(v_channel)),
                'median': float(np.median(v_channel))
            }
        except Exception as e:
            logger.error(f"Brightness check failed: {e}")
            return {'mean': 128.0, 'median': 128.0}
    
    def _get_glare_ratio(self, img: np.ndarray, hsv: np.ndarray) -> Dict:
        """
        Detect specular glare (sun reflection on dry surfaces).
        
        Args:
            img: Pre-decoded BGR image array
            hsv: Pre-decoded HSV image array
        
        Glare appears as blown-out white pixels (high V, low S).
        Returns ratio of glare pixels and whether glare is surrounded by dry surface.
        """
        if not CV2_AVAILABLE or img is None or hsv is None:
            return {'ratio': 0.0, 'is_dry_glare': False}
        
        try:
            # Glare: Very high brightness (V>250), low saturation (S<30)
            glare_mask = cv2.inRange(hsv, np.array([0, 0, 250]), np.array([180, 30, 255]))
            
            total_pixels = img.shape[0] * img.shape[1]
            glare_ratio = np.sum(glare_mask > 0) / total_pixels
            
            # Check if glare is surrounded by DRY surface (not water)
            # Dilate glare region and check if surrounding is low-saturation (dry)
            is_dry_glare = False
            if glare_ratio > 0.02:  # Significant glare present
                kernel = np.ones((15, 15), np.uint8)
                dilated = cv2.dilate(glare_mask, kernel, iterations=2)
                surrounding = dilated & ~glare_mask
                
                if np.sum(surrounding > 0) > 0:
                    surrounding_sat = hsv[:, :, 1][surrounding > 0]
                    avg_surrounding_sat = np.mean(surrounding_sat)
                    # Low saturation surroundings = dry (not water)
                    is_dry_glare = avg_surrounding_sat < 50
            
            return {
                'ratio': float(glare_ratio),
                'is_dry_glare': is_dry_glare
            }
        except Exception as e:
            logger.error(f"Glare detection failed: {e}")
            return {'ratio': 0.0, 'is_dry_glare': False}
    
    def _check_geometric_regularity(self, water_mask) -> Dict:
        """
        Check if water regions are geometrically regular (pool-like).
        
        Swimming pools and fountains are geometric (rectangular/circular).
        Floods are organic, messy, with irregular boundaries.
        
        Returns:
            is_pool_like: True if water looks like artificial pool
            max_rectangularity: Highest extent value found
            max_solidity: Highest convexity value found
        """
        if not CV2_AVAILABLE or water_mask is None:
            return {'is_pool_like': False, 'max_rectangularity': 0.0, 'max_solidity': 0.0}
        
        try:
            contours, _ = cv2.findContours(water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            max_rectangularity = 0.0
            max_solidity = 0.0
            pool_like_regions = 0
            significant_regions = 0
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 500:  # Ignore small puddles
                    continue
                
                significant_regions += 1
                
                # Check 1: Rectangularity (extent)
                # extent = contour_area / bounding_rect_area
                # Perfect rectangle = 1.0, irregular = lower
                x, y, w, h = cv2.boundingRect(cnt)
                rect_area = w * h
                extent = float(area) / rect_area if rect_area > 0 else 0
                
                # Check 2: Convexity (solidity)
                # solidity = contour_area / convex_hull_area
                # Convex shapes = high, concave/messy = lower
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = float(area) / hull_area if hull_area > 0 else 0
                
                max_rectangularity = max(max_rectangularity, extent)
                max_solidity = max(max_solidity, solidity)
                
                # If VERY rectangular (>0.85) AND solid (>0.9), count as pool-like
                if extent > 0.85 and solidity > 0.9:
                    pool_like_regions += 1
            
            # If any significant region is pool-like, flag it
            is_pool_like = pool_like_regions > 0 and significant_regions > 0
            
            return {
                'is_pool_like': is_pool_like,
                'max_rectangularity': float(max_rectangularity),
                'max_solidity': float(max_solidity),
                'pool_regions': pool_like_regions,
                'total_regions': significant_regions
            }
        except Exception as e:
            logger.error(f"Geometric regularity check failed: {e}")
            return {'is_pool_like': False, 'max_rectangularity': 0.0, 'max_solidity': 0.0}
    
    def _detect_vertical_reflections(self, img: np.ndarray, hsv: np.ndarray) -> Dict:
        """
        Detect vertical reflection patterns (wet asphalt/road).
        
        Args:
            img: Pre-decoded BGR image array
            hsv: Pre-decoded HSV image array
        
        Wet roads reflect light in vertical streaks (sky/lights).
        Real flood pools have more horizontal, uniform patterns.
        
        Returns:
            is_vertical_reflection: True if blue pixels form vertical streaks
            confidence: 0-1 confidence in detection
        """
        if not CV2_AVAILABLE or img is None or hsv is None:
            return {'is_vertical_reflection': False, 'confidence': 0.0, 'vertical_blob_ratio': 0.0}
        
        try:
            # Focus on bottom 60% of image (where reflections appear)
            height = img.shape[0]
            bottom_region = hsv[int(height * 0.4):, :, :]
            
            # Blue detection in bottom region
            blue_mask = cv2.inRange(bottom_region, np.array([85, 50, 40]), np.array([135, 255, 255]))
            
            if np.sum(blue_mask > 0) < 100:  # Not enough blue pixels
                return {'is_vertical_reflection': False, 'confidence': 0.0, 'vertical_blob_ratio': 0.0}
            
            # IMPROVED: Use contour aspect ratio instead of global variance
            # Reflections form tall, thin streaks (aspect ratio < 0.4)
            # Floods form wide, horizontal pools (aspect ratio > 1.0)
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            vertical_blobs = 0
            total_blobs = 0
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 50:  # Noise
                    continue
                    
                x, y, w, h = cv2.boundingRect(cnt)
                if h == 0:
                    continue
                    
                aspect_ratio = float(w) / h
                
                # Tall and thin (streak) = vertical reflection
                if aspect_ratio < 0.4:
                    vertical_blobs += 1
                total_blobs += 1
            
            # If >50% of blue blobs are vertical streaks, it's a reflection
            if total_blobs > 0:
                vertical_ratio = vertical_blobs / total_blobs
                is_vertical = vertical_ratio > 0.5
                confidence = vertical_ratio if is_vertical else 0.0
            else:
                vertical_ratio = 0.0
                is_vertical = False
                confidence = 0.0
            
            return {
                'is_vertical_reflection': is_vertical,
                'confidence': float(confidence),
                'vertical_blob_ratio': float(vertical_ratio)
            }
        except Exception as e:
            logger.error(f"Vertical reflection detection failed: {e}")
            return {'is_vertical_reflection': False, 'confidence': 0.0, 'vertical_blob_ratio': 0.0}
    
    def predict(self, image_data: bytes) -> Dict:
        """
        Ensemble prediction with comprehensive edge case handling.
        
        Returns:
            Dict with is_flood, confidence, scores, edge_case_reasons, and detailed signals
        """
        # Initialize edge case tracking
        edge_case_reasons: List[str] = []
        edge_case_adjustments: List[str] = []
        
        # ===== STEP 1: SINGLE-PASS DECODE (Performance Optimization) =====
        # Decode image ONCE with EXIF rotation fix, convert to HSV ONCE
        # Then pass pre-decoded arrays to all CV2-based helpers
        img, hsv = self._decode_image(image_data)
        
        if img is None:
            return {
                "is_flood": False, "confidence": 0.0, 
                "reason": "Image decode failed",
                "individual_scores": {}, "edge_cases_detected": [],
                "model": "Ensemble v2 (decode_failed)"
            }
        
        # ===== STEP 2: Get all signals (using pre-decoded arrays) =====
        # CNN needs raw bytes (uses PIL internally)
        cnn_score = self._get_cnn_score(image_data)
        
        # CV2-based helpers receive pre-decoded arrays
        water_ratios = self._get_water_ratio(image_data)  # Has its own decode with EXIF
        texture_data = self._get_texture_score(img)       # Uses pre-decoded img
        ndwi_score = self._get_ndwi_proxy(img)            # Uses pre-decoded img
        brightness_data = self._get_brightness(hsv)       # Uses pre-decoded hsv
        glare_data = self._get_glare_ratio(img, hsv)      # Uses pre-decoded img, hsv
        reflection_data = self._detect_vertical_reflections(img, hsv)  # Uses img, hsv
        
        # Extract values
        raw_total = water_ratios.get('total', 0.0)
        blue_ratio = water_ratios.get('blue', 0.0)
        brown_ratio = water_ratios.get('brown', 0.0)
        green_ratio = water_ratios.get('green', 0.0)
        
        texture_score = texture_data.get('score', 0.5)
        texture_variance = texture_data.get('variance', 250.0)
        
        brightness_mean = brightness_data.get('mean', 128.0)
        brightness_median = brightness_data.get('median', 128.0)
        
        glare_ratio = glare_data.get('ratio', 0.0)
        is_dry_glare = glare_data.get('is_dry_glare', False)
        
        is_vertical_reflection = reflection_data.get('is_vertical_reflection', False)
        reflection_confidence = reflection_data.get('confidence', 0.0)
        
        # Signal Validation Flags
        # Refined High Texture Check:
        # If texture IS high (>2000), it's likely a city... UNLESS brown > 30% (Massive Muddy Flood)
        # FLOOD_Houses has variance ~4300 but Brown ~35% -> Should be FLOOD
        # NYC_Skyline has variance ~2700 but Brown        # Signal Validation Flags
        is_textured_city = texture_variance > 2000 and brown_ratio < 0.30
        valid_brown_signal = brown_ratio > 0.10 and not is_textured_city
        has_real_water_signal = valid_brown_signal or (blue_ratio > 0.05)
        
        # ===== STEP 2: Edge Case Detection =====
        
        # --- FALSE NEGATIVE EDGE CASES ---
        
        # Edge Case 1: DEBRIS-FILLED FLOOD
        # High CNN + High texture variance (debris) + Low water color
        is_debris_flood = False
        if cnn_score > 0.90 and texture_variance > self.DEBRIS_TEXTURE_VARIANCE and raw_total < 0.10:
            is_debris_flood = True
            edge_case_reasons.append("Debris-filled Flood (high CNN, textured surface obscuring water)")
        
        # Edge Case 2: GREEN/ALGAE WATER (stagnant flood)
        # IMPORTANT: Must verify texture is low. Grass is green but rough (variance > 400).
        # Algae water is smooth (low variance).
        has_algae_water = False
        if green_ratio > 0.15 and texture_variance < 400:
            has_algae_water = True
            edge_case_reasons.append(f"Algae/stagnant water detected ({green_ratio:.0%})")
        elif green_ratio > 0.15:
            # Green vegetation detected but ignored due to rough texture
            edge_case_reasons.append(f"Green vegetation detected ({green_ratio:.0%}, ignored - rough texture)")
        
        # Edge Case 3: CLEAR WATER ON ROAD
        # High CNN + Very smooth texture + Low water color = transparent water
        is_clear_water = False
        if cnn_score > 0.95 and texture_variance < self.CLEAR_WATER_TEXTURE_VARIANCE and raw_total < 0.10:
            is_clear_water = True
            edge_case_reasons.append("Clear/transparent water (high CNN, smooth texture, low color)")
        
        # --- FALSE POSITIVE EDGE CASES ---
        
        # Edge Case 4: WET ASPHALT / VERTICAL REFLECTIONS
        # Primary check: Vertical blue streaks (contour aspect ratio)
        # Fallback check: High blue + High texture variance (scattered reflections on rough surface)
        is_wet_asphalt = False
        if is_vertical_reflection and blue_ratio > 0.08:
            is_wet_asphalt = True
            edge_case_reasons.append(f"Wet asphalt reflections detected (vertical blue streaks, conf={reflection_confidence:.0%})")
        elif blue_ratio > 0.20 and texture_variance > 500:
            # Fallback: Blue reflections on rough/textured surface = wet street
            # Real flood water is smooth (low variance), wet asphalt is rough (high variance)
            is_wet_asphalt = True
            edge_case_reasons.append(f"Wet asphalt detected (high blue {blue_ratio:.0%} + rough texture {texture_variance:.0f})")
        
        # Edge Case 5: SUN GLARE on dry surface
        is_sun_glare = False
        if glare_ratio > self.GLARE_THRESHOLD and is_dry_glare and raw_total < 0.15:
            is_sun_glare = True
            edge_case_reasons.append(f"Sun glare on dry surface ({glare_ratio:.0%} glare)")
        
        # Edge Case 6: NIGHT CITYSCAPE (existing)
        is_nightscape = brightness_median < 50 and brightness_mean < 100
        if is_nightscape:
            edge_case_reasons.append("Night cityscape (dark with bright spots)")
        
        # Edge Case 7: MIXED URBAN COLORS (existing)
        # Refined: Raised brown threshold to 0.20 to avoid flagging muddy city floods as "mixed"
        has_mixed_colors = blue_ratio > 0.10 and brown_ratio > 0.20
        if has_mixed_colors:
            edge_case_reasons.append("Mixed urban scene (tan surfaces + blue sky)")
        
        # Edge Case 8: SWIMMING POOL (Geometric Regularity)
        # Check if water regions are artificially shaped (rectangular/circular)
        water_mask = water_ratios.get('water_mask', None)
        pool_data = self._check_geometric_regularity(water_mask) if water_mask is not None else {'is_pool_like': False}
        is_pool_like = pool_data.get('is_pool_like', False)
        if is_pool_like:
            edge_case_reasons.append(f"Swimming pool/fountain detected (rectangular={pool_data.get('max_rectangularity', 0):.0%}, solid={pool_data.get('max_solidity', 0):.0%})")
        
        # ===== STEP 3: Calculate Effective Water Ratio =====
        
        # Include green/algae water in calculation
        if has_algae_water:
            effective_green = green_ratio * 0.9  # Trust algae water at 90%
        else:
            effective_green = green_ratio * 0.3  # Low green could be vegetation
        
        # Determine effective water based on texture and edge cases
        if texture_score > 0.4:
            effective_water = raw_total + effective_green
        elif is_debris_flood:
            # DEBRIS: Trust CNN over color detection
            effective_water = 0.25  # Set moderate to allow CNN to influence
            edge_case_adjustments.append("Boosted effective water for debris-filled flood")
        elif is_clear_water:
            # CLEAR WATER: Trust CNN + smooth texture
            effective_water = 0.20  # Allow CNN influence
            edge_case_adjustments.append("Boosted effective water for clear water detection")
        elif valid_brown_signal and not has_mixed_colors:
            # Only count brown water if texture is reasonable (not city walls)
            effective_water = blue_ratio + (brown_ratio * 0.8) + effective_green
        elif has_mixed_colors or is_textured_city:
            effective_water = 0.05  # Urban scene / Textured City penalty
            edge_case_adjustments.append("High texture/Urban scene penalty")
        elif texture_score > 0.2:
            effective_water = blue_ratio + (brown_ratio * 0.5) + effective_green
        else:
            effective_water = blue_ratio + effective_green
        
        # ===== STEP 4: Calculate Base Ensemble Score =====
        
        ensemble_score = (
            self.WEIGHTS['cnn'] * cnn_score +
            self.WEIGHTS['water_ratio'] * effective_water +
            self.WEIGHTS['texture'] * texture_score +
            self.WEIGHTS['ndwi'] * ndwi_score
        )
        
        # ===== STEP 5: Apply Edge Case Penalties/Boosts =====
        
        # IMPORTANT: Skip certain penalties when CNN is VERY HIGH (>95%) AND
        # there's a real water signal (not just city lights being detected as water)
        # Real floods have: brown_ratio > 10% (muddy) OR blue_ratio > 5% (clear water in ground level)
        # EXCEPTION: If wet asphalt is detected, the blue signal is from sky reflections, NOT water
        # Refined water signal check:
        # Brown water is only valid if texture is reasonable. 
        # Extremely high texture (>2000) with brown usually means dense city/buildings, not water.
        # but if brown > 30%, we trust it (defined in Step 2: is_textured_city)
        
        # is_textured_city uses (texture > 2000 AND brown < 0.30)
        valid_brown_signal = brown_ratio > 0.10 and not is_textured_city
        
        has_real_water_signal = valid_brown_signal or (blue_ratio > 0.05 and not has_mixed_colors)
        trust_cnn_over_heuristics = cnn_score > 0.95 and has_real_water_signal and not is_wet_asphalt
        
        # False Positive Penalties
        is_snow_like = False
        if brightness_mean > 200 and not trust_cnn_over_heuristics:
            ensemble_score *= 0.3
            is_snow_like = True
            edge_case_adjustments.append("Snow/bright surface penalty (70%)")
        elif brightness_mean > 180 and not trust_cnn_over_heuristics:
            ensemble_score *= 0.7
            edge_case_adjustments.append("Bright surface penalty (30%)")
        
        if is_nightscape and not trust_cnn_over_heuristics:
            ensemble_score *= 0.5
            edge_case_adjustments.append("Nightscape penalty (50%)")
        
        if is_wet_asphalt and not trust_cnn_over_heuristics:
            ensemble_score *= 0.6
            edge_case_adjustments.append("Wet asphalt reflection penalty (40%)")
        
        if is_sun_glare and not trust_cnn_over_heuristics:
            ensemble_score *= 0.5
            edge_case_adjustments.append("Sun glare penalty (50%)")
        
        # Swimming pool penalty (geometric water shapes are NOT floods)
        if is_pool_like:
            ensemble_score *= 0.2  # Massive 80% penalty
            edge_case_adjustments.append("Swimming pool penalty (80%)")
        
        # Dry rough surface penalty
        if effective_water < 0.05 and texture_score < 0.2:
            ensemble_score *= 0.6
            edge_case_adjustments.append("Dry rough surface penalty (40%)")
        
        # Additional false positive check
        if raw_total < 0.05 and texture_score > 0.8 and ndwi_score > 0.5:
            ensemble_score *= 0.5
            edge_case_adjustments.append("No color signature penalty (50%)")
        
        # ===== STEP 6: CNN Override with Edge Case Awareness =====
        
        cnn_override = False
        total_water = effective_water
        
        # Block overrides for known false positive edge cases
        # Also block if it's a "Texture City" (dense buildings looking like brown water)
        block_override = is_nightscape or is_wet_asphalt or is_sun_glare or has_mixed_colors or is_textured_city
        
        # TIER 0: Debris-filled or Clear Water Flood (Trust CNN heavily)
        if (is_debris_flood or is_clear_water) and cnn_score > 0.90:
            ensemble_score = max(ensemble_score, 0.70)
            cnn_override = True
            edge_case_adjustments.append(f"CNN override for {'debris' if is_debris_flood else 'clear water'} flood")
        
        # TIER 1: CNN PERFECT (>99%)
        elif cnn_score > 0.99 and total_water > 0.10 and not block_override:
            ensemble_score = max(ensemble_score, 0.75)
            cnn_override = True
        
        # TIER 2: CNN very high (>98%)
        elif cnn_score > 0.98 and total_water > 0.25 and not block_override:
            ensemble_score = max(ensemble_score, 0.70)
            cnn_override = True
        
        # TIER 3: CNN high (>95%)
        elif cnn_score > 0.95 and total_water > 0.20 and not block_override:
            ensemble_score = max(ensemble_score, 0.62)
            cnn_override = True
        
        # PENALTY: High CNN but NO water (unless debris/clear water edge case)
        if cnn_score > 0.90 and total_water < 0.05 and not is_debris_flood and not is_clear_water:
            ensemble_score *= 0.7
            edge_case_adjustments.append("High CNN no water penalty (30%)")
        
        # ===== STEP 7: Final Decision =====
        
        is_flood = ensemble_score >= self.FLOOD_THRESHOLD
        
        # Calculate confidence
        if is_flood:
            confidence = 0.5 + (ensemble_score - self.FLOOD_THRESHOLD) * 2
        else:
            confidence = 0.5 + (self.FLOOD_THRESHOLD - ensemble_score) * 2
        confidence = max(self.CONFIDENCE_MIN, min(0.99, confidence))
        
        # ===== STEP 8: Generate Reasoning =====
        
        signals = []
        if cnn_score > 0.5:
            signals.append(f"CNN ({cnn_score:.0%})")
        if raw_total > 0.1:
            signals.append(f"Water color ({raw_total:.0%})")
        if green_ratio > 0.1:
            signals.append(f"Algae water ({green_ratio:.0%})")
        if texture_score > 0.6:
            signals.append("Smooth texture")
        elif texture_variance > self.DEBRIS_TEXTURE_VARIANCE:
            signals.append(f"High texture variance ({texture_variance:.0f})")
        if ndwi_score > 0.55:
            signals.append("High water index")
        if is_snow_like:
            edge_case_reasons.append("Snow/bright penalty")
        if cnn_override:
            signals.append("CNN override active")
        
        # Flood type classification
        flood_type = None
        if is_flood:
            if is_debris_flood:
                flood_type = "Debris-filled Flood"
            elif has_algae_water:
                flood_type = "Stagnant/Algae Flood"
            elif is_clear_water:
                flood_type = "Clear Water Flood"
            elif brown_ratio > blue_ratio:
                flood_type = "Muddy Water Flood"
            else:
                flood_type = "Clear Water Flood"
        
        return {
            "is_flood": is_flood,
            "flood_type": flood_type,
            "confidence": round(confidence, 3),
            "ensemble_score": round(ensemble_score, 3),
            "individual_scores": {
                "cnn": round(cnn_score, 3),
                "water_ratio": round(raw_total, 3),
                "blue_ratio": round(blue_ratio, 3),
                "brown_ratio": round(brown_ratio, 3),
                "green_ratio": round(green_ratio, 3),
                "texture": round(texture_score, 3),
                "texture_variance": round(texture_variance, 1),
                "ndwi": round(ndwi_score, 3),
                "brightness": round(brightness_mean, 1),
                "glare_ratio": round(glare_ratio, 3)
            },
            "edge_cases_detected": edge_case_reasons,
            "adjustments_applied": edge_case_adjustments,
            "signals": signals,
            "model": "Ensemble v2 (CNN+HSV+Texture+NDWI+EdgeCases)"
        }
    
    def validate_image(self, image_data: bytes) -> Dict:
        """Full validation pipeline for user-submitted image."""
        if len(image_data) < 1000:
            return {
                "valid": False, "score": 0.0, "reason": "Image too small",
                "is_flood_detected": False, "confidence": 0.0
            }
        
        if len(image_data) > 10_000_000:
            return {
                "valid": False, "score": 0.0, "reason": "Image too large (>10MB)",
                "is_flood_detected": False, "confidence": 0.0
            }
        
        result = self.predict(image_data)
        
        if result["is_flood"]:
            score = 0.5 + result["ensemble_score"] * 0.5
        else:
            score = 0.3
        
        return {
            "valid": True,
            "score": round(score, 3),
            "is_flood_detected": result["is_flood"],
            "flood_type": result.get("flood_type"),
            "confidence": result["confidence"],
            "water_coverage": result["individual_scores"]["water_ratio"],
            "model_used": result["model"],
            "signals": result["signals"],
            "edge_cases": result["edge_cases_detected"],
            "details": result["individual_scores"]
        }


# Create singleton instance
ensemble_classifier = EnsembleFloodClassifier()


# Testing
if __name__ == "__main__":
    from PIL import Image
    import io
    
    # Create test image (blue water)
    img = Image.new('RGB', (256, 256), (30, 100, 180))
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    
    result = ensemble_classifier.validate_image(buffer.getvalue())
    print("Test Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
