-- Migration: Add cache tables for forecast, risks, and anomalies
-- This dramatically improves API response times by avoiding expensive recomputation
-- 
-- Run this migration with:
-- psql -U your_username -d your_database_name -f schedule-risk-backend/migrations/add_cache_tables.sql

-- Forecast cache table
CREATE TABLE IF NOT EXISTS forecast_cache (
    project_id VARCHAR PRIMARY KEY,
    p50 FLOAT NOT NULL,
    p80 FLOAT NOT NULL,
    p90 FLOAT,
    p95 FLOAT,
    current FLOAT,
    criticality_indices JSONB,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_forecast_cache_computed_at ON forecast_cache(computed_at);

-- Risks cache table
CREATE TABLE IF NOT EXISTS risks_cache (
    project_id VARCHAR PRIMARY KEY,
    total_risks INTEGER NOT NULL,
    top_risks JSONB NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_risks_cache_computed_at ON risks_cache(computed_at);

-- Anomalies cache table
CREATE TABLE IF NOT EXISTS anomalies_cache (
    project_id VARCHAR PRIMARY KEY,
    zombie_tasks JSONB NOT NULL,
    black_holes JSONB NOT NULL,
    total_anomalies INTEGER NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_anomalies_cache_computed_at ON anomalies_cache(computed_at);

-- Comments for documentation
COMMENT ON TABLE forecast_cache IS 'Caches Monte Carlo forecast results to avoid expensive recomputation';
COMMENT ON TABLE risks_cache IS 'Caches risk analysis results to avoid expensive recomputation';
COMMENT ON TABLE anomalies_cache IS 'Caches anomaly detection results to avoid expensive recomputation';
COMMENT ON COLUMN forecast_cache.activity_count IS 'Number of activities when computed - used for cache invalidation';
COMMENT ON COLUMN risks_cache.activity_count IS 'Number of activities when computed - used for cache invalidation';
COMMENT ON COLUMN anomalies_cache.activity_count IS 'Number of activities when computed - used for cache invalidation';

