"""
Balanced Dataset Preparation for Flood Classifier

Downloads and organizes images for training:
- Flood images: From existing Kaggle dataset (already have)
- Non-flood images: Urban, green spaces, desert scenes

Sources for negative samples (all public/free):
1. Unsplash API (free tier)
2. Places365 mini dataset
3. Synthetic generation

Output structure:
    data/balanced_flood_dataset/
        flood/
            img_001.jpg
            ...
        not_flood/
            urban_001.jpg
            green_001.jpg
            desert_001.jpg
            ...
"""

import os
import sys
import shutil
import requests
from pathlib import Path
from PIL import Image
import io
import random

# Configuration
OUTPUT_DIR = Path("data/balanced_flood_dataset")
FLOOD_DIR = OUTPUT_DIR / "flood"
NOT_FLOOD_DIR = OUTPUT_DIR / "not_flood"

# Target: 500 flood + 500 not-flood
TARGET_FLOOD = 500
TARGET_NOT_FLOOD = 500

# Unsplash API (free tier - 50 req/hour)
# Get your key at: https://unsplash.com/developers
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

def ensure_directories():
    """Create output directories."""
    FLOOD_DIR.mkdir(parents=True, exist_ok=True)
    NOT_FLOOD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output directories ready: {OUTPUT_DIR}")

def count_existing():
    """Count existing images."""
    flood_count = len(list(FLOOD_DIR.glob("*.jpg"))) + len(list(FLOOD_DIR.glob("*.png")))
    not_flood_count = len(list(NOT_FLOOD_DIR.glob("*.jpg"))) + len(list(NOT_FLOOD_DIR.glob("*.png")))
    return flood_count, not_flood_count

def download_unsplash_images(query, count, prefix, output_dir):
    """Download images from Unsplash API."""
    if not UNSPLASH_ACCESS_KEY:
        print(f"[SKIP] Unsplash: No API key. Set UNSPLASH_ACCESS_KEY environment variable.")
        return 0
    
    downloaded = 0
    page = 1
    
    while downloaded < count:
        url = f"https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": 30,
            "page": page,
            "client_id": UNSPLASH_ACCESS_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get("results", []):
                if downloaded >= count:
                    break
                
                img_url = result["urls"]["small"]
                img_response = requests.get(img_url, timeout=30)
                
                if img_response.status_code == 200:
                    filename = f"{prefix}_{downloaded+1:04d}.jpg"
                    filepath = output_dir / filename
                    
                    with open(filepath, "wb") as f:
                        f.write(img_response.content)
                    
                    downloaded += 1
                    
            page += 1
            
            if page > 10:  # Limit to 10 pages
                break
                
        except Exception as e:
            print(f"  [ERROR] Unsplash request failed: {e}")
            break
    
    print(f"  Downloaded {downloaded} images for '{query}'")
    return downloaded

def generate_synthetic_negatives(count, output_dir):
    """Generate synthetic non-flood images."""
    from PIL import ImageDraw
    import numpy as np
    
    generated = 0
    categories = ["urban", "grass", "desert", "forest", "road"]
    
    for i in range(count):
        category = random.choice(categories)
        img = Image.new('RGB', (256, 256))
        draw = ImageDraw.Draw(img)
        
        if category == "urban":
            # Gray buildings with rectangles
            base_color = (random.randint(80, 130), random.randint(80, 130), random.randint(80, 130))
            img.paste(base_color, [0, 0, 256, 256])
            for _ in range(random.randint(5, 15)):
                x1, y1 = random.randint(0, 200), random.randint(0, 200)
                x2, y2 = x1 + random.randint(20, 60), y1 + random.randint(30, 80)
                shade = random.randint(-30, 30)
                color = tuple(max(0, min(255, c + shade)) for c in base_color)
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(50, 50, 50))
                
        elif category == "grass":
            # Green with texture
            base_color = (random.randint(40, 80), random.randint(120, 180), random.randint(30, 70))
            img.paste(base_color, [0, 0, 256, 256])
            for _ in range(200):
                x, y = random.randint(0, 255), random.randint(0, 255)
                shade = random.randint(-20, 20)
                color = tuple(max(0, min(255, c + shade)) for c in base_color)
                draw.line([x, y, x + random.randint(-3, 3), y + random.randint(5, 15)], fill=color, width=1)
                
        elif category == "desert":
            # Sandy/brown
            base_color = (random.randint(180, 220), random.randint(150, 190), random.randint(100, 150))
            img.paste(base_color, [0, 0, 256, 256])
            for _ in range(100):
                x, y = random.randint(0, 255), random.randint(0, 255)
                size = random.randint(2, 5)
                shade = random.randint(-15, 15)
                color = tuple(max(0, min(255, c + shade)) for c in base_color)
                draw.ellipse([x, y, x+size, y+size], fill=color)
                
        elif category == "forest":
            # Dark green with variation
            base_color = (random.randint(20, 50), random.randint(60, 100), random.randint(20, 50))
            img.paste(base_color, [0, 0, 256, 256])
            for _ in range(50):
                x, y = random.randint(0, 230), random.randint(0, 230)
                size = random.randint(10, 30)
                shade = random.randint(-20, 20)
                color = tuple(max(0, min(255, c + shade)) for c in base_color)
                draw.ellipse([x, y, x+size, y+size], fill=color)
                
        elif category == "road":
            # Gray road with markings
            img.paste((100, 100, 100), [0, 0, 256, 256])
            draw.rectangle([110, 0, 146, 256], fill=(80, 80, 80))
            for y in range(0, 256, 40):
                draw.rectangle([125, y, 131, y+20], fill=(255, 255, 255))
        
        filename = f"synthetic_{category}_{i+1:04d}.jpg"
        img.save(output_dir / filename, "JPEG")
        generated += 1
    
    print(f"  Generated {generated} synthetic non-flood images")
    return generated

def copy_existing_flood_images():
    """Copy flood images from Kaggle dataset."""
    # Check various possible locations
    kaggle_dirs = [
        Path("data/Image"),
        Path("data/images"),
        Path("data/flood_images/flood"),
        Path("data/balanced_flood_dataset/flood"),  # Already copied
    ]
    
    flood_images = []
    for d in kaggle_dirs:
        if d.exists():
            flood_images.extend(list(d.glob("*.jpg")))
            flood_images.extend(list(d.glob("*.png")))
    
    if not flood_images:
        print("[WARN] No existing flood images found. Please download Kaggle dataset:")
        print("       kaggle datasets download -d faizalkarim/flood-area-segmentation")
        return 0
    
    copied = 0
    for i, img_path in enumerate(flood_images[:TARGET_FLOOD]):
        dest = FLOOD_DIR / f"flood_{i+1:04d}.jpg"
        if not dest.exists():
            shutil.copy(img_path, dest)
            copied += 1
    
    print(f"  Copied {copied} flood images")
    return copied

def main():
    print("=" * 60)
    print("BALANCED DATASET PREPARATION")
    print("=" * 60)
    
    ensure_directories()
    
    flood_count, not_flood_count = count_existing()
    print(f"\nCurrent counts: {flood_count} flood, {not_flood_count} not-flood")
    
    # Step 1: Copy/download flood images
    print("\n--- Step 1: Flood Images ---")
    if flood_count < TARGET_FLOOD:
        needed = TARGET_FLOOD - flood_count
        print(f"  Need {needed} more flood images")
        copy_existing_flood_images()
    else:
        print(f"  [OK] Have enough flood images ({flood_count})")
    
    # Step 2: Download/generate non-flood images
    print("\n--- Step 2: Non-Flood Images ---")
    not_flood_count = len(list(NOT_FLOOD_DIR.glob("*")))
    
    if not_flood_count < TARGET_NOT_FLOOD:
        needed = TARGET_NOT_FLOOD - not_flood_count
        print(f"  Need {needed} more non-flood images")
        
        # Try Unsplash first
        if UNSPLASH_ACCESS_KEY:
            queries = [
                ("city buildings street", 50, "urban"),
                ("green grass field", 50, "grass"),
                ("desert sand dry", 30, "desert"),
                ("forest trees", 30, "forest"),
                ("highway road asphalt", 30, "road"),
            ]
            
            for query, count, prefix in queries:
                download_unsplash_images(query, count, prefix, NOT_FLOOD_DIR)
        
        # Generate synthetic to fill remainder
        not_flood_count = len(list(NOT_FLOOD_DIR.glob("*")))
        if not_flood_count < TARGET_NOT_FLOOD:
            remaining = TARGET_NOT_FLOOD - not_flood_count
            print(f"  Generating {remaining} synthetic images...")
            generate_synthetic_negatives(remaining, NOT_FLOOD_DIR)
    else:
        print(f"  [OK] Have enough non-flood images ({not_flood_count})")
    
    # Final count
    print("\n" + "=" * 60)
    flood_count, not_flood_count = count_existing()
    print(f"FINAL COUNTS:")
    print(f"  Flood: {flood_count}")
    print(f"  Not-Flood: {not_flood_count}")
    print(f"  Total: {flood_count + not_flood_count}")
    print(f"  Balance: {flood_count/(flood_count + not_flood_count)*100:.1f}% flood")
    print("=" * 60)

if __name__ == "__main__":
    main()
