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

-- Gamification Tables
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    total_xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    total_commits INTEGER DEFAULT 0,
    total_flow_time INTEGER DEFAULT 0, -- in minutes
    total_coding_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    category VARCHAR(50), -- flow, commits, streaks, coding, debugging
    xp_reward INTEGER DEFAULT 0,
    unlock_criteria JSONB, -- flexible criteria storage
    tier VARCHAR(20) DEFAULT 'bronze', -- bronze, silver, gold, platinum
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    achievement_id UUID REFERENCES achievements(id),
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    session_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id, achievement_id)
);

CREATE TABLE xp_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    session_id VARCHAR(255),
    amount INTEGER NOT NULL,
    source VARCHAR(100), -- flow_state, commit, debugging, test_pass, etc.
    description TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE daily_streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    date DATE NOT NULL,
    coding_minutes INTEGER DEFAULT 0,
    commits INTEGER DEFAULT 0,
    flow_sessions INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    files_edited INTEGER DEFAULT 0,
    tests_passed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE TABLE active_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50), -- vscode, browser, nvim
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    sync_token VARCHAR(255) -- for cross-platform sync
);

CREATE TABLE leaderboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    category VARCHAR(50), -- xp, streaks, commits, flow_time
    value INTEGER NOT NULL,
    period VARCHAR(20), -- daily, weekly, monthly, all_time
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Gamification indexes
CREATE INDEX idx_user_profiles_session_id ON user_profiles(session_id);
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_xp_transactions_user_session ON xp_transactions(user_id, session_id);
CREATE INDEX idx_xp_transactions_timestamp ON xp_transactions(timestamp DESC);
CREATE INDEX idx_daily_streaks_user_date ON daily_streaks(user_id, date DESC);
CREATE INDEX idx_active_sessions_user_platform ON active_sessions(user_id, platform, is_active);
CREATE INDEX idx_leaderboards_category_period ON leaderboards(category, period, date DESC);

-- Convert XP transactions to hypertable
SELECT create_hypertable('xp_transactions', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Insert default achievements
INSERT INTO achievements (name, description, icon, category, xp_reward, unlock_criteria, tier) VALUES
-- Coding achievements
('First Steps', 'Write your first line of code', '🎯', 'coding', 10, '{"event_count": 1, "event_type": "file_edit"}', 'bronze'),
('Code Rookie', 'Edit 10 files', '📝', 'coding', 25, '{"files_edited": 10}', 'bronze'),
('Code Warrior', 'Edit 100 files', '⚔️', 'coding', 100, '{"files_edited": 100}', 'silver'),
('Code Master', 'Edit 1000 files', '👑', 'coding', 500, '{"files_edited": 1000}', 'gold'),

-- Flow achievements
('Flow Starter', 'Achieve 15 minutes of continuous flow', '🌊', 'flow', 25, '{"flow_duration": 15}', 'bronze'),
('Flow Master', 'Achieve 60 minutes of continuous flow', '🌀', 'flow', 75, '{"flow_duration": 60}', 'silver'),
('Flow Legend', 'Achieve 2 hours of flow in one session', '🧘', 'flow', 200, '{"single_flow_duration": 120}', 'gold'),
('Flow God', 'Achieve 4 hours of flow in one day', '✨', 'flow', 500, '{"daily_flow_time": 240}', 'platinum'),

-- Commit achievements
('First Commit', 'Make your first commit', '📦', 'commits', 20, '{"commits": 1}', 'bronze'),
('Commit Streak', 'Make commits for 5 consecutive days', '🔥', 'commits', 75, '{"commit_streak": 5}', 'silver'),
('Commit Champion', 'Make 100 total commits', '🏆', 'commits', 200, '{"total_commits": 100}', 'gold'),
('Speed Demon', 'Complete 10 commits in one day', '⚡', 'commits', 150, '{"daily_commits": 10}', 'silver'),

-- Streak achievements
('Streak Starter', 'Code for 3 consecutive days', '🔥', 'streaks', 50, '{"streak_days": 3}', 'bronze'),
('Week Warrior', 'Code every day for a week', '🗓️', 'streaks', 150, '{"streak_days": 7}', 'silver'),
('Month Master', 'Code every day for a month', '📅', 'streaks', 500, '{"streak_days": 30}', 'gold'),
('Year Legend', 'Code every day for 365 days', '🌟', 'streaks', 2000, '{"streak_days": 365}', 'platinum'),

-- Debugging achievements
('Bug Hunter', 'Resolve your first error', '🐛', 'debugging', 15, '{"errors_resolved": 1}', 'bronze'),
('Debug Ninja', 'Successfully resolve 10 errors', '🥷', 'debugging', 75, '{"errors_resolved": 10}', 'silver'),
('Error Eliminator', 'Resolve 100 errors', '💀', 'debugging', 250, '{"errors_resolved": 100}', 'gold'),

-- Testing achievements
('Test Rookie', 'Pass your first test', '✅', 'testing', 15, '{"tests_passed": 1}', 'bronze'),
('Test Master', 'Achieve 90% test pass rate', '🎯', 'testing', 100, '{"test_pass_rate": 0.9}', 'silver'),
('Test Perfectionist', 'Achieve 100% test pass rate', '💯', 'testing', 200, '{"test_pass_rate": 1.0}', 'gold'),

-- Special achievements
('Night Owl', 'Code after midnight', '🦉', 'special', 25, '{"late_night_coding": true}', 'bronze'),
('Early Bird', 'Code before 6 AM', '🐦', 'special', 25, '{"early_morning_coding": true}', 'bronze'),
('Weekend Warrior', 'Code on weekends', '⚡', 'special', 50, '{"weekend_coding": true}', 'silver'),
('Productivity Beast', 'Earn 1000 XP in one day', '🔥', 'special', 300, '{"daily_xp": 1000}', 'gold');

-- Gamification triggers
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();