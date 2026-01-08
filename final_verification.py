import sys
import os
import io
import random
from PIL import Image, ImageDraw
import traceback

sys.path.insert(0, '.')
from src.ml.models.ensemble_classifier import ensemble_classifier

# 1. Config
TEST_IMAGES = {
    "REAL_CityStreet_FP": "C:/Users/KIIT0001/.gemini/antigravity/brain/cec46f89-9db1-492a-a1e3-ba76da4e8440/uploaded_image_1767820905037.jpg",
    "REAL_WetStreet_FP": "C:/Users/KIIT0001/.gemini/antigravity/brain/cec46f89-9db1-492a-a1e3-ba76da4e8440/uploaded_image_1767817347277.png",
    "REAL_CarFlood_TP": "C:/Users/KIIT0001/.gemini/antigravity/brain/cec46f89-9db1-492a-a1e3-ba76da4e8440/uploaded_image_1767814790241.png"
}

EXPECTED = {
    "REAL_CityStreet_FP": False, # Expect NOT Flood
    "REAL_WetStreet_FP": False,  # Expect NOT Flood
    "REAL_CarFlood_TP": True,    # Expect FLOOD
    "SYN_Muddy_TP": True         # Expect FLOOD
}

def create_synthetic_muddy():
    """Create a muddy water image (Brown, Smooth)"""
    img = Image.new('RGB', (256, 256))
    # Muddy brown (Low Saturation Brown)
    base = (130, 110, 80)
    img.paste(base, [0, 0, 256, 256])
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def run_verification():
    print(f"{'TEST CASE':<20} | {'EXPECTED':<8} | {'ACTUAL':<8} | {'CONFIDENCE':<10} | {'DETAILS (CNN/Water/Tex)'}")
    print("-" * 100)
    
    passed = 0
    total = 0
    
    # 1. Real Images
    for name, path in TEST_IMAGES.items():
        total += 1
        if not os.path.exists(path):
            print(f"{name:<20} | {'???':<8} | {'ERR':<8} | {'N/A':<10} | File missing")
            continue
            
        with open(path, 'rb') as f:
            content = f.read()
            
        result = ensemble_classifier.predict(content)
        is_flood = result['is_flood']
        score = result['ensemble_score']
        input_scores = result.get('individual_scores', {})
        water_ratios = ensemble_classifier._get_water_ratio(content)
        extra_details = f"Blue:{water_ratios.get('blue',0):.2f} Brown:{water_ratios.get('brown',0):.2f}"
        
        status = "PASS" if is_flood == EXPECTED[name] else "FAIL"
        if status == "PASS": passed += 1
        
        print(f"{name:<20} | {str(EXPECTED[name]):<8} | {str(is_flood):<8} | {score:<10.4f} | {extra_details} -> {status}")

    # 2. Synthetic Muddy
    total += 1
    content = create_synthetic_muddy()
    result = ensemble_classifier.predict(content)
    is_flood = result['is_flood']
    score = result['ensemble_score']
    input_scores = result.get('individual_scores', {})
    details = f"C:{input_scores.get('cnn',0):.2f} W:{input_scores.get('water_ratio',0):.2f} T:{input_scores.get('texture',0):.2f}"
    status = "PASS" if is_flood == EXPECTED["SYN_Muddy_TP"] else "FAIL"
    if status == "PASS": passed += 1
    
    print(f"{'SYN_Muddy_TP':<20} | {str(EXPECTED['SYN_Muddy_TP']):<8} | {str(is_flood):<8} | {score:<10.4f} | {details} -> {status}")

    print("-" * 100)
    print(f"Overall Result: {passed}/{total} Passed")
    
    if passed == total:
        print("\n SYSTEM VERIFIED: All critical edge cases handled correctly.")
    else:
        print("\n VERIFICATION FAILED: Check logs.")

if __name__ == "__main__":
    run_verification()
