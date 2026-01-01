# Diagram 5: Database Entity Relationship Diagram

The PostGIS database schema showing relationships between core entities in the flood validation system.

## Mermaid Code

```mermaid
erDiagram
    USERS {
        int user_id PK "Primary Key"
        string username UK "Unique, Indexed"
        string email "Optional"
        string phone_hash "SHA-256 Hashed"
        float trust_score "0.0 - 1.0"
        float trust_alpha "Bayesian α"
        float trust_beta "Bayesian β"
        int total_reports "Count"
        int verified_reports "Validated Count"
        int flagged_reports "Flagged Count"
        datetime created_at "Timestamp"
        datetime updated_at "On Update"
        datetime last_active "Activity Tracker"
    }

    FLOOD_REPORTS {
        int report_id PK "Primary Key"
        int user_id FK "References USERS"
        geography location "PostGIS POINT(4326)"
        float latitude "Decimal Degrees"
        float longitude "Decimal Degrees"
        float location_accuracy_m "GPS Accuracy"
        float depth_meters "Observed Depth"
        datetime timestamp "Report Time"
        text description "User Notes"
        text photo_url "S3 URL"
        string source "mobile_app|web|twitter|sms"
        string validation_status "pending|validated|flagged|rejected"
        float final_score "Aggregated 0.0-1.0"
        float physical_score "Layer 1"
        float statistical_score "Layer 2"
        float reputation_score "Layer 3"
        boolean is_synthetic "Test Data Flag"
        datetime created_at "Insert Time"
        datetime updated_at "Modification Time"
        datetime validated_at "Validation Complete"
    }

    VALIDATION_METADATA {
        int validation_id PK "Primary Key"
        int report_id FK "References FLOOD_REPORTS"
        float elevation "DEM Value (m)"
        float elevation_neighborhood_mean "5x5 Window"
        float hand_value "HAND Index"
        float slope_degrees "Terrain Slope"
        float rainfall_24h_mm "IMD Data"
        int neighbor_count "DBSCAN K"
        datetime created_at "Timestamp"
    }

    GROUND_TRUTH {
        int truth_id PK "Primary Key"
        string event_name "Flood Event ID"
        datetime event_date "Occurrence Date"
        geography flood_extent "PostGIS MULTIPOLYGON"
        datetime created_at "Timestamp"
    }

    EXPERIMENT_RESULTS {
        int result_id PK "Primary Key"
        int truth_id FK "References GROUND_TRUTH"
        string experiment_name "Run Identifier"
        float accuracy "Model Accuracy"
        float precision_val "Precision"
        float recall "Recall"
        float f1_score "F1 Metric"
        json confusion_matrix "TP/TN/FP/FN"
        json layer_weights "Learned Weights"
        datetime run_at "Experiment Time"
    }

    %% Relationships
    USERS ||--o{ FLOOD_REPORTS : "submits"
    FLOOD_REPORTS ||--|| VALIDATION_METADATA : "has"
    GROUND_TRUTH ||--o{ EXPERIMENT_RESULTS : "validates"
```

## Indexes and Constraints

```sql
-- Primary Keys
ALTER TABLE users ADD PRIMARY KEY (user_id);
ALTER TABLE flood_reports ADD PRIMARY KEY (report_id);
ALTER TABLE validation_metadata ADD PRIMARY KEY (validation_id);
ALTER TABLE ground_truth ADD PRIMARY KEY (truth_id);

-- Unique Constraints
ALTER TABLE users ADD CONSTRAINT uq_username UNIQUE (username);

-- Foreign Keys
ALTER TABLE flood_reports 
    ADD CONSTRAINT fk_user 
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;

ALTER TABLE validation_metadata 
    ADD CONSTRAINT fk_report 
    FOREIGN KEY (report_id) REFERENCES flood_reports(report_id) ON DELETE CASCADE;

-- Spatial Indexes (PostGIS)
CREATE INDEX idx_reports_location ON flood_reports USING GIST (location);
CREATE INDEX idx_ground_truth_extent ON ground_truth USING GIST (flood_extent);

-- Performance Indexes
CREATE INDEX idx_reports_status ON flood_reports (validation_status);
CREATE INDEX idx_reports_timestamp ON flood_reports (timestamp);
CREATE INDEX idx_users_trust ON users (trust_score DESC);
```

## PostGIS Extensions

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Spatial Reference System (WGS84)
-- SRID 4326 is used for GPS coordinates
SELECT ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) AS location;

-- Example: Find reports within 5km radius
SELECT * FROM flood_reports
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(85.88, 20.46), 4326)::geography,
    5000  -- meters
);
```
