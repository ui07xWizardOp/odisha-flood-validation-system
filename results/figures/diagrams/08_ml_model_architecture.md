# Diagram 8: ML Model Architecture

Detailed visualization of the machine learning models used in the flood validation system, showing their interconnections and data flow.

## Mermaid Code

```mermaid
flowchart TD
    subgraph Input["📥 Input Features"]
        GEO["🌍 Geospatial<br/>(lat, lon, elevation)"]
        TEMPORAL["⏰ Temporal<br/>(timestamp, duration)"]
        USER["👤 User<br/>(trust_score, history)"]
        IMG["🖼️ Image<br/>(photo bytes)"]
        CONTEXT["📰 Context<br/>(news, tweets)"]
    end

    subgraph FeatureEngineering["⚙️ Feature Engineering"]
        RASTER["📊 Raster Extraction<br/>(DEM, HAND, Slope)"]
        SPATIAL["🗺️ Spatial Features<br/>(neighbor_count, distance)"]
        TEMPORAL_FE["📅 Temporal Features<br/>(hour, day, season)"]
        TEXT_FE["📝 Text Embeddings<br/>(TF-IDF / Transformers)"]
    end

    subgraph Models["🧠 ML Models"]
        subgraph Ensemble["🌲 Ensemble Models"]
            RF["🌳 Random Forest<br/>(Physical Plausibility)<br/>n_estimators=100"]
            LGB["📈 LightGBM<br/>(Gradient Boosting)<br/>num_leaves=31"]
            XGB["🚀 XGBoost<br/>(Alternative Ensemble)<br/>max_depth=6"]
        end
        
        subgraph Clustering["📊 Clustering"]
            DBSCAN["🔬 DBSCAN<br/>(Spatial Consistency)<br/>eps=1km, min_samples=3"]
        end
        
        subgraph DeepLearning["🧠 Deep Learning"]
            CNN["🖼️ CNN (ResNet-50)<br/>(Image Classification)<br/>Fine-tuned for Floods"]
            WATER_SEG["💧 Water Segmentation<br/>(U-Net Lite)"]
        end
        
        subgraph Probabilistic["🎲 Probabilistic"]
            BAYESIAN["📊 Bayesian Trust<br/>(Beta Distribution)<br/>α, β updates"]
        end
    end

    subgraph WeightLearning["⚖️ Weight Learning Network"]
        ADAPTIVE["🔗 Adaptive Weighting<br/>(Learned from Ground Truth)"]
        GRADIENT["📉 Gradient-Free Opt<br/>(Nelder-Mead)"]
    end

    subgraph Output["📤 Outputs"]
        L1["Layer 1 Score"]
        L2["Layer 2 Score"]
        L3["Layer 3 Score"]
        L4["Layer 4 Score"]
        L5["Layer 5 Score"]
        FINAL["🎯 Final Score<br/>(Weighted Sum)"]
    end

    %% Feature Flow
    GEO --> RASTER
    GEO --> SPATIAL
    TEMPORAL --> TEMPORAL_FE
    CONTEXT --> TEXT_FE
    
    %% To Models
    RASTER --> RF
    RASTER --> LGB
    SPATIAL --> DBSCAN
    USER --> BAYESIAN
    IMG --> CNN
    CNN --> WATER_SEG
    
    %% Model Outputs
    RF --> L1
    LGB --> L1
    DBSCAN --> L2
    BAYESIAN --> L3
    TEXT_FE --> L4
    WATER_SEG --> L5

    %% Weight Learning
    L1 --> ADAPTIVE
    L2 --> ADAPTIVE
    L3 --> ADAPTIVE
    L4 --> ADAPTIVE
    L5 --> ADAPTIVE
    GRADIENT --> ADAPTIVE
    ADAPTIVE --> FINAL

    %% Styling
    classDef inputNode fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef feNode fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef modelNode fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef dlNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef weightNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef outputNode fill:#fff8e1,stroke:#f9a825,stroke-width:2px

    class GEO,TEMPORAL,USER,IMG,CONTEXT inputNode
    class RASTER,SPATIAL,TEMPORAL_FE,TEXT_FE feNode
    class RF,LGB,XGB,DBSCAN,BAYESIAN modelNode
    class CNN,WATER_SEG dlNode
    class ADAPTIVE,GRADIENT weightNode
    class L1,L2,L3,L4,L5,FINAL outputNode
```

## Model Specifications

| Model | Library | Purpose | Hyperparameters |
|-------|---------|---------|-----------------|
| **Random Forest** | scikit-learn | Physical Plausibility | n_estimators=100, max_depth=15 |
| **LightGBM** | lightgbm | Ensemble Boosting | num_leaves=31, learning_rate=0.05 |
| **XGBoost** | xgboost | Alternative Ensemble | max_depth=6, n_estimators=200 |
| **DBSCAN** | scikit-learn | Spatial Clustering | eps=1000m, min_samples=3 |
| **ResNet-50** | PyTorch | Flood Detection | pretrained=ImageNet, fine-tuned |
| **Beta Distribution** | scipy.stats | Trust Scoring | α=1.0, β=1.0 (prior) |

## Training Pipeline

```mermaid
flowchart LR
    subgraph Data["📊 Training Data"]
        GT["Ground Truth<br/>(SAR / Satellite)"]
        SYNTH["Synthetic<br/>(Augmented)"]
    end
    
    subgraph Split["✂️ Data Split"]
        TRAIN["Train (70%)"]
        VAL["Validation (15%)"]
        TEST["Test (15%)"]
    end
    
    subgraph Training["🏋️ Training"]
        CV["5-Fold CV"]
        OPTUNA["Hyperparameter<br/>Optimization"]
    end
    
    subgraph Eval["📈 Evaluation"]
        METRICS["Accuracy, F1<br/>Precision, Recall"]
        CONFUSION["Confusion Matrix"]
    end
    
    GT --> TRAIN
    SYNTH --> TRAIN
    GT --> VAL
    GT --> TEST
    
    TRAIN --> CV
    CV --> OPTUNA
    OPTUNA --> METRICS
    VAL --> METRICS
    TEST --> CONFUSION
```
