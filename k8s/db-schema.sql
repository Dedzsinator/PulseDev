-- PulseDev CCM Database Schema
-- This script initializes the database structure for the Context-Cognizant Monitoring system

-- Create TimescaleDB extension (if not already created)
CREATE EXTENSION
IF NOT EXISTS timescaledb CASCADE;

-- Enable necessary extensions
CREATE EXTENSION
IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION
IF NOT EXISTS "pgcrypto";

-- Create enum types
CREATE TYPE event_type AS ENUM
(
    'code_change',
    'file_access',
    'test_run',
    'build',
    'debug',
    'commit',
    'branch_switch',
    'merge',
    'deployment',
    'error',
    'warning',
    'info'
);

CREATE TYPE agent_type AS ENUM
(
    'vscode',
    'intellij',
    'vim',
    'neovim',
    'sublime',
    'atom',
    'emacs',
    'other'
);

CREATE TYPE flow_state AS ENUM
(
    'in_flow',
    'entering_flow',
    'exiting_flow',
    'interrupted',
    'stuck'
);

-- Users table
CREATE TABLE
IF NOT EXISTS users
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    username VARCHAR
(255) UNIQUE NOT NULL,
    email VARCHAR
(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW
(),
    updated_at TIMESTAMPTZ DEFAULT NOW
(),
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

-- Projects table
CREATE TABLE
IF NOT EXISTS projects
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    name VARCHAR
(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR
(500),
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    created_at TIMESTAMPTZ
DEFAULT NOW
(),
    updated_at TIMESTAMPTZ DEFAULT NOW
(),
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

-- Context events table (main time-series data)
CREATE TABLE
IF NOT EXISTS context_events
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW
(),
    event_type event_type NOT NULL,
    agent agent_type NOT NULL,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    project_id UUID
REFERENCES projects
(id) ON
DELETE CASCADE,
    file_path VARCHAR(1000),
    function_name VARCHAR
(500),
    line_number INTEGER,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    git_branch VARCHAR
(255),
    git_commit_hash VARCHAR
(40),
    energy_score FLOAT,
    flow_state flow_state,
    context_hash VARCHAR
(64), -- For deduplication
    created_at TIMESTAMPTZ DEFAULT NOW
()
);

-- Convert context_events to hypertable for time-series optimization
SELECT create_hypertable('context_events', 'timestamp', if_not_exists
=> TRUE);

-- Flow sessions table
CREATE TABLE
IF NOT EXISTS flow_sessions
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    project_id UUID
REFERENCES projects
(id) ON
DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_minutes INTEGER,
    event_count INTEGER
DEFAULT 0,
    average_energy_score FLOAT,
    peak_energy_score FLOAT,
    flow_quality_score FLOAT,
    interruption_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW
()
);

-- Gamification points table
CREATE TABLE
IF NOT EXISTS gamification_points
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    project_id UUID
REFERENCES projects
(id) ON
DELETE CASCADE,
    points INTEGER
NOT NULL DEFAULT 0,
    reason VARCHAR
(255) NOT NULL,
    event_id UUID REFERENCES context_events
(id) ON
DELETE CASCADE,
    created_at TIMESTAMPTZ
DEFAULT NOW
()
);

-- User achievements table
CREATE TABLE
IF NOT EXISTS user_achievements
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    achievement_type VARCHAR(100)
NOT NULL,
    achievement_name VARCHAR
(255) NOT NULL,
    description TEXT,
    points_awarded INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    earned_at TIMESTAMPTZ DEFAULT NOW
()
);

-- AI training data table
CREATE TABLE
IF NOT EXISTS ai_training_data
(
    id UUID DEFAULT gen_random_uuid
() PRIMARY KEY,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE,
    project_id UUID
REFERENCES projects
(id) ON
DELETE CASCADE,
    input_features JSONB
NOT NULL,
    target_output JSONB NOT NULL,
    model_version VARCHAR
(50),
    training_session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW
()
);

-- System metrics table
CREATE TABLE
IF NOT EXISTS system_metrics
(
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW
(),
    metric_name VARCHAR
(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB DEFAULT '{}'::jsonb,
    user_id UUID REFERENCES users
(id) ON
DELETE CASCADE
);

-- Convert system_metrics to hypertable
SELECT create_hypertable('system_metrics', 'timestamp', if_not_exists
=> TRUE);

-- Create indexes for better query performance
CREATE INDEX
IF NOT EXISTS idx_context_events_user_id ON context_events
(user_id);
CREATE INDEX
IF NOT EXISTS idx_context_events_project_id ON context_events
(project_id);
CREATE INDEX
IF NOT EXISTS idx_context_events_timestamp ON context_events
(timestamp);
CREATE INDEX
IF NOT EXISTS idx_context_events_event_type ON context_events
(event_type);
CREATE INDEX
IF NOT EXISTS idx_context_events_agent ON context_events
(agent);
CREATE INDEX
IF NOT EXISTS idx_context_events_flow_state ON context_events
(flow_state);
CREATE INDEX
IF NOT EXISTS idx_context_events_git_branch ON context_events
(git_branch);
CREATE INDEX
IF NOT EXISTS idx_context_events_context_hash ON context_events
(context_hash);

CREATE INDEX
IF NOT EXISTS idx_flow_sessions_user_id ON flow_sessions
(user_id);
CREATE INDEX
IF NOT EXISTS idx_flow_sessions_project_id ON flow_sessions
(project_id);
CREATE INDEX
IF NOT EXISTS idx_flow_sessions_start_time ON flow_sessions
(start_time);

CREATE INDEX
IF NOT EXISTS idx_gamification_points_user_id ON gamification_points
(user_id);
CREATE INDEX
IF NOT EXISTS idx_gamification_points_created_at ON gamification_points
(created_at);

CREATE INDEX
IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics
(timestamp);
CREATE INDEX
IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics
(metric_name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column
()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW
();
RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE
UPDATE ON users
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column
();

CREATE TRIGGER update_projects_updated_at BEFORE
UPDATE ON projects
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column
();

-- Create retention policies for time-series data
-- Keep detailed data for 30 days, then compress
SELECT add_retention_policy('context_events', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('system_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Enable compression on older data
SELECT add_compression_policy('context_events', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('system_metrics', INTERVAL '7 days', if_not_exists => TRUE);

-- Insert default admin user (optional)
INSERT INTO users
    (username, email, settings)
VALUES
    ('admin', 'admin@pulsedev.local', '{"role": "admin", "created_by": "system"}'
::jsonb)
ON CONFLICT
(username) DO NOTHING;

-- Create some useful views
CREATE OR REPLACE VIEW user_daily_stats AS
SELECT
    user_id,
    DATE(timestamp) as date,
    COUNT(*) as event_count,
    AVG(energy_score) as avg_energy_score,
    MAX(energy_score) as peak_energy_score,
    COUNT(DISTINCT flow_state) as flow_states_used,
    COUNT(*) FILTER
(WHERE flow_state = 'in_flow') as flow_events,
    COUNT
(*) FILTER
(WHERE event_type = 'error') as error_count
FROM context_events
GROUP BY user_id, DATE
(timestamp);

CREATE OR REPLACE VIEW project_activity_summary AS
SELECT
    p.id as project_id,
    p.name as project_name,
    COUNT(ce.*) as total_events,
    COUNT(DISTINCT ce.user_id) as active_users,
    MIN(ce.timestamp) as first_activity,
    MAX(ce.timestamp) as last_activity,
    AVG(ce.energy_score) as avg_energy_score
FROM projects p
    LEFT JOIN context_events ce ON p.id = ce.project_id
GROUP BY p.id, p.name;

-- Analyze tables for better query planning
ANALYZE users;
ANALYZE projects;
ANALYZE context_events;
ANALYZE flow_sessions;
ANALYZE gamification_points;
ANALYZE user_achievements;
ANALYZE ai_training_data;
ANALYZE system_metrics;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Log successful initialization
INSERT INTO system_metrics
    (metric_name, metric_value, labels)
VALUES
    ('database_initialization', 1, '{"status": "success", "version": "1.0"}'
::jsonb);

COMMIT;
