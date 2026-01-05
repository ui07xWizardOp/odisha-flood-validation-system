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
        """Load trained MobileNetV2 model or fallback to pretrained."""
        try:
            # Check if model file exists
            # Load weights if available
            model_path = "models/flood_cnn_v2.pth"  # Updated to v2 model
            
            if Path(model_path).exists():
                # Reconstruct the model architecture (matches v2 training)
                self.model = models.mobilenet_v2(weights=None) 
                self.model.classifier = nn.Sequential(
                    nn.Dropout(0.3),
                    nn.Linear(1280, 256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, 1),
                    nn.Sigmoid()
                )
                
                state_dict = torch.load(model_path, map_location=torch.device('cpu'))
                self.model.load_state_dict(state_dict)
                logger.info(f"Loaded custom flood model from {model_path}")
            else:
                logger.warning(f"Custom model not found at {model_path}. Disabling DL component.")
                # Do NOT load random model. Set to None so we fall back to OpenCV.
                self.model = None

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
        
        Uses a combination of:
        1. Deep learning features (if PyTorch available)
        2. Color-based water detection (if OpenCV available)
        
        Note: Both methods must agree for positive classification to reduce false positives.
        """
        water_ratio = 0.0
        is_flood = False
        confidence = 0.5
        model_used = "Heuristic"
        dl_confidence = 0.0
        
        # Step 1: OpenCV water detection (always try first if available)
        if CV2_AVAILABLE:
            water_ratio = self._detect_water_ratio(image_data)
            model_used = "OpenCV-Water"
            
            # INCREASED thresholds to reduce false positives
            # Water coverage based classification (conservative)
            if water_ratio > 0.35:  # Was 0.3 - require significant water
                is_flood = True
                confidence = min(0.6 + water_ratio, 0.95)
            elif water_ratio > 0.25:  # Was 0.15 - moderate water
                is_flood = True
                confidence = 0.5 + water_ratio
            else:
                is_flood = False
                confidence = 0.7  # More confident it's NOT flood
        
        # Step 2: Deep learning refinement (if available)
        if TORCH_AVAILABLE and self.model is not None:
            try:
                dl_result = self._deep_learning_predict(image_data)
                dl_confidence = dl_result['confidence']
                
                # STRICTER: Require BOTH high DL confidence AND visible water
                if dl_confidence > 0.7:  # Was 0.5 - require higher CNN confidence
                    if water_ratio > 0.2:  # Was 0.1 - require visible water
                        is_flood = True
                        confidence = (dl_confidence + water_ratio) / 2 + 0.3
                        confidence = min(confidence, 0.95)
                    else:
                        # DL says flood but no visible water - be cautious
                        is_flood = dl_confidence > 0.85  # Only if very confident
                        confidence = dl_confidence * 0.8  # Reduce confidence
                    model_used = "MobileNetV2+OpenCV"
                elif dl_confidence < 0.3:
                    # DL is confident it's NOT flood - trust it
                    is_flood = False
                    confidence = max(confidence, 1 - dl_confidence)
                    model_used = "MobileNetV2+OpenCV"
                    
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
        Use color analysis to estimate water coverage in image.
        Detects:
        - Blue water (clear)
        - Brown/muddy water (flood water)
        - Dark reflective surfaces (standing water)
        """
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 0.0
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Define water color ranges
            # Blue water
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            
            # Brown/muddy water (common in floods)
            lower_brown = np.array([10, 50, 50])
            upper_brown = np.array([30, 200, 200])
            
            # Gray/dark (reflective standing water)
            lower_gray = np.array([0, 0, 40])
            upper_gray = np.array([180, 50, 120])
            
            # Create masks
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
            gray_mask = cv2.inRange(hsv, lower_gray, upper_gray)
            
            # Combine masks with weights
            # Blue and brown are more indicative of flood
            water_mask = cv2.bitwise_or(blue_mask, brown_mask)
            
            # Calculate ratios
            total_pixels = img.shape[0] * img.shape[1]
            water_pixels = np.sum(water_mask > 0)
            gray_pixels = np.sum(gray_mask > 0)
            
            # Weight: blue/brown water counts more than gray
            water_ratio = (water_pixels + gray_pixels * 0.3) / total_pixels
            
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
