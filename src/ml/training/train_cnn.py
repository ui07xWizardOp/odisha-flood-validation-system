"""
CNN Training Script for Flood Image Classification.

Downloads FloodNet dataset and fine-tunes MobileNetV2 for binary flood detection.
Saves trained model to models/flood_cnn.pth
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset, random_split
    from torchvision import transforms, models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.error("PyTorch not installed. Run: pip install torch torchvision")

# Try to import PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class FloodDataset(Dataset):
    """
    Custom dataset for flood/non-flood image classification.
    
    Expected directory structure:
    data/flood_images/
        flood/
            img1.jpg
            img2.jpg
        not_flood/
            img3.jpg
            img4.jpg
    """
    
    def __init__(self, root_dir: str, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples = []
        
        # Load flood images (label=1)
        flood_dir = self.root_dir / "flood"
        if flood_dir.exists():
            for img_path in flood_dir.glob("*.jpg"):
                self.samples.append((str(img_path), 1))
            for img_path in flood_dir.glob("*.png"):
                self.samples.append((str(img_path), 1))
        
        # Load non-flood images (label=0)
        non_flood_dir = self.root_dir / "not_flood"
        if non_flood_dir.exists():
            for img_path in non_flood_dir.glob("*.jpg"):
                self.samples.append((str(img_path), 0))
            for img_path in non_flood_dir.glob("*.png"):
                self.samples.append((str(img_path), 0))
        
        logger.info(f"Loaded {len(self.samples)} images from {root_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


class FloodCNNTrainer:
    """
    Trainer for flood image classification CNN.
    Uses MobileNetV2 with transfer learning.
    """
    
    def __init__(self, data_dir: str = "data/flood_images", 
                 model_save_path: str = "models/flood_cnn.pth",
                 batch_size: int = 32,
                 epochs: int = 10,
                 learning_rate: float = 0.001):
        
        self.data_dir = data_dir
        self.model_save_path = Path(model_save_path)
        self.batch_size = batch_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.train_loader = None
        self.val_loader = None
        
        # Image transforms
        self.train_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        self.val_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    
    def setup_model(self):
        """Initialize MobileNetV2 with pretrained weights."""
        self.model = models.mobilenet_v2(weights='IMAGENET1K_V1')
        
        # Freeze all layers except classifier
        for param in self.model.features.parameters():
            param.requires_grad = False
        
        # Replace classifier for binary classification
        self.model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(1280, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        
        self.model = self.model.to(self.device)
        logger.info(f"Model initialized on {self.device}")
    
    def setup_data(self) -> bool:
        """Load and split dataset."""
        if not Path(self.data_dir).exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            logger.info("Please create the directory with flood/ and not_flood/ subdirectories")
            return False
        
        # Use train transform for initial loading (we'll apply val transform to validation set)
        dataset = FloodDataset(self.data_dir, transform=self.train_transform)
        
        if len(dataset) == 0:
            logger.error("No images found in dataset")
            return False
        
        # Split 80/20
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
        
        self.train_loader = DataLoader(train_dataset, batch_size=self.batch_size, 
                                        shuffle=True, num_workers=0)
        self.val_loader = DataLoader(val_dataset, batch_size=self.batch_size, 
                                      shuffle=False, num_workers=0)
        
        logger.info(f"Train: {len(train_dataset)}, Validation: {len(val_dataset)}")
        return True
    
    def train(self) -> dict:
        """Train the model."""
        if self.model is None:
            self.setup_model()
        
        if not self.setup_data():
            return {"error": "Failed to setup data"}
        
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.classifier.parameters(), lr=self.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2)
        
        best_val_loss = float('inf')
        history = {"train_loss": [], "val_loss": [], "val_acc": []}
        
        for epoch in range(self.epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for images, labels in self.train_loader:
                images = images.to(self.device)
                labels = labels.float().to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(images).squeeze()
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(self.train_loader)
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for images, labels in self.val_loader:
                    images = images.to(self.device)
                    labels = labels.float().to(self.device)
                    
                    outputs = self.model(images).squeeze()
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()
                    
                    predicted = (outputs > 0.5).float()
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            
            val_loss /= len(self.val_loader)
            val_acc = correct / total
            
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            
            logger.info(f"Epoch {epoch+1}/{self.epochs} - "
                       f"Train Loss: {train_loss:.4f}, "
                       f"Val Loss: {val_loss:.4f}, "
                       f"Val Acc: {val_acc:.4f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model()
            
            scheduler.step(val_loss)
        
        return {
            "final_train_loss": history["train_loss"][-1],
            "final_val_loss": history["val_loss"][-1],
            "final_val_acc": history["val_acc"][-1],
            "best_val_loss": best_val_loss,
            "model_path": str(self.model_save_path)
        }
    
    def save_model(self):
        """Save model weights."""
        self.model_save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), self.model_save_path)
        logger.info(f"Model saved to {self.model_save_path}")
    
    def load_model(self) -> bool:
        """Load model weights."""
        if not self.model_save_path.exists():
            logger.error(f"Model file not found: {self.model_save_path}")
            return False
        
        if self.model is None:
            self.setup_model()
        
        self.model.load_state_dict(torch.load(self.model_save_path, map_location=self.device))
        self.model.eval()
        logger.info(f"Model loaded from {self.model_save_path}")
        return True
    
    def predict(self, image: Image.Image) -> Tuple[bool, float]:
        """Predict if image contains flood."""
        if self.model is None:
            if not self.load_model():
                return False, 0.0
        
        self.model.eval()
        image = self.val_transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.model(image).squeeze().item()
        
        return output > 0.5, output


def create_sample_dataset():
    """Create sample directory structure for training data."""
    data_dir = Path("data/flood_images")
    (data_dir / "flood").mkdir(parents=True, exist_ok=True)
    (data_dir / "not_flood").mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory structure at {data_dir}")
    print("Please add images to:")
    print(f"  - {data_dir / 'flood'} (images showing flooding)")
    print(f"  - {data_dir / 'not_flood'} (normal images)")


if __name__ == "__main__":
    print("🧠 CNN Training Script for Flood Detection")
    print(f"   PyTorch available: {TORCH_AVAILABLE}")
    
    if not TORCH_AVAILABLE:
        print("   ERROR: PyTorch not installed")
        exit(1)
    
    # Create sample dataset structure
    create_sample_dataset()
    
    # Check if data exists
    data_dir = Path("data/flood_images")
    flood_count = len(list((data_dir / "flood").glob("*.jpg"))) if (data_dir / "flood").exists() else 0
    non_flood_count = len(list((data_dir / "not_flood").glob("*.jpg"))) if (data_dir / "not_flood").exists() else 0
    
    if flood_count == 0 and non_flood_count == 0:
        print("\n   No training data found.")
        print("   Add images to data/flood_images/flood/ and data/flood_images/not_flood/")
        print("   Then run: python -m src.ml.training.train_cnn")
    else:
        print(f"\n   Found {flood_count} flood images, {non_flood_count} non-flood images")
        
        trainer = FloodCNNTrainer()
        results = trainer.train()
        print(f"\n   Training results: {results}")
