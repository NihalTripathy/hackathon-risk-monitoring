-- Migration: Add portfolio optimization tables
-- This dramatically improves portfolio screen loading by storing computed metrics
-- 
-- Run this migration with:
-- psql -U your_username -d your_database_name -f schedule-risk-backend/migrations/add_portfolio_cache_tables.sql

-- Project metrics table - stores computed metrics per project for portfolio aggregation
CREATE TABLE IF NOT EXISTS project_metrics (
    project_id VARCHAR PRIMARY KEY,
    user_id INTEGER NOT NULL,
    risk_score FLOAT NOT NULL,
    activity_count INTEGER NOT NULL,
    resource_summary JSONB,
    high_risk_activities_count INTEGER DEFAULT 0,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_metrics_user_id ON project_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_project_metrics_computed_at ON project_metrics(computed_at);

-- Portfolio cache table - stores aggregated portfolio data per user
CREATE TABLE IF NOT EXISTS portfolio_cache (
    user_id INTEGER PRIMARY KEY,
    total_projects INTEGER NOT NULL,
    total_activities INTEGER NOT NULL,
    portfolio_risk_score FLOAT NOT NULL,
    projects_at_risk INTEGER NOT NULL,
    high_risk_projects JSONB NOT NULL,
    resource_summary JSONB NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_portfolio_cache_computed_at ON portfolio_cache(computed_at);

-- Comments for documentation
COMMENT ON TABLE project_metrics IS 'Stores computed metrics per project for fast portfolio aggregation';
COMMENT ON TABLE portfolio_cache IS 'Stores aggregated portfolio data per user for instant portfolio screen loading';
COMMENT ON COLUMN project_metrics.risk_score IS 'Average risk score for the project (computed from all activities)';
COMMENT ON COLUMN project_metrics.resource_summary IS 'Resource allocation summary for this project (JSON)';
COMMENT ON COLUMN portfolio_cache.high_risk_projects IS 'Array of high-risk project objects (JSON)';
COMMENT ON COLUMN portfolio_cache.resource_summary IS 'Aggregated resource summary across all projects (JSON)';

