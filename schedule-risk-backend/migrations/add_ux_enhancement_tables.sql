-- Migration: Add UX Enhancement Tables
-- Priority 1-8: Notification, Preferences, Webhooks, Feedback

-- Priority 1: Notification Preferences
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_risk_alerts BOOLEAN DEFAULT TRUE,
    email_daily_digest BOOLEAN DEFAULT FALSE,
    email_weekly_summary BOOLEAN DEFAULT FALSE,
    risk_alert_threshold FLOAT DEFAULT 70.0,
    risk_digest_threshold FLOAT DEFAULT 50.0,
    digest_frequency VARCHAR(20) DEFAULT 'daily',
    project_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);

-- Priority 4: Webhook Configurations
CREATE TABLE IF NOT EXISTS webhook_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id VARCHAR REFERENCES projects(project_id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    webhook_url VARCHAR NOT NULL,
    webhook_type VARCHAR NOT NULL,
    triggers JSONB NOT NULL,
    risk_threshold FLOAT DEFAULT 70.0,
    payload_template JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    secret_key VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_webhook_configurations_user_id ON webhook_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_configurations_project_id ON webhook_configurations(project_id);

-- Priority 6: User Preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    risk_threshold_high FLOAT DEFAULT 70.0,
    risk_threshold_medium FLOAT DEFAULT 40.0,
    risk_threshold_low FLOAT DEFAULT 0.0,
    dashboard_layout JSONB DEFAULT '{}',
    default_filters JSONB DEFAULT '{}',
    default_views JSONB DEFAULT '{}',
    show_p50_first BOOLEAN DEFAULT FALSE,
    show_p80_first BOOLEAN DEFAULT TRUE,
    show_anomalies_section BOOLEAN DEFAULT TRUE,
    show_resource_summary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Priority 8: User Feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    feedback_type VARCHAR NOT NULL,
    context_id VARCHAR,
    was_helpful BOOLEAN,
    feedback_text TEXT,
    rating INTEGER,
    page_url VARCHAR,
    user_agent VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_user_feedback_feedback_type ON user_feedback(feedback_type);

