"""
Neural Network for Dynamic Layer Weight Learning.

Instead of fixed weights (0.4, 0.4, 0.2), this network learns
optimal weights for combining Layer 1, 2, 3, 4 scores.
"""

import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class WeightLearningNetwork:
    """
    Simple feedforward network that learns optimal layer weights.
    Uses gradient descent to minimize validation error.
    """
    
    def __init__(self, n_layers: int = 4, learning_rate: float = 0.01):
        """
        Args:
            n_layers: Number of validation layers to combine
            learning_rate: Learning rate for weight updates
        """
        self.n_layers = n_layers
        self.lr = learning_rate
        
        # Initialize weights uniformly
        self.weights = np.ones(n_layers) / n_layers
        
        # Bias term
        self.bias = 0.0
        
        # Training history
        self.history = []
        
    def forward(self, layer_scores: np.ndarray) -> float:
        """
        Compute weighted combination of layer scores.
        
        Args:
            layer_scores: Array of [L1, L2, L3, L4] scores
            
        Returns:
            Final validation score (0-1)
        """
        # Weighted sum with softmax normalization
        normalized_weights = self._softmax(self.weights)
        score = np.dot(normalized_weights, layer_scores) + self.bias
        return self._sigmoid(score)
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid activation for output."""
        return 1 / (1 + np.exp(-np.clip(x, -20, 20)))
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax to ensure weights sum to 1."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def train_step(self, layer_scores: np.ndarray, target: float) -> float:
        """
        Single training step using gradient descent.
        
        Args:
            layer_scores: [L1, L2, L3, L4] scores
            target: Ground truth (0 or 1)
            
        Returns:
            Loss value
        """
        # Forward pass
        prediction = self.forward(layer_scores)
        
        # Binary cross-entropy loss
        eps = 1e-7
        loss = -(target * np.log(prediction + eps) + 
                 (1 - target) * np.log(1 - prediction + eps))
        
        # Gradient of loss w.r.t. prediction
        d_loss = (prediction - target)
        
        # Gradient of sigmoid
        d_sigmoid = prediction * (1 - prediction)
        
        # Update weights
        normalized_weights = self._softmax(self.weights)
        for i in range(self.n_layers):
            gradient = d_loss * d_sigmoid * layer_scores[i]
            self.weights[i] -= self.lr * gradient
        
        # Update bias
        self.bias -= self.lr * d_loss * d_sigmoid
        
        return loss
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100) -> List[float]:
        """
        Train on dataset of (layer_scores, target) pairs.
        
        Args:
            X: Shape (n_samples, n_layers)
            y: Shape (n_samples,) binary targets
            epochs: Training iterations
            
        Returns:
            Loss history
        """
        print(f"🧠 Training Weight Learning Network...")
        print(f"   Initial weights: {self._softmax(self.weights)}")
        
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0
            for i in range(len(X)):
                loss = self.train_step(X[i], y[i])
                epoch_loss += loss
            
            avg_loss = epoch_loss / len(X)
            losses.append(avg_loss)
            
            if epoch % 20 == 0:
                print(f"   Epoch {epoch}: Loss = {avg_loss:.4f}")
        
        print(f"   Final weights: {self._softmax(self.weights)}")
        self.history = losses
        return losses
    
    def get_weights(self) -> Dict[str, float]:
        """Get current normalized weights."""
        normalized = self._softmax(self.weights)
        return {
            "L1_physical": float(normalized[0]),
            "L2_statistical": float(normalized[1]),
            "L3_reputation": float(normalized[2]),
            "L4_social": float(normalized[3]) if self.n_layers > 3 else 0.0
        }
    
    def save(self, path: str):
        """Save model weights to JSON."""
        model_data = {
            "weights": self.weights.tolist(),
            "bias": float(self.bias),
            "n_layers": self.n_layers
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(model_data, f, indent=2)
        print(f"✅ Model saved: {path}")
    
    @classmethod
    def load(cls, path: str) -> 'WeightLearningNetwork':
        """Load model from JSON."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        model = cls(n_layers=data['n_layers'])
        model.weights = np.array(data['weights'])
        model.bias = data['bias']
        return model


# Singleton instance with default weights
weight_network = WeightLearningNetwork(n_layers=4)


def train_weight_network():
    """Generate synthetic data and train the network."""
    np.random.seed(42)
    
    # Generate training data
    # True floods: High L1, L2, variable L3, L4
    n_positive = 300
    X_pos = np.column_stack([
        np.random.beta(8, 2, n_positive),  # L1: High physical
        np.random.beta(7, 2, n_positive),  # L2: High statistical
        np.random.beta(5, 3, n_positive),  # L3: Variable reputation
        np.random.beta(4, 4, n_positive),  # L4: Variable social
    ])
    y_pos = np.ones(n_positive)
    
    # False reports: Low L1, L2, variable L3, L4
    n_negative = 200
    X_neg = np.column_stack([
        np.random.beta(2, 8, n_negative),  # L1: Low physical
        np.random.beta(2, 7, n_negative),  # L2: Low statistical
        np.random.beta(3, 5, n_negative),  # L3: Variable reputation
        np.random.beta(4, 4, n_negative),  # L4: Variable social
    ])
    y_neg = np.zeros(n_negative)
    
    # Combine
    X = np.vstack([X_pos, X_neg])
    y = np.concatenate([y_pos, y_neg])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X, y = X[indices], y[indices]
    
    # Train
    model = WeightLearningNetwork(n_layers=4, learning_rate=0.05)
    model.train(X, y, epochs=100)
    
    # Save
    model.save("models/weight_network.json")
    
    print(f"\n📊 Learned Weights:")
    for layer, weight in model.get_weights().items():
        print(f"   {layer}: {weight:.3f}")
    
    return model


if __name__ == "__main__":
    train_weight_network()
