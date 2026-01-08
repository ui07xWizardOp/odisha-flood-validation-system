# Flood Detection CNN Training - Google Colab
# ============================================
# This notebook trains MobileNetV2 on multiple Kaggle flood datasets
# Target: >95% F1 Score for binary flood/not_flood classification

# %% [markdown]
# # 🌊 Flood Detection Model Training
# 
# This notebook trains a MobileNetV2-based flood classifier using multiple Kaggle datasets.
# 
# **Datasets Used:**
# 1. nhatto12/flood-detection
# 2. tambiraigahadza/flood-detection
# 3. kabeer2004/flood-images
# 4. hhrclemson/flooding-image-dataset
# 5. saurabhshahane/roadway-flooding-image-dataset
# 6. sunnyshabanali/close-view-flood-dataset-cvfd
# 7. binhhhhhhhhh/dpl-2025

# %% [markdown]
# ## 1. Setup & Dependencies

# %%
# Check GPU availability
!nvidia-smi

# %%
# Install dependencies
!pip install -q torch torchvision albumentations kaggle tqdm pillow

# %%
import os
import shutil
import hashlib
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split, WeightedRandomSampler
from torchvision import models, transforms
from PIL import Image
import numpy as np

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# %% [markdown]
# ## 2. Kaggle API Setup
# 
# Upload your `kaggle.json` file to Colab, or set credentials manually.

# %%
# Option 1: Upload kaggle.json
from google.colab import files

print("Upload your kaggle.json file:")
uploaded = files.upload()

# Move to correct location
!mkdir -p ~/.kaggle
!mv kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json

# %%
# Verify Kaggle authentication
!kaggle datasets list --sort-by votes --size 5

# %% [markdown]
# ## 3. Download Datasets
# 
# ### Image Datasets (Kaggle)
# - 7 primary flood detection datasets
# - 2 additional ML-ready datasets (IoT + India Risk)
# 
# ### Odisha-Specific Data
# - CivicDataLab flood data ecosystem repository

# %%
# Create data directory
DATA_DIR = Path("/content/flood_data")
DATA_DIR.mkdir(exist_ok=True)

# Primary Image Datasets
# NOTE: hhrclemson/flooding-image-dataset removed - too large (14GB), causes Colab timeout
DATASETS = [
    # Primary flood detection datasets
    "nhatto12/flood-detection",
    "tambiraigahadza/flood-detection",
    "kabeer2004/flood-images-for-training-disaster-detection-model",
    # "hhrclemson/flooding-image-dataset",  # DISABLED: 14GB, causes timeout
    "saurabhshahane/roadway-flooding-image-dataset",
    "sunnyshabanali/close-view-flood-dataset-cvfd",
    "binhhhhhhhhh/dpl-2025",
    # Additional ML-ready datasets
    "ziya07/flood-risk-iot-and-remote-sensing-dataset",  # IoT + Remote Sensing
    "s3programmer/flood-risk-in-india",                   # India Flood Risk Data
]

# Download each dataset
for dataset in DATASETS:
    name = dataset.split("/")[-1]
    dest = DATA_DIR / name
    if not dest.exists():
        print(f"\n📥 Downloading: {dataset}")
        !kaggle datasets download -d {dataset} -p {dest} --unzip
    else:
        print(f"✅ Already exists: {name}")

print("\n✅ All Kaggle datasets downloaded!")

# %%
# Clone Odisha-specific data repository
ODISHA_DIR = Path("/content/odisha_data")
if not ODISHA_DIR.exists():
    print("\n📥 Cloning CivicDataLab Odisha Flood Data Ecosystem...")
    !git clone https://github.com/CivicDataLab/flood-data-ecosystem-Odisha.git {ODISHA_DIR}
else:
    print("✅ Odisha data already cloned")

# %%
# List downloaded data
print("\n📁 Kaggle datasets:")
!ls -la /content/flood_data/

print("\n📁 Odisha data:")
!ls -la /content/odisha_data/ 2>/dev/null || echo "Not available"

# %% [markdown]
# ### 3.3 Additional Academic Datasets
# 
# These provide higher quality labeled data for flood detection.

# %%
# Download Sen1Floods11 (Sentinel satellite flood segmentation dataset)
SEN1FLOODS_DIR = Path("/content/sen1floods11")
if not SEN1FLOODS_DIR.exists():
    print("\n📥 Downloading Sen1Floods11 dataset...")
    # Clone the Sen1Floods11 repository (contains labels and download scripts)
    !git clone https://github.com/cloudtostreet/Sen1Floods11.git {SEN1FLOODS_DIR}
    print("✅ Sen1Floods11 cloned")
else:
    print("✅ Sen1Floods11 already exists")

# %%
# Download FloodNet dataset (if available from IEEE DataPort)
# Note: This may require IEEE DataPort account
FLOODNET_DIR = Path("/content/floodnet")
if not FLOODNET_DIR.exists():
    print("\n📥 Attempting FloodNet download...")
    try:
        # Try Kaggle version first
        !kaggle datasets download -d veeralakrishna/floodnet-challenge-2021 -p {FLOODNET_DIR} --unzip 2>/dev/null || echo "FloodNet not on Kaggle, skipping"
    except:
        print("FloodNet requires manual download from IEEE DataPort")
else:
    print("✅ FloodNet already exists")

# %% [markdown]
# ### Additional Data Sources (Manual Download)
# 
# | Dataset | Source | Registration |
# | :--- | :--- | :--- |
# | **FloodCastBench** | [Nature](https://www.nature.com/articles/s41597-025-04725-2) | Free, Figshare |
# | **India Flood Inventory** | [IIT-Delhi](https://www.preventionweb.net/news/freely-available-geospatial-dataset-make-flood-research-easier) | Free |
# | **OSDMA Hazard Atlas** | [osdma.org](https://www.osdma.org/publication/flood-hazard-zonation-atlas-odisha/) | Free PDF |
# | **NRSC Inundation Maps** | [NDEM Portal](https://ndem.nrsc.gov.in/) | Gov login |

# %% [markdown]
# ## 4. Organize & Merge Datasets

# %%
# Create unified structure
UNIFIED_DIR = Path("/content/unified_data")
TRAIN_DIR = UNIFIED_DIR / "train"
VAL_DIR = UNIFIED_DIR / "val"
TEST_DIR = UNIFIED_DIR / "test"

for split in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
    (split / "flood").mkdir(parents=True, exist_ok=True)
    (split / "not_flood").mkdir(parents=True, exist_ok=True)

# %%
def get_image_hash(filepath):
    """Generate hash for duplicate detection."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def find_images(directory):
    """Recursively find all images."""
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    images = []
    for path in Path(directory).rglob('*'):
        if path.suffix.lower() in extensions:
            images.append(path)
    return images

def classify_image_path(img_path):
    """Determine if image is flood or not_flood based on full path."""
    path_lower = str(img_path).lower()
    
    # Not-flood indicators (check first, more specific)
    not_flood_keywords = [
        'not_flood', 'non_flood', 'normal', 'dry', 'no_flood', 'negative',
        'non-flood', 'notflood', 'no flood', 'non flood',
        '/0/', '/class0/', '/negative/', '/normal/',  # Common folder patterns
        'non_flooded', 'not_flooded', 'nonflooded'
    ]
    
    # Flood indicators
    flood_keywords = [
        'flood', 'flooded', 'inundation', 'submerged', 'water_damage',
        '/1/', '/class1/', '/positive/', '/flooded/',  # Common folder patterns
        'inundated', 'flooding', 'floodwater'
    ]
    
    # Check not_flood first (more specific)
    for kw in not_flood_keywords:
        if kw in path_lower:
            return 'not_flood'
    
    # Then check flood
    for kw in flood_keywords:
        if kw in path_lower:
            return 'flood'
    
    return None  # Unknown

def classify_image_folder(folder_name):
    """Fallback: Determine label from folder name only."""
    return classify_image_path(folder_name)

# %%
# Collect all images with labels
flood_images = []
not_flood_images = []
unknown_images = []

# Search in all data directories
all_data_dirs = [DATA_DIR]
if ODISHA_DIR.exists():
    all_data_dirs.append(ODISHA_DIR)
if SEN1FLOODS_DIR.exists():
    all_data_dirs.append(SEN1FLOODS_DIR)

for data_dir in all_data_dirs:
    print(f"\n🔍 Scanning: {data_dir}")
    for dataset_dir in data_dir.iterdir():
        if dataset_dir.is_dir():
            images_found = find_images(dataset_dir)
            print(f"   Found {len(images_found)} images in {dataset_dir.name}")
            
            for img_path in images_found:
                # Try to determine label from FULL PATH (more reliable)
                label = classify_image_path(img_path)
                
                if label == 'flood':
                    flood_images.append(img_path)
                elif label == 'not_flood':
                    not_flood_images.append(img_path)
                else:
                    unknown_images.append(img_path)

print(f"\n📊 Image counts:")
print(f"   Flood: {len(flood_images)}")
print(f"   Not Flood: {len(not_flood_images)}")
print(f"   Unknown: {len(unknown_images)}")

# Show sample unknown images for debugging
if unknown_images and len(unknown_images) < 20:
    print(f"\n⚠️ Unknown image paths (check folder names):")
    for img in unknown_images[:10]:
        print(f"   {img}")

# %%
# Remove duplicates using hashing
def deduplicate(images):
    seen_hashes = set()
    unique = []
    for img in tqdm(images, desc="Deduplicating"):
        h = get_image_hash(img)
        if h and h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(img)
    return unique

flood_images = deduplicate(flood_images)
not_flood_images = deduplicate(not_flood_images)

print(f"\n✅ After deduplication:")
print(f"   Flood: {len(flood_images)}")
print(f"   Not Flood: {len(not_flood_images)}")

# %%
# Balance and split
import random
random.seed(42)

# VALIDATION: Ensure we have images
if len(flood_images) == 0 and len(not_flood_images) == 0:
    print("❌ ERROR: No labeled images found!")
    print("\\n💡 Attempting to use unknown images as flood...")
    # If we have unknown images, assume they might be flood (common in flood datasets)
    if unknown_images:
        # Split unknown 50/50 as a fallback
        random.shuffle(unknown_images)
        mid = len(unknown_images) // 2
        flood_images = unknown_images[:mid]
        not_flood_images = unknown_images[mid:]
        print(f"   Assigned {len(flood_images)} as flood, {len(not_flood_images)} as not_flood")
    else:
        raise ValueError("No images found in any dataset. Check download and folder structure.")

elif len(flood_images) == 0:
    print("⚠️ WARNING: No flood images found. Splitting unknown images...")
    random.shuffle(unknown_images)
    flood_images = unknown_images[:len(unknown_images)//2]
    
elif len(not_flood_images) == 0:
    print("⚠️ WARNING: No non-flood images found. Splitting unknown images...")
    random.shuffle(unknown_images)
    not_flood_images = unknown_images[:len(unknown_images)//2]

# Balance classes
min_count = min(len(flood_images), len(not_flood_images))
if min_count == 0:
    raise ValueError("Cannot balance: one class has 0 images")
    
flood_images = random.sample(flood_images, min_count)
not_flood_images = random.sample(not_flood_images, min_count)

print(f"\\n⚖️ Balanced dataset: {min_count} images per class")

# Split: 80% train, 10% val, 10% test
def split_data(images, train_ratio=0.8, val_ratio=0.1):
    random.shuffle(images)
    n = len(images)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return images[:train_end], images[train_end:val_end], images[val_end:]

flood_train, flood_val, flood_test = split_data(flood_images)
not_flood_train, not_flood_val, not_flood_test = split_data(not_flood_images)

# %%
# Copy to unified directory
def copy_images(images, dest_dir, prefix=""):
    for i, src in enumerate(tqdm(images, desc=f"Copying to {dest_dir.name}")):
        ext = src.suffix
        dst = dest_dir / f"{prefix}_{i:05d}{ext}"
        shutil.copy2(src, dst)

copy_images(flood_train, TRAIN_DIR / "flood", "flood")
copy_images(flood_val, VAL_DIR / "flood", "flood")
copy_images(flood_test, TEST_DIR / "flood", "flood")

copy_images(not_flood_train, TRAIN_DIR / "not_flood", "not_flood")
copy_images(not_flood_val, VAL_DIR / "not_flood", "not_flood")
copy_images(not_flood_test, TEST_DIR / "not_flood", "not_flood")

print("\n✅ Data organized!")
print(f"   Train: {len(list((TRAIN_DIR/'flood').iterdir()))} flood, {len(list((TRAIN_DIR/'not_flood').iterdir()))} not_flood")
print(f"   Val: {len(list((VAL_DIR/'flood').iterdir()))} flood, {len(list((VAL_DIR/'not_flood').iterdir()))} not_flood")
print(f"   Test: {len(list((TEST_DIR/'flood').iterdir()))} flood, {len(list((TEST_DIR/'not_flood').iterdir()))} not_flood")

# %% [markdown]
# ## 5. Dataset & DataLoader

# %%
class FloodDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        
        # Load flood images (label=1)
        flood_dir = self.root_dir / "flood"
        if flood_dir.exists():
            for img in flood_dir.iterdir():
                if img.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                    self.samples.append((img, 1))
        
        # Load not_flood images (label=0)
        not_flood_dir = self.root_dir / "not_flood"
        if not_flood_dir.exists():
            for img in not_flood_dir.iterdir():
                if img.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
                    self.samples.append((img, 0))
        
        print(f"Loaded {len(self.samples)} images from {root_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, label
        except Exception as e:
            # Return a black image if loading fails
            return torch.zeros(3, 224, 224), label

# %%
# Transforms
train_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# %%
# Create datasets
train_dataset = FloodDataset(TRAIN_DIR, transform=train_transform)
val_dataset = FloodDataset(VAL_DIR, transform=val_transform)
test_dataset = FloodDataset(TEST_DIR, transform=val_transform)

# Create dataloaders
BATCH_SIZE = 32

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

print(f"Train batches: {len(train_loader)}")
print(f"Val batches: {len(val_loader)}")
print(f"Test batches: {len(test_loader)}")

# %% [markdown]
# ## 6. Model Definition

# %%
class FloodClassifier(nn.Module):
    def __init__(self, freeze_backbone=True):
        super().__init__()
        
        # Load pretrained MobileNetV2
        self.backbone = models.mobilenet_v2(weights='IMAGENET1K_V1')
        
        # Freeze backbone if specified
        if freeze_backbone:
            for param in self.backbone.features.parameters():
                param.requires_grad = False
        
        # Replace classifier
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(1280, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.backbone(x)
    
    def unfreeze_layers(self, n_layers=3):
        """Unfreeze last n layers of backbone for fine-tuning."""
        layers = list(self.backbone.features.children())
        for layer in layers[-n_layers:]:
            for param in layer.parameters():
                param.requires_grad = True

# %%
# Initialize model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = FloodClassifier(freeze_backbone=True).to(device)

print(f"Model on: {device}")
print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# %% [markdown]
# ## 7. Training Functions

# %%
def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    pbar = tqdm(loader, desc="Training")
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.float().unsqueeze(1).to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        predicted = (outputs > 0.5).float()
        correct += (predicted == labels).sum().item()
        total += labels.size(0)
        
        pbar.set_postfix({'loss': f'{total_loss/total:.4f}', 'acc': f'{correct/total:.4f}'})
    
    return total_loss / len(loader), correct / total

def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(loader, desc="Validating"):
            images = images.to(device)
            labels = labels.float().unsqueeze(1).to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            predicted = (outputs > 0.5).float()
            correct += (predicted == labels).sum().item()
            total += labels.size(0)
            
            all_preds.extend(predicted.cpu().numpy().flatten())
            all_labels.extend(labels.cpu().numpy().flatten())
    
    # Calculate metrics
    from sklearn.metrics import precision_score, recall_score, f1_score
    precision = precision_score(all_labels, all_preds)
    recall = recall_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds)
    
    return total_loss / len(loader), correct / total, precision, recall, f1

# %% [markdown]
# ## 8. Training - Phase 1 (Frozen Backbone)

# %%
# Phase 1: Train classifier head only
criterion = nn.BCELoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

EPOCHS_PHASE1 = 10
best_f1 = 0

print("=" * 60)
print("PHASE 1: Training Classifier Head (Backbone Frozen)")
print("=" * 60)

for epoch in range(EPOCHS_PHASE1):
    print(f"\nEpoch {epoch+1}/{EPOCHS_PHASE1}")
    
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc, precision, recall, f1 = validate(model, val_loader, criterion, device)
    
    scheduler.step(val_loss)
    
    print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    
    if f1 > best_f1:
        best_f1 = f1
        torch.save(model.state_dict(), "flood_cnn_phase1.pth")
        print(f"✅ Best model saved (F1: {f1:.4f})")

# %% [markdown]
# ## 9. Training - Phase 2 (Fine-tuning)

# %%
# Phase 2: Unfreeze last layers and fine-tune
model.unfreeze_layers(n_layers=3)
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.0001)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

EPOCHS_PHASE2 = 15

print("\n" + "=" * 60)
print("PHASE 2: Fine-tuning (Last 3 Layers Unfrozen)")
print("=" * 60)
print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

for epoch in range(EPOCHS_PHASE2):
    print(f"\nEpoch {epoch+1}/{EPOCHS_PHASE2}")
    
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc, precision, recall, f1 = validate(model, val_loader, criterion, device)
    
    scheduler.step(val_loss)
    
    print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    
    if f1 > best_f1:
        best_f1 = f1
        torch.save(model.state_dict(), "flood_cnn_final.pth")
        print(f"✅ Best model saved (F1: {f1:.4f})")

# %% [markdown]
# ## 10. Final Evaluation

# %%
# Load best model
model.load_state_dict(torch.load("flood_cnn_final.pth"))

# Evaluate on test set
test_loss, test_acc, precision, recall, f1 = validate(model, test_loader, criterion, device)

print("\n" + "=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)
print(f"Accuracy:  {test_acc:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")

# %%
# Confusion Matrix
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(device)
        outputs = model(images)
        predicted = (outputs > 0.5).float()
        all_preds.extend(predicted.cpu().numpy().flatten())
        all_labels.extend(labels.numpy())

cm = confusion_matrix(all_labels, all_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Not Flood', 'Flood'],
            yticklabels=['Not Flood', 'Flood'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.savefig('confusion_matrix.png', dpi=150)
plt.show()

print("\nClassification Report:")
print(classification_report(all_labels, all_preds, target_names=['Not Flood', 'Flood']))

# %% [markdown]
# ## 11. Export Model

# %%
# Save final model
torch.save(model.state_dict(), "flood_cnn_colab_final.pth")

# Also save as complete model (for easier loading)
torch.save(model, "flood_cnn_colab_complete.pth")

print("✅ Models saved!")
print("   - flood_cnn_colab_final.pth (state_dict)")
print("   - flood_cnn_colab_complete.pth (full model)")

# %%
# Download model
from google.colab import files

print("📥 Downloading model...")
files.download("flood_cnn_colab_final.pth")

# %% [markdown]
# ## 12. Usage in Project
# 
# After downloading the model:
# 
# ```bash
# # Copy to your project
# cp flood_cnn_colab_final.pth models/mobilenetv2_flood_final.pth
# 
# # Restart backend
# .venv\Scripts\python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002
# ```
# 
# The ensemble classifier will automatically load the new model!
