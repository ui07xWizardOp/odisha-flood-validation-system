"""
Generate Synthetic Flood Dataset for Pipeline Verification.
Creates random noise/pattern images to test CNN training script.
"""

from PIL import Image, ImageDraw
import random
from pathlib import Path
import os

def create_synthetic_data(count=50):
    base_dir = Path("data/flood_images")
    flood_dir = base_dir / "flood"
    not_flood_dir = base_dir / "not_flood"
    
    flood_dir.mkdir(parents=True, exist_ok=True)
    not_flood_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {count*2} synthetic images...")
    
    # Generate "Flood" images (Blue tint)
    for i in range(count):
        img = Image.new('RGB', (224, 224), color=(0, 0, random.randint(100, 255)))
        draw = ImageDraw.Draw(img)
        # Add some "water" waves
        for _ in range(5):
            y = random.randint(0, 224)
            draw.line([(0, y), (224, y)], fill=(200, 200, 255), width=2)
        img.save(flood_dir / f"flood_{i}.jpg")
    
    # Generate "Not Flood" images (Green/Brown tint)
    for i in range(count):
        img = Image.new('RGB', (224, 224), color=(random.randint(0, 100), random.randint(100, 255), 0))
        draw = ImageDraw.Draw(img)
        # Add some "land" features
        for _ in range(5):
            x = random.randint(0, 224)
            draw.rectangle([x, x, x+20, x+20], fill=(139, 69, 19))
        img.save(not_flood_dir / f"normal_{i}.jpg")

    print("Synthetic generation complete.")

if __name__ == "__main__":
    create_synthetic_data()
