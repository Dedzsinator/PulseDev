-- PulseDev+ CCM Database Schema
-- TimescaleDB extension for time-series data

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main context nodes table (hypertable for time-series)
CREATE TABLE context_nodes (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    encrypted_payload TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_path TEXT,
    line_number INTEGER,
    user_id VARCHAR(255),
    project_id VARCHAR(255)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('context_nodes', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Context relationships table
CREATE TABLE context_relationships (
    id BIGSERIAL PRIMARY KEY,
    from_node_id BIGINT REFERENCES context_nodes(id) ON DELETE CASCADE,
    to_node_id BIGINT REFERENCES context_nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(from_node_id, to_node_id, relationship_type)
);

-- Flow sessions table
CREATE TABLE flow_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    keystrokes INTEGER DEFAULT 0,
    context_switches INTEGER DEFAULT 0,
    test_runs INTEGER DEFAULT 0,
    commits INTEGER DEFAULT 0,
    energy_score FLOAT,
    focus_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stuck states table
CREATE TABLE stuck_states (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pattern VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ
);

-- Code relationships table
CREATE TABLE code_relationships (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    dependencies JSONB NOT NULL DEFAULT '[]',
    dependents JSONB NOT NULL DEFAULT '[]',
    impact_score INTEGER DEFAULT 0,
    risk_level VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User preferences table
CREATE TABLE user_preferences (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    auto_commit_enabled BOOLEAN DEFAULT FALSE,
    ephemeral_mode_hours INTEGER DEFAULT 24,
    encryption_enabled BOOLEAN DEFAULT TRUE,
    ignore_patterns JSONB DEFAULT '[]',
    slack_webhook_url TEXT,
    jira_config JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Energy metrics table (hypertable)
CREATE TABLE energy_metrics (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    energy_score FLOAT NOT NULL,
    flow_duration INTEGER DEFAULT 0,
    test_pass_rate FLOAT DEFAULT 0,
    context_switches INTEGER DEFAULT 0,
    error_frequency FLOAT DEFAULT 0,
    keystroke_rhythm FLOAT DEFAULT 0,
    metrics_data JSONB NOT NULL DEFAULT '{}'
);

SELECT create_hypertable('energy_metrics', 'timestamp', chunk_time_interval => INTERVAL '1 hour');

-- Git activity table
CREATE TABLE git_activity (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    repo_path TEXT NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    branch_name VARCHAR(255),
    commit_hash VARCHAR(40),
    commit_message TEXT,
    files_changed JSONB DEFAULT '[]',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI interactions table
CREATE TABLE ai_interactions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    prompt_text TEXT,
    response_text TEXT,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    context_window_minutes INTEGER DEFAULT 30,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Browser activity table (hypertable)
CREATE TABLE browser_activity (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    tab_id INTEGER,
    url TEXT,
    title TEXT,
    activity_type VARCHAR(50) NOT NULL,
    focus_duration INTEGER DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('browser_activity', 'timestamp', chunk_time_interval => INTERVAL '1 hour');

-- Indexes for performance
CREATE INDEX idx_context_nodes_session_timestamp ON context_nodes (session_id, timestamp DESC);
CREATE INDEX idx_context_nodes_agent_type ON context_nodes (agent, event_type);
CREATE INDEX idx_context_nodes_file_path ON context_nodes (file_path) WHERE file_path IS NOT NULL;

CREATE INDEX idx_context_relationships_from_node ON context_relationships (from_node_id);
CREATE INDEX idx_context_relationships_to_node ON context_relationships (to_node_id);

CREATE INDEX idx_flow_sessions_session_id ON flow_sessions (session_id);
CREATE INDEX idx_flow_sessions_start_time ON flow_sessions (start_time DESC);

CREATE INDEX idx_stuck_states_session_timestamp ON stuck_states (session_id, detected_at DESC);
CREATE INDEX idx_stuck_states_pattern ON stuck_states (pattern);

CREATE INDEX idx_energy_metrics_session_timestamp ON energy_metrics (session_id, timestamp DESC);

CREATE INDEX idx_git_activity_session_timestamp ON git_activity (session_id, timestamp DESC);
CREATE INDEX idx_git_activity_repo ON git_activity (repo_path);

CREATE INDEX idx_browser_activity_session_timestamp ON browser_activity (session_id, timestamp DESC);
CREATE INDEX idx_browser_activity_url ON browser_activity (url);

-- Retention policies for automatic cleanup
SELECT add_retention_policy('context_nodes', INTERVAL '90 days');
SELECT add_retention_policy('energy_metrics', INTERVAL '30 days');
SELECT add_retention_policy('browser_activity', INTERVAL '30 days');

-- Views for common queries
CREATE VIEW recent_context AS
SELECT 
    cn.*,
    cr.relationship_type,
    cr.weight as relationship_weight
FROM context_nodes cn
LEFT JOIN context_relationships cr ON cn.id = cr.from_node_id
WHERE cn.timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY cn.timestamp DESC;

CREATE VIEW session_summary AS
SELECT 
    session_id,
    COUNT(*) as total_events,
    COUNT(DISTINCT agent) as agents_used,
    COUNT(DISTINCT file_path) as files_touched,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as duration_minutes
FROM context_nodes
GROUP BY session_id;

-- Trigger for auto-updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_code_relationships_updated_at 
    BEFORE UPDATE ON code_relationships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();