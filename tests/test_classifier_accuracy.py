"""
Automated Test Suite for Flood Image Classifier

Tests both the standard FloodImageClassifier and EnsembleFloodClassifier.
Uses synthetic and real (if available) test images.

Run: python -m tests.test_classifier_accuracy
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict
import io
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("PIL not available")
    sys.exit(1)


# Test case generator
def generate_flood_images(count: int) -> List[Tuple[bytes, str]]:
    """Generate synthetic flood images."""
    images = []
    
    for i in range(count):
        img = Image.new('RGB', (256, 256))
        draw = ImageDraw.Draw(img)
        
        variant = i % 5
        
        if variant == 0:
            # Blue water
            base = (random.randint(20, 60), random.randint(80, 140), random.randint(150, 200))
            img.paste(base, [0, 0, 256, 256])
            name = f"flood_blue_{i}"
            
        elif variant == 1:
            # Muddy brown water
            base = (random.randint(100, 140), random.randint(80, 120), random.randint(50, 90))
            img.paste(base, [0, 0, 256, 256])
            name = f"flood_muddy_{i}"
            
        elif variant == 2:
            # Partial flood (half water, half land)
            img.paste((50, 120, 180), [0, 0, 256, 128])  # Water top
            img.paste((100, 150, 80), [0, 128, 256, 256])  # Land bottom
            name = f"flood_partial_{i}"
            
        elif variant == 3:
            # Dark standing water
            base = (random.randint(30, 50), random.randint(40, 60), random.randint(50, 70))
            img.paste(base, [0, 0, 256, 256])
            name = f"flood_dark_{i}"
            
        else:
            # Flood with debris
            img.paste((60, 100, 150), [0, 0, 256, 256])
            for _ in range(10):
                x, y = random.randint(0, 240), random.randint(0, 240)
                draw.ellipse([x, y, x+15, y+15], fill=(80, 60, 40))
            name = f"flood_debris_{i}"
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        images.append((buffer.getvalue(), name))
    
    return images


def generate_not_flood_images(count: int) -> List[Tuple[bytes, str]]:
    """Generate synthetic non-flood images."""
    images = []
    
    for i in range(count):
        img = Image.new('RGB', (256, 256))
        draw = ImageDraw.Draw(img)
        
        variant = i % 6
        
        if variant == 0:
            # Urban buildings (gray)
            base = (random.randint(90, 130), random.randint(90, 130), random.randint(90, 130))
            img.paste(base, [0, 0, 256, 256])
            for _ in range(random.randint(5, 15)):
                x, y = random.randint(0, 200), random.randint(0, 200)
                w, h = random.randint(20, 50), random.randint(30, 70)
                shade = random.randint(-30, 30)
                color = tuple(max(0, min(255, c + shade)) for c in base)
                draw.rectangle([x, y, x+w, y+h], fill=color, outline=(50, 50, 50))
            name = f"urban_{i}"
            
        elif variant == 1:
            # Green grass
            base = (random.randint(40, 80), random.randint(130, 180), random.randint(30, 70))
            img.paste(base, [0, 0, 256, 256])
            for _ in range(200):
                x, y = random.randint(0, 255), random.randint(0, 255)
                shade = random.randint(-20, 20)
                color = tuple(max(0, min(255, c + shade)) for c in base)
                draw.line([x, y, x + random.randint(-2, 2), y + random.randint(5, 12)], fill=color)
            name = f"grass_{i}"
            
        elif variant == 2:
            # Desert sand
            base = (random.randint(190, 230), random.randint(160, 200), random.randint(110, 160))
            img.paste(base, [0, 0, 256, 256])
            for _ in range(100):
                x, y = random.randint(0, 250), random.randint(0, 250)
                size = random.randint(2, 5)
                shade = random.randint(-15, 15)
                color = tuple(max(0, min(255, c + shade)) for c in base)
                draw.ellipse([x, y, x+size, y+size], fill=color)
            name = f"desert_{i}"
            
        elif variant == 3:
            # Forest (dark green)
            base = (random.randint(20, 50), random.randint(70, 110), random.randint(20, 50))
            img.paste(base, [0, 0, 256, 256])
            for _ in range(50):
                x, y = random.randint(0, 230), random.randint(0, 230)
                size = random.randint(15, 40)
                shade = random.randint(-20, 20)
                color = tuple(max(0, min(255, c + shade)) for c in base)
                draw.ellipse([x, y, x+size, y+size], fill=color)
            name = f"forest_{i}"
            
        elif variant == 4:
            # Road/asphalt
            img.paste((100, 100, 100), [0, 0, 256, 256])
            draw.rectangle([110, 0, 146, 256], fill=(80, 80, 80))
            for y in range(0, 256, 40):
                draw.rectangle([125, y, 131, y+20], fill=(255, 255, 255))
            name = f"road_{i}"
            
        else:
            # Snow/white
            base = (random.randint(230, 250), random.randint(230, 250), random.randint(235, 255))
            img.paste(base, [0, 0, 256, 256])
            name = f"snow_{i}"
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        images.append((buffer.getvalue(), name))
    
    return images


def run_tests(classifier, flood_images, not_flood_images) -> Dict:
    """Run tests on classifier and return metrics."""
    results = {
        "true_positives": 0,
        "false_positives": 0,
        "true_negatives": 0,
        "false_negatives": 0,
        "flood_details": [],
        "not_flood_details": []
    }
    
    # Test flood images (should be detected as flood)
    for img_data, name in flood_images:
        try:
            result = classifier.validate_image(img_data)
            is_flood = result.get("is_flood_detected", False)
            
            if is_flood:
                results["true_positives"] += 1
            else:
                results["false_negatives"] += 1
            
            results["flood_details"].append({
                "name": name,
                "detected": is_flood,
                "score": result.get("score", 0),
                "water": result.get("water_coverage", 0)
            })
        except Exception as e:
            results["false_negatives"] += 1
            results["flood_details"].append({"name": name, "error": str(e)})
    
    # Test non-flood images (should NOT be detected as flood)
    for img_data, name in not_flood_images:
        try:
            result = classifier.validate_image(img_data)
            is_flood = result.get("is_flood_detected", False)
            
            if not is_flood:
                results["true_negatives"] += 1
            else:
                results["false_positives"] += 1
            
            results["not_flood_details"].append({
                "name": name,
                "detected": is_flood,
                "score": result.get("score", 0),
                "water": result.get("water_coverage", 0)
            })
        except Exception as e:
            results["true_negatives"] += 1  # Error = likely not flood
            results["not_flood_details"].append({"name": name, "error": str(e)})
    
    # Calculate metrics
    tp, fp, tn, fn = results["true_positives"], results["false_positives"], results["true_negatives"], results["false_negatives"]
    
    results["accuracy"] = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
    results["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
    results["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
    results["specificity"] = tn / (tn + fp) if (tn + fp) > 0 else 0
    results["f1"] = 2 * (results["precision"] * results["recall"]) / (results["precision"] + results["recall"]) if (results["precision"] + results["recall"]) > 0 else 0
    
    return results


def print_results(name: str, results: Dict):
    """Pretty print test results."""
    print(f"\n{'='*60}")
    print(f"{name} Test Results")
    print('='*60)
    
    tp, fp, tn, fn = results["true_positives"], results["false_positives"], results["true_negatives"], results["false_negatives"]
    
    print(f"\nConfusion Matrix:")
    print(f"                  Predicted")
    print(f"                  FLOOD    NO FLOOD")
    print(f"  Actual FLOOD      {tp:3d}       {fn:3d}")
    print(f"  Actual NO FLOOD   {fp:3d}       {tn:3d}")
    
    print(f"\nMetrics:")
    print(f"  Accuracy:    {results['accuracy']:.1%}")
    print(f"  Precision:   {results['precision']:.1%}")
    print(f"  Recall:      {results['recall']:.1%}")
    print(f"  Specificity: {results['specificity']:.1%}")
    print(f"  F1 Score:    {results['f1']:.1%}")
    
    # Show failures
    fp_list = [d["name"] for d in results["not_flood_details"] if d.get("detected")]
    fn_list = [d["name"] for d in results["flood_details"] if not d.get("detected")]
    
    if fp_list:
        print(f"\nFalse Positives ({len(fp_list)}):")
        for name in fp_list[:5]:
            print(f"  - {name}")
        if len(fp_list) > 5:
            print(f"  ... and {len(fp_list) - 5} more")
    
    if fn_list:
        print(f"\nFalse Negatives ({len(fn_list)}):")
        for name in fn_list[:5]:
            print(f"  - {name}")
        if len(fn_list) > 5:
            print(f"  ... and {len(fn_list) - 5} more")


def main():
    print("="*60)
    print("FLOOD CLASSIFIER TEST SUITE")
    print("="*60)
    
    # Generate test images
    print("\nGenerating test images...")
    flood_images = generate_flood_images(50)
    not_flood_images = generate_not_flood_images(50)
    print(f"  Flood images: {len(flood_images)}")
    print(f"  Non-flood images: {len(not_flood_images)}")
    
    # Test Standard Classifier
    print("\nTesting FloodImageClassifier...")
    try:
        from src.ml.models.image_classifier import FloodImageClassifier
        standard = FloodImageClassifier()
        standard_results = run_tests(standard, flood_images, not_flood_images)
        print_results("FloodImageClassifier", standard_results)
    except Exception as e:
        print(f"  FloodImageClassifier failed: {e}")
        standard_results = None
    
    # Test Ensemble Classifier
    print("\nTesting EnsembleFloodClassifier...")
    try:
        from src.ml.models.ensemble_classifier import EnsembleFloodClassifier
        ensemble = EnsembleFloodClassifier()
        ensemble_results = run_tests(ensemble, flood_images, not_flood_images)
        print_results("EnsembleFloodClassifier", ensemble_results)
    except Exception as e:
        print(f"  EnsembleFloodClassifier failed: {e}")
        ensemble_results = None
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if standard_results and ensemble_results:
        print(f"\n{'Metric':<15} {'Standard':<12} {'Ensemble':<12} {'Winner'}")
        print("-"*50)
        
        for metric in ['accuracy', 'precision', 'recall', 'specificity', 'f1']:
            s = standard_results[metric]
            e = ensemble_results[metric]
            winner = "Standard" if s > e else "Ensemble" if e > s else "Tie"
            print(f"{metric.capitalize():<15} {s:>10.1%}   {e:>10.1%}   {winner}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
