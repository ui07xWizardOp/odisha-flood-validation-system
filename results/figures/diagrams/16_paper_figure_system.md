# Diagram 16: Research Paper Figures - Complete Set

A comprehensive set of publication-ready diagrams suitable for inclusion in IEEE/ACM academic papers. These follow strict academic styling with detailed component labeling.

---

## Figure 1: Complete System Architecture (Primary)

```mermaid
flowchart TD
    subgraph DataCollection["Data Collection Layer"]
        DC1["Mobile Application<br/>(React Native PWA)"]
        DC2["Web Dashboard<br/>(React.js)"]
        DC3["Twitter API v2<br/>(Streaming Endpoint)"]
        DC4["Facebook Graph API<br/>(Webhook)"]
        DC5["SMS Gateway<br/>(Twilio Webhook)"]
        DC6["Government Sensors<br/>(ISRO Bhuvan API)"]
    end

    subgraph StreamProcessing["Stream Processing Layer"]
        SP1["Apache Kafka<br/>(3 Topics: raw, processed, alerts)"]
        SP2["Kafka Consumer Group<br/>(Python 3.10)"]
        SP3["Preprocessing Pipeline"]
        
        subgraph Preprocessing["Preprocessing"]
            PP1["Geocoding<br/>(Google Maps API)"]
            PP2["Schema Validation<br/>(Pydantic)"]
            PP3["Deduplication<br/>(RapidFuzz)"]
            PP4["NLP Extraction<br/>(spaCy)"]
        end
    end

    subgraph ValidationEngine["5-Layer ML Validation Engine"]
        VE0["Orchestrator<br/>(FloodReportValidator)"]
        
        subgraph Layer1["L1: Physical Plausibility"]
            L1A["DEM Lookup<br/>(SRTM 30m)"]
            L1B["HAND Index<br/>(WhiteboxTools)"]
            L1C["Slope Analysis<br/>(Degrees)"]
            L1D["Random Forest<br/>(scikit-learn)"]
        end
        
        subgraph Layer2["L2: Statistical Consistency"]
            L2A["Spatial Query<br/>(PostGIS ST_DWithin)"]
            L2B["DBSCAN Clustering<br/>(eps=1km, min=3)"]
            L2C["Consensus Score"]
        end
        
        subgraph Layer3["L3: User Reputation"]
            L3A["User History<br/>(α, β values)"]
            L3B["Bayesian Update<br/>(Beta Distribution)"]
            L3C["Trust Score<br/>(α/(α+β))"]
        end
        
        subgraph Layer4["L4: Social Context"]
            L4A["NewsAPI Query"]
            L4B["Twitter Search"]
            L4C["NLP Corroboration"]
        end
        
        subgraph Layer5["L5: Computer Vision"]
            L5A["Image Input<br/>(JPEG/PNG)"]
            L5B["CNN Classifier<br/>(ResNet-50)"]
            L5C["Water Segmentation"]
        end
        
        subgraph Aggregation["Weighted Aggregation"]
            AGG1["Weight Network<br/>(Learned via Ground Truth)"]
            AGG2["Final Score<br/>(Σ wᵢ × sᵢ)"]
        end
    end

    subgraph DataStorage["Data Storage Layer"]
        DS1["PostgreSQL 15<br/>(Primary DB)"]
        DS2["PostGIS 3.3<br/>(Spatial Extension)"]
        DS3["AWS S3<br/>(Image Storage)"]
        DS4["Redis<br/>(Session Cache)"]
    end

    subgraph OutputLayer["Output Layer"]
        OL1["Validation Result<br/>(validated/flagged/rejected)"]
        OL2["Alert System<br/>(Firebase FCM + Twilio)"]
        OL3["Analytics Dashboard<br/>(React + Mapbox)"]
        OL4["OSDMA API<br/>(Government Integration)"]
    end

    %% Data Collection to Stream Processing
    DC1 --> SP1
    DC2 --> SP1
    DC3 --> SP1
    DC4 --> SP1
    DC5 --> SP1
    DC6 --> SP1

    SP1 --> SP2
    SP2 --> SP3
    SP3 --> PP1
    SP3 --> PP2
    SP3 --> PP3
    SP3 --> PP4

    %% Preprocessing to Validation
    PP2 --> VE0
    VE0 --> L1A
    VE0 --> L2A
    VE0 --> L3A
    VE0 --> L4A
    VE0 --> L5A

    %% Layer 1 Flow
    L1A --> L1D
    L1B --> L1D
    L1C --> L1D
    L1D --> AGG1

    %% Layer 2 Flow
    L2A --> L2B
    L2B --> L2C
    L2C --> AGG1

    %% Layer 3 Flow
    L3A --> L3B
    L3B --> L3C
    L3C --> AGG1

    %% Layer 4 Flow
    L4A --> L4C
    L4B --> L4C
    L4C --> AGG1

    %% Layer 5 Flow
    L5A --> L5B
    L5B --> L5C
    L5C --> AGG1

    %% Aggregation
    AGG1 --> AGG2
    AGG2 --> OL1

    %% Output
    OL1 --> DS1
    OL1 --> OL2
    OL1 --> OL3
    OL1 --> OL4

    %% Storage Connections
    PP2 --> DS1
    L5A --> DS3
    SP2 --> DS4

    %% Academic Styling (grayscale-friendly)
    classDef inputLayer fill:#f5f5f5,stroke:#424242,stroke-width:1px
    classDef processLayer fill:#e0e0e0,stroke:#424242,stroke-width:1px
    classDef validationLayer fill:#bdbdbd,stroke:#212121,stroke-width:2px
    classDef storageLayer fill:#eeeeee,stroke:#424242,stroke-width:1px
    classDef outputLayer fill:#f5f5f5,stroke:#424242,stroke-width:1px

    class DC1,DC2,DC3,DC4,DC5,DC6 inputLayer
    class SP1,SP2,SP3,PP1,PP2,PP3,PP4 processLayer
    class VE0,L1A,L1B,L1C,L1D,L2A,L2B,L2C,L3A,L3B,L3C,L4A,L4B,L4C,L5A,L5B,L5C,AGG1,AGG2 validationLayer
    class DS1,DS2,DS3,DS4 storageLayer
    class OL1,OL2,OL3,OL4 outputLayer
```

---

## Figure 2: Validation Algorithm Detail

```mermaid
flowchart TD
    subgraph Input["Input Vector"]
        I1["Report R = (φ, λ, d, t, I)"]
        I2["φ: Latitude (19.0° - 22.5°N)"]
        I3["λ: Longitude (81.0° - 87.5°E)"]
        I4["d: Depth (0 - 20m)"]
        I5["t: Timestamp (ISO 8601)"]
        I6["I: Image (JPEG, max 5MB)"]
    end

    subgraph FeatureExtraction["Feature Extraction"]
        F1["e = DEM(φ, λ)<br/>(Elevation in meters)"]
        F2["h = HAND(φ, λ)<br/>(Height Above Nearest Drainage)"]
        F3["s = Slope(φ, λ)<br/>(Degrees, 0-90)"]
        F4["N = neighbors(φ, λ, 5km, 24h)<br/>(Recent reports)"]
        F5["U = user_history(uid)<br/>(α, β parameters)"]
        F6["C = news_search(location, 'flood')"]
        F7["P = CNN(I)<br/>(Flood probability)"]
    end

    subgraph LayerComputation["Layer Score Computation"]
        S1["S₁ = RF(e, h, s, ē, ∇e)<br/>Physical Plausibility"]
        S2["S₂ = cluster_score(DBSCAN(N))<br/>Statistical Consistency"]
        S3["S₃ = α/(α + β)<br/>User Reputation"]
        S4["S₄ = corroboration(C)<br/>Social Context"]
        S5["S₅ = water_ratio(P)<br/>Computer Vision"]
    end

    subgraph WeightedSum["Weighted Aggregation"]
        W1["w = [0.35, 0.25, 0.20, 0.10, 0.10]<br/>(Default Weights)"]
        W2["S_final = Σᵢ wᵢ × Sᵢ"]
    end

    subgraph Decision["Decision Threshold"]
        D1{"S_final ≥ 0.7"}
        D2["VALIDATED"]
        D3{"S_final ≥ 0.4"}
        D4["FLAGGED"]
        D5["REJECTED"]
    end

    I1 --> F1
    I1 --> F2
    I1 --> F3
    I1 --> F4
    I1 --> F5
    I1 --> F6
    I6 --> F7

    F1 --> S1
    F2 --> S1
    F3 --> S1
    F4 --> S2
    F5 --> S3
    F6 --> S4
    F7 --> S5

    S1 --> W2
    S2 --> W2
    S3 --> W2
    S4 --> W2
    S5 --> W2
    W1 --> W2

    W2 --> D1
    D1 -->|"Yes"| D2
    D1 -->|"No"| D3
    D3 -->|"Yes"| D4
    D3 -->|"No"| D5

    classDef inputNode fill:#f5f5f5,stroke:#333,stroke-width:1px
    classDef featureNode fill:#e0e0e0,stroke:#333,stroke-width:1px
    classDef layerNode fill:#bdbdbd,stroke:#212121,stroke-width:2px
    classDef weightNode fill:#9e9e9e,stroke:#212121,stroke-width:2px
    classDef decisionNode fill:#757575,stroke:#212121,stroke-width:2px,color:#fff

    class I1,I2,I3,I4,I5,I6 inputNode
    class F1,F2,F3,F4,F5,F6,F7 featureNode
    class S1,S2,S3,S4,S5 layerNode
    class W1,W2 weightNode
    class D1,D2,D3,D4,D5 decisionNode
```

---

## Figure 3: Physical Plausibility Layer (L1) Detail

```mermaid
flowchart LR
    subgraph RasterData["Geospatial Raster Data"]
        R1["SRTM DEM<br/>(30m resolution)"]
        R2["Derived HAND<br/>(WhiteboxTools)"]
        R3["Derived Slope<br/>(Degrees)"]
    end

    subgraph Extraction["Point Extraction"]
        E1["ST_Value(dem, point)"]
        E2["ST_Value(hand, point)"]
        E3["ST_Value(slope, point)"]
        E4["Neighborhood Mean<br/>(5×5 window)"]
        E5["Elevation Gradient<br/>(∇elevation)"]
    end

    subgraph FeatureVector["Feature Vector (7 dims)"]
        FV["[e, h, s, ē, ∇e, d, t_hour]"]
    end

    subgraph Model["Random Forest Classifier"]
        M1["100 Estimators"]
        M2["max_depth=15"]
        M3["Trained on Mahanadi Basin<br/>(2019-2023 events)"]
        M4["Output: P(flood|features)"]
    end

    R1 --> E1
    R2 --> E2
    R3 --> E3
    E1 --> E4
    E1 --> E5
    E1 --> FV
    E2 --> FV
    E3 --> FV
    E4 --> FV
    E5 --> FV
    FV --> M1
    M1 --> M2
    M2 --> M3
    M3 --> M4
```

---

## Figure 4: DBSCAN Clustering (L2) Detail

```mermaid
flowchart TD
    subgraph SpatialQuery["Spatial Query"]
        SQ1["SELECT * FROM flood_reports<br/>WHERE ST_DWithin(location, target, 5000m)<br/>AND timestamp > NOW() - INTERVAL '24h'"]
        SQ2["Result: N neighboring reports"]
    end

    subgraph CoordinateTransform["Coordinate Transform"]
        CT1["Convert (lat, lon) → radians"]
        CT2["Distance matrix: Haversine"]
    end

    subgraph DBSCAN["DBSCAN Algorithm"]
        DB1["Parameters:<br/>ε = 1000m (radius)<br/>min_samples = 3"]
        DB2["Core Points:<br/>|N_ε(p)| ≥ min_samples"]
        DB3["Border Points:<br/>In ε-neighborhood of core"]
        DB4["Noise Points:<br/>label = -1"]
    end

    subgraph Scoring["Consensus Scoring"]
        SC1["target_cluster = labels[0]"]
        SC2["cluster_size = count(labels == target_cluster)"]
        SC3["S₂ = min(cluster_size / 10, 1.0)"]
    end

    SQ1 --> SQ2
    SQ2 --> CT1
    CT1 --> CT2
    CT2 --> DB1
    DB1 --> DB2
    DB2 --> DB3
    DB3 --> DB4
    DB4 --> SC1
    SC1 --> SC2
    SC2 --> SC3
```

---

## Figure 5: Bayesian Trust Model (L3)

```mermaid
flowchart TD
    subgraph Prior["Prior Distribution"]
        P1["Initial: α₀ = 1, β₀ = 1"]
        P2["Trust₀ = α₀/(α₀ + β₀) = 0.5"]
    end

    subgraph Update["Posterior Update"]
        U1["Report Validated?"]
        U2["Yes: α ← α + 1"]
        U3["No: β ← β + 1"]
        U4["Flagged: No update"]
    end

    subgraph Posterior["Posterior Trust"]
        PO1["Trust = α/(α + β)"]
        PO2["Variance = αβ/((α+β)²(α+β+1))"]
    end

    subgraph Example["Example Progression"]
        EX1["User A: 45 validated, 5 rejected"]
        EX2["α = 46, β = 6"]
        EX3["Trust = 46/52 = 0.88"]
        EX4["High reputation user"]
    end

    P1 --> P2
    P2 --> U1
    U1 -->|"Validated"| U2
    U1 -->|"Rejected"| U3
    U1 -->|"Flagged"| U4
    U2 --> PO1
    U3 --> PO1
    U4 --> PO1
    PO1 --> PO2
    EX1 --> EX2
    EX2 --> EX3
    EX3 --> EX4
```

---

## Figure 6: CNN Image Classifier (L5)

```mermaid
flowchart LR
    subgraph Input["Image Input"]
        I1["User Photo<br/>(Variable size JPEG)"]
        I2["Resize: 224×224"]
        I3["Normalize: ImageNet stats"]
    end

    subgraph Backbone["ResNet-50 Backbone"]
        B1["Conv1: 7×7, 64, stride=2"]
        B2["MaxPool: 3×3, stride=2"]
        B3["Layer1: 3 blocks, 256"]
        B4["Layer2: 4 blocks, 512"]
        B5["Layer3: 6 blocks, 1024"]
        B6["Layer4: 3 blocks, 2048"]
        B7["AvgPool: 7×7"]
    end

    subgraph Head["Classification Head"]
        H1["FC: 2048 → 512"]
        H2["ReLU + Dropout(0.3)"]
        H3["FC: 512 → 2"]
        H4["Softmax"]
    end

    subgraph Output["Output"]
        O1["P(flood) = 0.87"]
        O2["P(non-flood) = 0.13"]
        O3["S₅ = P(flood)"]
    end

    I1 --> I2
    I2 --> I3
    I3 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    B5 --> B6
    B6 --> B7
    B7 --> H1
    H1 --> H2
    H2 --> H3
    H3 --> H4
    H4 --> O1
    H4 --> O2
    O1 --> O3
```

---

## Figure Captions for Paper

**Figure 1:** *Complete system architecture of the proposed AI/ML-enhanced crowdsourced flood validation system, showing all six functional layers from data collection through output generation. Key technologies are labeled at each processing node.*

**Figure 2:** *Detailed validation algorithm showing the complete data flow from input report vector R through feature extraction, layer score computation, weighted aggregation, and final decision thresholding.*

**Figure 3:** *Physical plausibility layer (L1) implementation using Random Forest classifier trained on geospatial features derived from SRTM DEM data for the Mahanadi River Basin.*

**Figure 4:** *Statistical consistency layer (L2) using DBSCAN clustering to compute consensus scores based on spatiotemporal proximity of multiple crowdsourced reports.*

**Figure 5:** *Bayesian trust model for user reputation (L3), demonstrating the beta-binomial update mechanism and example progression for a high-reputation user.*

**Figure 6:** *Computer vision layer (L5) architecture using fine-tuned ResNet-50 for binary flood/non-flood classification from user-submitted photographs.*

---

## Export Commands for LaTeX

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate high-resolution PNGs (300 DPI equivalent)
mmdc -i 16_paper_figure_system.md -o figure1.png -s 4 -b white

# Generate SVG for vector graphics
mmdc -i 16_paper_figure_system.md -o figure1.svg -b white

# Convert SVG to PDF for LaTeX
inkscape figure1.svg --export-pdf=figure1.pdf

# Or use pdf2svg
pdf2svg figure1.pdf figure1.svg
```

## LaTeX Include Example

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{figures/figure1.pdf}
    \caption{Complete system architecture of the proposed AI/ML-enhanced 
    crowdsourced flood validation system.}
    \label{fig:system-architecture}
\end{figure}
```
