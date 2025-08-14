-- PulseDev CCM Database Schema (Simplified for Docker)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum types
CREATE TYPE event_type AS ENUM ('code_change', 'file_access', 'test_run', 'build', 'debug', 'commit', 'branch_switch', 'merge', 'deployment', 'error', 'warning', 'info');
CREATE TYPE agent_type AS ENUM ('vscode', 'intellij', 'vim', 'neovim', 'sublime', 'atom', 'emacs', 'other');
CREATE TYPE flow_state AS ENUM ('in_flow', 'entering_flow', 'exiting_flow', 'interrupted', 'stuck');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true
);

-- Context events table (main time-series data)
CREATE TABLE IF NOT EXISTS context_events (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id UUID DEFAULT gen_random_uuid(),
    event_type event_type NOT NULL,
    agent agent_type NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path TEXT,
    function_name TEXT,
    line_number INTEGER,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    git_branch TEXT,
    git_commit_hash TEXT,
    energy_score FLOAT,
    flow_state flow_state,
    context_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (timestamp, id)  -- Composite primary key including timestamp
);

-- Convert to hypertable
SELECT create_hypertable('context_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_context_events_user_id ON context_events(user_id);
CREATE INDEX IF NOT EXISTS idx_context_events_timestamp ON context_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_context_events_event_type ON context_events(event_type);

-- Insert default admin user
INSERT INTO users (username, email, settings)
VALUES ('admin', 'admin@pulsedev.local', '{"role": "admin"}'::jsonb)
ON CONFLICT (username) DO NOTHING;
