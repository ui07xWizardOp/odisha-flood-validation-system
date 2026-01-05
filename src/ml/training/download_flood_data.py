"""
Download Sample Flood Dataset.

Downloads flood and non-flood images from public GitHub repositories
to facilitate testing of the CNN training pipeline.
"""

import requests
import logging
from pathlib import Path
import concurrent.futures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample image URLs from public domain / open sources
# Using placeholder URLs from a stable GitHub dataset if possible, 
# or reliable picsum/wikipedia sources for demo purposes.
# For this "System Check", we will use a diverse set of images.

FLOOD_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Flood1_Gneiss.jpg/640px-Flood1_Gneiss.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Flooded_street_in_New_Orleans_after_Hurricane_Katrina.jpg/640px-Flooded_street_in_New_Orleans_after_Hurricane_Katrina.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Flood_in_faisalabad.jpg/640px-Flood_in_faisalabad.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Flooding_in_Steyr_2013.jpg/640px-Flooding_in_Steyr_2013.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Flood_damage_caused_by_Hurricane_Sandy_in_Staten_Island.jpg/640px-Flood_damage_caused_by_Hurricane_Sandy_in_Staten_Island.jpg",
    "https://live.staticflickr.com/5443/9363063541_583858348e_b.jpg",
    "https://live.staticflickr.com/2852/9363062325_2f788176e5_b.jpg",
    "https://live.staticflickr.com/7438/9365842816_1250275880_b.jpg"
] * 5  # Duplicate to create a larger "dataset"

NOT_FLOOD_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Clouds_over_the_Atlantic_Ocean.jpg/640px-Clouds_over_the_Atlantic_Ocean.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Altja_j%C3%B5gi_Lahemaal.jpg/640px-Altja_j%C3%B5gi_Lahemaal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Green_fields.jpg/640px-Green_fields.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Street_in_New_Orleans.jpg/640px-Street_in_New_Orleans.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/City_street_in_Amsterdam.jpg/640px-City_street_in_Amsterdam.jpg",
    "https://live.staticflickr.com/3757/12437632615_d840ae0bd6_b.jpg",
    "https://live.staticflickr.com/7360/12438132934_6e53a3e9c4_b.jpg",
    "https://live.staticflickr.com/2873/12438131334_6f5407077f_b.jpg"
] * 5

def download_image(url: str, save_path: Path):
    """Download a single image."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return False

def download_dataset():
    """Download the dataset."""
    base_dir = Path("data/flood_images")
    flood_dir = base_dir / "flood"
    not_flood_dir = base_dir / "not_flood"
    
    flood_dir.mkdir(parents=True, exist_ok=True)
    not_flood_dir.mkdir(parents=True, exist_ok=True)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Download flood images
        futures = []
        for i, url in enumerate(FLOOD_URLS):
            save_path = flood_dir / f"flood_{i}.jpg"
            if not save_path.exists():
                futures.append(executor.submit(download_image, url, save_path))
        
        # Download non-flood images
        for i, url in enumerate(NOT_FLOOD_URLS):
            save_path = not_flood_dir / f"normal_{i}.jpg"
            if not save_path.exists():
                futures.append(executor.submit(download_image, url, save_path))
        
        # Wait for completion
        results = [f.result() for f in futures]
        success_count = sum(results)
    
    logger.info(f"Downloaded {success_count} images")

if __name__ == "__main__":
    download_dataset()
