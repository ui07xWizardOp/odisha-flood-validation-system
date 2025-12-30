-- =============================================================================
-- Odisha Flood Validation System - Database Setup Script
-- =============================================================================
-- PostgreSQL 15+ with PostGIS 3.3+ required
--
-- Usage:
--   psql -U postgres -f scripts/setup_database.sql
--
-- Or to run as specific user:
--   psql -h localhost -U postgres -d postgres -f scripts/setup_database.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Create Database and Enable Extensions
-- -----------------------------------------------------------------------------

-- Drop database if exists (BE CAREFUL in production!)
-- DROP DATABASE IF EXISTS flood_validation;

-- Create database
CREATE DATABASE flood_validation
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Connect to the new database
\c flood_validation

-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- For text matching

-- Verify PostGIS installation
SELECT PostGIS_Full_Version();

-- -----------------------------------------------------------------------------
-- 2. Create Application User
-- -----------------------------------------------------------------------------

-- Create application user (password should be changed in production)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flood_admin') THEN
        CREATE ROLE flood_admin WITH LOGIN PASSWORD 'flood_secure_password_2024';
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE flood_validation TO flood_admin;

-- -----------------------------------------------------------------------------
-- 3. Create Users Table (Contributors/Citizens)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    phone_hash VARCHAR(64),  -- Hashed phone for privacy
    
    -- Trust/Reputation System
    trust_score REAL DEFAULT 0.5 
        CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    trust_alpha REAL DEFAULT 1.0,  -- Beta distribution alpha (successes)
    trust_beta REAL DEFAULT 1.0,   -- Beta distribution beta (failures)
    
    -- Statistics
    total_reports INTEGER DEFAULT 0,
    verified_reports INTEGER DEFAULT 0,
    flagged_reports INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for username lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_trust_score ON users(trust_score DESC);

COMMENT ON TABLE users IS 'Registered contributors who submit flood reports';
COMMENT ON COLUMN users.trust_score IS 'Current trust score (0-1), derived from Bayesian update';
COMMENT ON COLUMN users.trust_alpha IS 'Beta distribution alpha parameter for Bayesian trust';

-- -----------------------------------------------------------------------------
-- 4. Create Flood Reports Table
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS flood_reports (
    report_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Location (PostGIS Geography for accurate distance calculations)
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    location_accuracy_m REAL,  -- GPS accuracy in meters
    
    -- Report Details
    depth_meters REAL CHECK (depth_meters >= 0 AND depth_meters <= 20),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    photo_url TEXT,
    source VARCHAR(50) DEFAULT 'mobile_app',  -- mobile_app, twitter, manual
    
    -- Validation Results
    validation_status VARCHAR(20) DEFAULT 'pending'
        CHECK (validation_status IN ('pending', 'validated', 'flagged', 'rejected', 'expired')),
    final_score REAL CHECK (final_score >= 0 AND final_score <= 1),
    
    -- Layer Scores
    physical_score REAL,
    statistical_score REAL,
    reputation_score REAL,
    
    -- Metadata
    is_synthetic BOOLEAN DEFAULT FALSE,  -- For experiment data
    ground_truth_label VARCHAR(20),  -- 'flooded' or 'safe' (for experiments)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP WITH TIME ZONE
);

-- Spatial index for location queries (CRITICAL for performance)
CREATE INDEX IF NOT EXISTS idx_reports_location 
    ON flood_reports USING GIST(location);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_reports_timestamp 
    ON flood_reports(timestamp DESC);

-- Index for validation status filtering
CREATE INDEX IF NOT EXISTS idx_reports_status 
    ON flood_reports(validation_status);

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_reports_status_timestamp 
    ON flood_reports(validation_status, timestamp DESC);

COMMENT ON TABLE flood_reports IS 'Crowdsourced flood reports from citizens';
COMMENT ON COLUMN flood_reports.location IS 'PostGIS Geography point for accurate spatial queries';

-- -----------------------------------------------------------------------------
-- 5. Create Validation Metadata Table
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS validation_metadata (
    validation_id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES flood_reports(report_id) ON DELETE CASCADE,
    
    -- Layer 1: Physical Plausibility Details
    elevation REAL,
    elevation_neighborhood_mean REAL,
    elevation_diff REAL,
    hand_value REAL,
    slope_degrees REAL,
    
    -- Layer 1 Sub-scores
    elevation_score REAL,
    hand_score REAL,
    slope_score REAL,
    
    -- Layer 2: Statistical Consistency Details
    neighbor_count INTEGER,
    agreeing_neighbors INTEGER,
    consensus_percentage REAL,
    rainfall_24h_mm REAL,
    is_statistical_outlier BOOLEAN,
    
    -- Layer 2 Sub-scores
    spatial_score REAL,
    temporal_score REAL,
    outlier_score REAL,
    
    -- Processing Metadata
    validation_time_ms INTEGER,  -- Processing time
    algorithm_version VARCHAR(20) DEFAULT '1.0.0',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_report 
    ON validation_metadata(report_id);

COMMENT ON TABLE validation_metadata IS 'Detailed validation scores and terrain features';

-- -----------------------------------------------------------------------------
-- 6. Create Ground Truth Table (Bhuvan Data)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ground_truth (
    truth_id SERIAL PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,  -- e.g., 'Cyclone Fani 2019'
    event_date DATE NOT NULL,
    
    -- Flood extent polygon
    flood_extent GEOGRAPHY(MULTIPOLYGON, 4326),
    
    -- Optional point data
    sample_point GEOGRAPHY(POINT, 4326),
    actual_depth_m REAL,
    
    -- Source information
    source VARCHAR(100) DEFAULT 'ISRO_Bhuvan',
    source_url TEXT,
    
    -- Administrative boundaries
    district VARCHAR(100),
    block VARCHAR(100),
    village VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_groundtruth_extent 
    ON ground_truth USING GIST(flood_extent);

CREATE INDEX IF NOT EXISTS idx_groundtruth_event 
    ON ground_truth(event_name, event_date);

COMMENT ON TABLE ground_truth IS 'Validated flood extents from ISRO Bhuvan';

-- -----------------------------------------------------------------------------
-- 7. Create Experiment Results Table
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    
    -- Configuration
    noise_percentage REAL,
    validation_method VARCHAR(50),  -- 'proposed', 'pure_ml', 'dem_only', 'none'
    dataset_path TEXT,
    
    -- Metrics
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    accuracy REAL,
    iou_score REAL,
    roc_auc REAL,
    
    -- Confusion Matrix
    true_positives INTEGER,
    false_positives INTEGER,
    true_negatives INTEGER,
    false_negatives INTEGER,
    
    -- Timing
    total_reports INTEGER,
    processing_time_seconds REAL,
    avg_time_per_report_ms REAL,
    
    -- Metadata
    run_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_experiments_name 
    ON experiment_results(experiment_name);

COMMENT ON TABLE experiment_results IS 'Results from validation experiments';

-- -----------------------------------------------------------------------------
-- 8. Create Useful Functions
-- -----------------------------------------------------------------------------

-- Function: Get reports within radius of a point
CREATE OR REPLACE FUNCTION get_reports_within_radius(
    center_lat REAL,
    center_lon REAL,
    radius_meters INTEGER DEFAULT 200
)
RETURNS TABLE(
    report_id INTEGER,
    user_id INTEGER,
    latitude REAL,
    longitude REAL,
    depth_meters REAL,
    validation_status VARCHAR,
    distance_meters REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fr.report_id,
        fr.user_id,
        fr.latitude,
        fr.longitude,
        fr.depth_meters,
        fr.validation_status,
        ST_Distance(
            fr.location,
            ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography
        )::REAL as distance_meters
    FROM flood_reports fr
    WHERE ST_DWithin(
        fr.location,
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326)::geography,
        radius_meters
    )
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_reports_within_radius IS 'Find all reports within specified radius of a coordinate';


-- Function: Calculate IoU between validated reports and ground truth
CREATE OR REPLACE FUNCTION calculate_iou(
    event_name_param VARCHAR,
    buffer_degrees REAL DEFAULT 0.01
)
RETURNS REAL AS $$
DECLARE
    validated_polygon GEOMETRY;
    truth_polygon GEOMETRY;
    intersection_area REAL;
    union_area REAL;
BEGIN
    -- Create polygon from validated reports (buffered points)
    SELECT ST_Union(ST_Buffer(location::geometry, buffer_degrees))
    INTO validated_polygon
    FROM flood_reports
    WHERE validation_status = 'validated'
      AND depth_meters > 0;
    
    -- Get ground truth polygon
    SELECT flood_extent::geometry
    INTO truth_polygon
    FROM ground_truth
    WHERE ground_truth.event_name = event_name_param
    LIMIT 1;
    
    IF validated_polygon IS NULL OR truth_polygon IS NULL THEN
        RETURN 0.0;
    END IF;
    
    -- Calculate IoU
    intersection_area := ST_Area(ST_Intersection(validated_polygon, truth_polygon));
    union_area := ST_Area(ST_Union(validated_polygon, truth_polygon));
    
    IF union_area = 0 THEN
        RETURN 0.0;
    END IF;
    
    RETURN intersection_area / union_area;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_iou IS 'Calculate Intersection over Union for flood extent accuracy';


-- Function: Get user leaderboard by trust score
CREATE OR REPLACE FUNCTION get_user_leaderboard(
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    rank_position INTEGER,
    user_id INTEGER,
    username VARCHAR,
    trust_score REAL,
    total_reports INTEGER,
    verified_reports INTEGER,
    accuracy_percentage REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY u.trust_score DESC)::INTEGER as rank_position,
        u.user_id,
        u.username,
        u.trust_score,
        u.total_reports,
        u.verified_reports,
        CASE 
            WHEN u.total_reports > 0 
            THEN (u.verified_reports::REAL / u.total_reports * 100)
            ELSE 0.0
        END as accuracy_percentage
    FROM users u
    WHERE u.total_reports > 0
    ORDER BY u.trust_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_leaderboard IS 'Get top contributors ranked by trust score';

-- -----------------------------------------------------------------------------
-- 9. Create Views
-- -----------------------------------------------------------------------------

-- View: User statistics with accuracy
CREATE OR REPLACE VIEW v_user_statistics AS
SELECT 
    u.user_id,
    u.username,
    u.trust_score,
    u.total_reports,
    u.verified_reports,
    u.flagged_reports,
    CASE 
        WHEN u.total_reports > 0 
        THEN ROUND((u.verified_reports::NUMERIC / u.total_reports * 100), 2)
        ELSE 0
    END as accuracy_percentage,
    u.last_active,
    u.created_at
FROM users u;

COMMENT ON VIEW v_user_statistics IS 'User statistics with calculated accuracy percentage';


-- View: Recent reports with user info
CREATE OR REPLACE VIEW v_recent_reports AS
SELECT 
    fr.report_id,
    fr.latitude,
    fr.longitude,
    fr.depth_meters,
    fr.timestamp,
    fr.validation_status,
    fr.final_score,
    u.username,
    u.trust_score as user_trust_score
FROM flood_reports fr
LEFT JOIN users u ON fr.user_id = u.user_id
ORDER BY fr.timestamp DESC
LIMIT 100;

COMMENT ON VIEW v_recent_reports IS 'Most recent 100 flood reports with user info';


-- View: Validation summary statistics
CREATE OR REPLACE VIEW v_validation_summary AS
SELECT 
    validation_status,
    COUNT(*) as report_count,
    ROUND(AVG(final_score)::NUMERIC, 3) as avg_score,
    ROUND(AVG(physical_score)::NUMERIC, 3) as avg_physical,
    ROUND(AVG(statistical_score)::NUMERIC, 3) as avg_statistical,
    ROUND(AVG(reputation_score)::NUMERIC, 3) as avg_reputation
FROM flood_reports
GROUP BY validation_status;

COMMENT ON VIEW v_validation_summary IS 'Summary statistics by validation status';

-- -----------------------------------------------------------------------------
-- 10. Create Trigger for updated_at
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER update_users_modtime
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_reports_modtime
    BEFORE UPDATE ON flood_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- -----------------------------------------------------------------------------
-- 11. Grant Permissions
-- -----------------------------------------------------------------------------

GRANT USAGE ON SCHEMA public TO flood_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flood_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flood_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO flood_admin;

-- -----------------------------------------------------------------------------
-- 12. Insert Sample Data (for testing)
-- -----------------------------------------------------------------------------

-- Sample users
INSERT INTO users (username, email, trust_score, total_reports, verified_reports)
VALUES 
    ('citizen_cuttack', 'citizen1@example.com', 0.75, 15, 12),
    ('rescue_volunteer', 'volunteer@ngo.org', 0.90, 45, 42),
    ('anonymous_reporter', NULL, 0.50, 3, 1)
ON CONFLICT (username) DO NOTHING;

-- Sample flood report (Cuttack city center during Fani)
INSERT INTO flood_reports (
    user_id, 
    location, 
    latitude, 
    longitude, 
    depth_meters, 
    timestamp, 
    description,
    validation_status,
    final_score
)
SELECT 
    1,
    ST_SetSRID(ST_MakePoint(85.8830, 20.4625), 4326)::geography,
    20.4625,
    85.8830,
    1.5,
    '2019-05-03 14:30:00+05:30',
    'Water level rising near Kathajodi river',
    'validated',
    0.85
WHERE NOT EXISTS (
    SELECT 1 FROM flood_reports WHERE latitude = 20.4625 AND longitude = 85.8830
);

-- -----------------------------------------------------------------------------
-- Verification
-- -----------------------------------------------------------------------------

\echo ''
\echo '============================================='
\echo '  Database Setup Complete!'
\echo '============================================='
\echo ''

-- Show table info
\dt

-- Show extensions
\dx

-- Verify sample data
SELECT 'Users:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Reports:', COUNT(*) FROM flood_reports;
