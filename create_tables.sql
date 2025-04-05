-- Simple SQL script to create the necessary tables for BrainBot in Supabase

-- Users table - stores basic user information
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- URL history table - stores the URLs visited by users
CREATE TABLE IF NOT EXISTS url_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    url TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'productive', 'unproductive', or 'unknown'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User state table - tracks if users are locked in studying or brain rotting
CREATE TABLE IF NOT EXISTS user_state (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    locked_in BOOLEAN NOT NULL,  -- true = locked in studying, false = brain rotting
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER,  -- duration in seconds, calculated when end_time is set
    notes TEXT  -- optional notes about this state period
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_url_history_user_id ON url_history(user_id);
CREATE INDEX IF NOT EXISTS idx_url_history_category ON url_history(category);
CREATE INDEX IF NOT EXISTS idx_user_state_user_id ON user_state(user_id);
CREATE INDEX IF NOT EXISTS idx_user_state_locked_in ON user_state(locked_in);
