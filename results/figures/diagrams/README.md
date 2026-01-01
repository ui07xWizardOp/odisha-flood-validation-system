# Mermaid.js Technical Documentation Diagrams

This directory contains comprehensive Mermaid.js diagrams documenting the **AI/ML-Enhanced Crowdsourced Flood Validation System for Odisha**.

## Diagram Index

| # | Diagram | Description | Best For |
|---|---------|-------------|----------|
| 01 | [System Architecture](./01_system_architecture.md) | High-level ecosystem visualization | Overview presentations |
| 02 | [Data Ingestion Pipeline](./02_data_ingestion.md) | Real-time streaming architecture | Technical deep-dive |
| 03 | [Validation Algorithm](./03_validation_algorithm.md) | 5-layer ML validation logic | **Research Paper** |
| 04 | [Report Lifecycle](./04_report_lifecycle.md) | State diagram with sub-states | Database design |
| 05 | [Database ER Diagram](./05_database_er.md) | PostGIS schema structure | Database documentation |
| 06 | [API Sequence](./06_api_sequence.md) | Image upload workflow | API documentation |
| 07 | [Deployment Architecture](./07_deployment_architecture.md) | Docker containerization | DevOps documentation |
| 08 | [ML Model Architecture](./08_ml_model_architecture.md) | Machine learning pipeline | **Research Paper** |
| 09 | [Trust Score Flow](./09_trust_score_flow.md) | Bayesian reputation system | Algorithm explanation |
| 10 | [User Journey](./10_user_journey.md) | End-to-end user experience | UX documentation |
| 11 | [Component Dependencies](./11_component_dependency.md) | Codebase module graph | Developer onboarding |
| 12 | [Weight Learning Network](./12_validation_weight_network.md) | Adaptive weight optimization | **Research Paper** |
| 13 | [Geospatial Processing](./13_geospatial_processing.md) | DEM/HAND/Slope pipeline | Geospatial methods |
| 14 | [DBSCAN Clustering](./14_dbscan_clustering.md) | Spatial clustering algorithm | Algorithm explanation |
| 15 | [Notification Flow](./15_notification_flow.md) | Emergency alert system | System design |
| 16 | [Paper Figures (6 Figs)](./16_paper_figure_system.md) | Publication-ready diagrams | **Academic Papers** |
| 17 | [Complete Data Flow](./17_complete_data_flow.md) | End-to-end data movement | Architecture overview |
| 18 | [Technology Stack](./18_technology_stack.md) | All technologies with versions | Documentation |

## Quick Stats
- **Total Diagrams:** 18 (with 6 additional sub-figures in Paper Figures)
- **Diagram Types:** Flowcharts, State Diagrams, ER Diagrams, Sequence Diagrams, Journey Maps
- **Last Updated:** January 2026
- **All diagrams include:** Color coding, technology labels, explanatory tables

## How to Render

### Option 1: Mermaid Live Editor
1. Copy the Mermaid code block from any diagram file
2. Paste into [mermaid.live](https://mermaid.live/)
3. Export as SVG/PNG

### Option 2: VS Code Extension
Install the "Markdown Preview Mermaid Support" extension to preview diagrams directly.

### Option 3: GitHub/GitLab
Both platforms natively render Mermaid diagrams in markdown files.

### Option 4: Pandoc + mermaid-filter
```bash
pandoc input.md --filter mermaid-filter -o output.pdf
```

## Technologies Referenced

- **Backend**: FastAPI, Uvicorn
- **Database**: PostgreSQL 15, PostGIS 3.3, GeoAlchemy2
- **ML/AI**: Random Forest, DBSCAN, LightGBM, XGBoost, CNN (Image Classification)
- **Streaming**: Apache Kafka
- **External APIs**: Twitter, ISRO Bhuvan, IMD Weather, Google Vision
- **Frontend**: React, React Native (PWA)
- **DevOps**: Docker, Nginx
