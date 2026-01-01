"""
Computer Vision Module for Flood Photo Validation.

Uses a lightweight CNN to classify user-submitted photos as:
- Flood (water visible, inundation)
- Not Flood (normal conditions)
- Invalid (blurry, irrelevant, inappropriate)
"""

import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging
import base64
import io

logger = logging.getLogger(__name__)

# Try to import TensorFlow, fall back to mock if unavailable
try:
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing import image as keras_image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available. Using mock CV predictions.")

# Try to import OpenCV for image processing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available. Water detection disabled.")


class FloodImageClassifier:
    """
    CNN-based classifier for flood photos.
    Uses MobileNetV2 as backbone (lightweight, works on CPU).
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        
        if TF_AVAILABLE:
            self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load pre-trained model or create new one."""
        if self.model_path and Path(self.model_path).exists():
            self.model = tf.keras.models.load_model(self.model_path)
            logger.info(f"Loaded model from {self.model_path}")
        else:
            # Create a simple binary classifier using MobileNetV2
            base_model = MobileNetV2(
                weights='imagenet',
                include_top=False,
                input_shape=(224, 224, 3)
            )
            base_model.trainable = False  # Freeze base
            
            self.model = tf.keras.Sequential([
                base_model,
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            logger.info("Created new MobileNetV2-based classifier")
    
    def predict(self, image_data: bytes) -> Dict:
        """
        Classify an image as flood/not-flood.
        
        Args:
            image_data: Raw image bytes (JPEG/PNG)
            
        Returns:
            Dict with 'is_flood', 'confidence', 'water_ratio'
        """
        if not TF_AVAILABLE:
            return self._mock_predict()
        
        try:
            # Decode image
            img_array = tf.image.decode_image(image_data, channels=3)
            img_array = tf.image.resize(img_array, (224, 224))
            img_array = preprocess_input(img_array)
            img_array = tf.expand_dims(img_array, 0)
            
            # Predict
            prediction = self.model.predict(img_array, verbose=0)[0][0]
            
            # Also analyze water content if OpenCV available
            water_ratio = self._detect_water_ratio(image_data) if CV2_AVAILABLE else 0.0
            
            return {
                "is_flood": prediction > 0.5,
                "confidence": float(prediction) if prediction > 0.5 else float(1 - prediction),
                "water_ratio": water_ratio,
                "model": "MobileNetV2"
            }
            
        except Exception as e:
            logger.error(f"Image prediction failed: {e}")
            return self._mock_predict()
    
    def _detect_water_ratio(self, image_data: bytes) -> float:
        """
        Use color analysis to estimate water coverage in image.
        Water typically appears as blue/dark blue pixels.
        """
        try:
            # Decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 0.0
            
            # Convert to HSV
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Define water color range (blue-ish)
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            
            # Also check for muddy water (brown)
            lower_brown = np.array([10, 50, 50])
            upper_brown = np.array([30, 200, 200])
            
            # Create masks
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
            water_mask = cv2.bitwise_or(blue_mask, brown_mask)
            
            # Calculate ratio
            total_pixels = img.shape[0] * img.shape[1]
            water_pixels = np.sum(water_mask > 0)
            
            return float(water_pixels / total_pixels)
            
        except Exception as e:
            logger.error(f"Water detection failed: {e}")
            return 0.0
    
    def _mock_predict(self) -> Dict:
        """Fallback mock prediction when TF not available."""
        return {
            "is_flood": False,
            "confidence": 0.5,
            "water_ratio": 0.0,
            "model": "Mock (TF not installed)"
        }
    
    def validate_image(self, image_data: bytes) -> Dict:
        """
        Full validation pipeline for a user-submitted image.
        
        Returns:
            Dict with validation result and score
        """
        # Basic checks
        if len(image_data) < 1000:  # Too small
            return {
                "valid": False,
                "score": 0.0,
                "reason": "Image too small",
                "details": {}
            }
        
        if len(image_data) > 10_000_000:  # Too large (>10MB)
            return {
                "valid": False,
                "score": 0.0,
                "reason": "Image too large",
                "details": {}
            }
        
        # Run prediction
        prediction = self.predict(image_data)
        
        # Calculate validation score
        score = 0.5  # Base score
        
        if prediction['is_flood']:
            score += 0.3
        
        if prediction['water_ratio'] > 0.2:
            score += 0.2
        
        return {
            "valid": True,
            "score": min(score, 1.0),
            "is_flood_detected": prediction['is_flood'],
            "confidence": prediction['confidence'],
            "water_coverage": prediction['water_ratio'],
            "model_used": prediction['model']
        }


# Singleton instance
flood_classifier = FloodImageClassifier()


if __name__ == "__main__":
    # Test with a sample image (if available)
    print("🖼️ Flood Image Classifier")
    print(f"   TensorFlow available: {TF_AVAILABLE}")
    print(f"   OpenCV available: {CV2_AVAILABLE}")
    
    # Mock test
    result = flood_classifier._mock_predict()
    print(f"   Mock prediction: {result}")
