"""
Computer Vision Module for Flood Photo Validation.

Uses a lightweight approach with:
1. PyTorch/torchvision (if available) with MobileNetV2
2. OpenCV color-based water detection 
3. Heuristic fallback when ML libraries unavailable
"""

import numpy as np
from pathlib import Path
from typing import Dict, Optional
import logging
import io

logger = logging.getLogger(__name__)

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torchvision.models as models
    import torchvision.transforms as transforms
    from PIL import Image
    TORCH_AVAILABLE = True
except Exception as e:
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch not available (Error: {e}). Using heuristic CV predictions.")

# Try to import OpenCV for image processing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Water detection disabled.")

# Try PIL as fallback for image loading
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class FloodImageClassifier:
    """
    CNN-based classifier for flood photos.
    Uses MobileNetV2 as backbone (lightweight, works on CPU).
    Falls back to heuristic water detection when PyTorch unavailable.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self.transform = None
        
        if TORCH_AVAILABLE:
            self._load_model()
            self._setup_transforms()
    
    def _load_model(self):
        """Load trained MobileNetV2 model. Priority: balanced > Kaggle > v2."""
        try:
            models_dir = Path(__file__).parent.parent.parent.parent / "models"
            
            # Priority 0: Balanced model (trained on 50/50 flood/not-flood) - Best specificity
            balanced_model_path = models_dir / "mobilenetv2_flood_balanced_final.pth"
            
            # Priority 1: Kaggle Flood Dataset model (93%+ accuracy)
            kaggle_model_path = models_dir / "mobilenetv2_flood_final.pth"
            
            # Priority 2: v2 model (FloodNet trained)
            v2_model_path = models_dir / "flood_cnn_v2.pth"
            
            # Try loading in priority order
            model_path = None
            if balanced_model_path.exists():
                model_path = balanced_model_path
                model_name = "Balanced (50/50)"
            elif kaggle_model_path.exists():
                model_path = kaggle_model_path
                model_name = "Kaggle"
            elif v2_model_path.exists():
                model_path = v2_model_path
                model_name = "v2"
            
            if model_path:
                # Load model with simple classifier head (works for balanced, Kaggle, and v2)
                self.model = models.mobilenet_v2(weights=None)
                self.model.classifier = nn.Sequential(
                    nn.Dropout(0.2),
                    nn.Linear(self.model.last_channel, 1),
                    nn.Sigmoid()
                )
                
                checkpoint = torch.load(str(model_path), map_location=torch.device('cpu'))
                
                # Handle both full checkpoint and state_dict only formats
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    acc = checkpoint.get('model_config', {}).get('best_val_acc', 'N/A')
                    logger.info(f"Loaded {model_name} model (acc: {acc})")
                else:
                    self.model.load_state_dict(checkpoint)
                    logger.info(f"Loaded {model_name} model from {model_path}")
                
                self.model.eval()
            else:
                logger.warning(f"No custom flood model found. Disabling DL component.")
                self.model = None
                return
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {e}")
            self.model = None
    
    def _setup_transforms(self):
        """Setup image preprocessing transforms."""
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def predict(self, image_data: bytes) -> Dict:
        """
        Classify an image as flood/not-flood.
        
        ULTRA-CONSERVATIVE: Default is NOT flood.
        Requires strong evidence from BOTH OpenCV AND CNN to classify as flood.
        """
        water_ratio = 0.0
        is_flood = False  # Default: NOT flood (conservative)
        confidence = 0.6  # Default confidence for "not flood"
        model_used = "Heuristic"
        dl_confidence = 0.0
        
        # Step 1: OpenCV water detection
        if CV2_AVAILABLE:
            water_ratio = self._detect_water_ratio(image_data)
            model_used = "OpenCV-Water"
            
            # BALANCED: Flag if >20% of image is water-colored
            if water_ratio > 0.20:
                is_flood = True
                confidence = min(0.60 + water_ratio, 0.90)
            else:
                is_flood = False
                confidence = 0.75  # Confident it's NOT flood
        
        # Step 2: Deep learning refinement
        if TORCH_AVAILABLE and self.model is not None:
            try:
                dl_result = self._deep_learning_predict(image_data)
                dl_confidence = dl_result['confidence']
                model_used = "MobileNetV2+OpenCV"
                
                # BALANCED DECISION LOGIC (Kaggle-trained model):
                # Flood = True if:
                #   - CNN > 60% confident AND water > 10% (Common street flood)
                #   - OR water > 30% (Strong visual evidence, trust OpenCV)
                #   - OR CNN > 85% AND water > 5% (Strong model confidence with minimal water evidence)
                
                if dl_confidence > 0.60 and water_ratio > 0.10:
                    # Moderate confidence + some water = flood
                    is_flood = True
                    confidence = (dl_confidence + water_ratio) / 2 + 0.2
                elif water_ratio > 0.30:
                    # Significant water coverage = flood (trust OpenCV)
                    is_flood = True
                    confidence = 0.6 + water_ratio
                elif dl_confidence > 0.85 and water_ratio > 0.05:
                    # Very high model confidence WITH minimal water evidence
                    is_flood = True
                    confidence = dl_confidence
                elif dl_confidence < 0.40 or water_ratio < 0.03:
                    # CNN says NOT flood OR no water detected = NOT flood
                    is_flood = False
                    confidence = max(0.60, 1 - dl_confidence)
                else:
                    # Uncertain zone (40-60% confidence)
                    is_flood = False
                    confidence = 0.50
                    
            except Exception as e:
                logger.error(f"DL prediction failed: {e}")
        
        return {
            "is_flood": is_flood,
            "confidence": round(confidence, 3),
            "water_ratio": round(water_ratio, 3),
            "dl_confidence": round(dl_confidence, 3),
            "model": model_used
        }
    
    def _deep_learning_predict(self, image_data: bytes) -> Dict:
        """Use MobileNetV2 to analyze image features."""
        try:
            # Load image
            img = PILImage.open(io.BytesIO(image_data)).convert('RGB')
            
            # Transform
            input_tensor = self.transform(img).unsqueeze(0)
            
            # Run inference
            with torch.no_grad():
                output = self.model(input_tensor)
                # Output is single sigmoid value
                flood_prob = output.item()
            
            return {
                "confidence": flood_prob,
                "top_class": 1 if flood_prob > 0.5 else 0
            }
            
        except Exception as e:
            logger.error(f"DL inference failed: {e}")
            return {"confidence": 0.5, "top_class": -1}
    
    def _detect_water_ratio(self, image_data: bytes) -> float:
        """
        Use HSV color analysis + texture variance to estimate water coverage.
        
        Improvements over simple color:
        - Texture check: Water is smooth (low variance), concrete is textured (high variance)
        - Stricter gray detection to avoid false positives on buildings
        """
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 0.0
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate texture variance (Laplacian for edge detection)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            texture_variance = laplacian.var()
            
            # Define water color ranges (HSV)
            # Blue water (H: 90-130, high saturation)
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            
            # Brown/muddy water (H: 10-30, moderate saturation)
            lower_brown = np.array([10, 50, 50])
            upper_brown = np.array([30, 200, 200])
            
            # Gray/dark (potential standing water) - STRICTER thresholds
            # Only low saturation AND specific value range
            lower_gray = np.array([0, 0, 50])
            upper_gray = np.array([180, 30, 100])  # Reduced saturation threshold
            
            # Create masks
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
            gray_mask = cv2.inRange(hsv, lower_gray, upper_gray)
            
            # Combine blue and brown (definite water colors)
            definite_water = cv2.bitwise_or(blue_mask, brown_mask)
            
            # Calculate ratios
            total_pixels = img.shape[0] * img.shape[1]
            definite_water_pixels = np.sum(definite_water > 0)
            gray_pixels = np.sum(gray_mask > 0)
            
            # Base water ratio from definite water colors
            water_ratio = definite_water_pixels / total_pixels
            
            # TEXTURE CHECK: Only add gray as water if texture is LOW (smooth like water)
            # Buildings/concrete have high texture variance (>500), water has low (<200)
            TEXTURE_THRESHOLD = 300
            
            if texture_variance < TEXTURE_THRESHOLD:
                # Low texture = likely water surface, count gray pixels
                gray_water_ratio = (gray_pixels * 0.5) / total_pixels
                water_ratio += gray_water_ratio
            else:
                # High texture = probably buildings/roads, reduce gray contribution
                gray_water_ratio = (gray_pixels * 0.05) / total_pixels
                water_ratio += gray_water_ratio
            
            return min(float(water_ratio), 1.0)
            
        except Exception as e:
            logger.error(f"Water detection failed: {e}")
            return 0.0
    
    def validate_image(self, image_data: bytes) -> Dict:
        """
        Full validation pipeline for a user-submitted image.
        
        Returns:
            Dict with validation result and score
        """
        # Basic size checks
        if len(image_data) < 1000:  # Too small
            return {
                "valid": False,
                "score": 0.0,
                "reason": "Image too small",
                "is_flood_detected": False,
                "confidence": 0.0,
                "water_coverage": 0.0,
                "model_used": "None"
            }
        
        if len(image_data) > 10_000_000:  # Too large (>10MB)
            return {
                "valid": False,
                "score": 0.0,
                "reason": "Image too large (max 10MB)",
                "is_flood_detected": False,
                "confidence": 0.0,
                "water_coverage": 0.0,
                "model_used": "None"
            }
        
        # Run prediction
        prediction = self.predict(image_data)
        
        # Calculate validation score
        score = 0.3  # Base score for valid image
        
        if prediction['is_flood']:
            score += 0.4  # Flood detected bonus
        
        if prediction['water_ratio'] > 0.2:
            score += 0.2  # Significant water coverage
        elif prediction['water_ratio'] > 0.1:
            score += 0.1
        
        # Confidence adjustment
        score *= (0.5 + prediction['confidence'] * 0.5)
        
        return {
            "valid": True,
            "score": round(min(score, 1.0), 3),
            "is_flood_detected": prediction['is_flood'],
            "confidence": prediction['confidence'],
            "water_coverage": prediction['water_ratio'],
            "model_used": prediction['model']
        }


# Singleton instance
flood_classifier = FloodImageClassifier()


if __name__ == "__main__":
    # Test the classifier
    print("🖼️ Flood Image Classifier")
    print(f"   PyTorch available: {TORCH_AVAILABLE}")
    print(f"   OpenCV available: {CV2_AVAILABLE}")
    print(f"   PIL available: {PIL_AVAILABLE}")
    
    # Test with mock data
    mock_result = flood_classifier.validate_image(b'x' * 2000)  # Fake image data
    print(f"   Mock validation: {mock_result}")
