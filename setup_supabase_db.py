"""
Setup script for BrainBot Supabase database
This script creates all the necessary tables in Supabase for the BrainBot application

Usage:
    python setup_supabase_db.py          # Create tables only
    python setup_supabase_db.py test     # Create tables and insert test data
    python setup_supabase_db.py clean    # Clean database (delete all data)
"""
from supabase import create_client
import sys
import time

# Supabase credentials - same as in simple_app.py
SUPABASE_URL = "https://pieavugnpmilwweysycb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpZWF2dWducG1pbHd3ZXlzeWNiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NDcxMjcsImV4cCI6MjA1OTQyMzEyN30.n7cbXhyZdmyFS2r3wSJNeTvM6xCGrj79D4zGDkDoNws"

# SQL statements to create tables
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

CREATE_URL_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS url_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

CREATE_USER_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_state (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    locked_in BOOLEAN NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    notes TEXT
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_url_history_user_id ON url_history(user_id);
CREATE INDEX IF NOT EXISTS idx_url_history_category ON url_history(category);
CREATE INDEX IF NOT EXISTS idx_user_state_user_id ON user_state(user_id);
CREATE INDEX IF NOT EXISTS idx_user_state_locked_in ON user_state(locked_in);
"""

# Sample data for testing
INSERT_TEST_USER = """
INSERT INTO users (id, created_at, updated_at)
VALUES ('test_user', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
"""

INSERT_TEST_URLS = """
INSERT INTO url_history (user_id, url, category, timestamp)
VALUES 
    ('test_user', 'https://github.com', 'productive', NOW() - INTERVAL '1 hour'),
    ('test_user', 'https://stackoverflow.com', 'productive', NOW() - INTERVAL '45 minutes'),
    ('test_user', 'https://youtube.com', 'unproductive', NOW() - INTERVAL '30 minutes'),
    ('test_user', 'https://docs.google.com', 'productive', NOW() - INTERVAL '15 minutes'),
    ('test_user', 'https://reddit.com', 'unproductive', NOW() - INTERVAL '5 minutes')
ON CONFLICT DO NOTHING;
"""

INSERT_TEST_STATE = """
INSERT INTO user_state (user_id, locked_in, start_time, end_time, duration, notes)
VALUES 
    ('test_user', TRUE, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', 3600, 'Productive study session'),
    ('test_user', FALSE, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes', 1800, 'Break time'),
    ('test_user', TRUE, NOW() - INTERVAL '30 minutes', NULL, NULL, 'Currently studying')
ON CONFLICT DO NOTHING;
"""

# SQL to clean the database
CLEAN_DATABASE = """
DELETE FROM user_state;
DELETE FROM url_history;
DELETE FROM users;
"""

# Get command line argument
mode = sys.argv[1] if len(sys.argv) > 1 else "create"

try:
    # Initialize Supabase client
    print("🚀 Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
    
    if mode == "clean":
        # Clean the database
        print("\n🧹 Cleaning database...")
        supabase.postgrest.rpc('exec_sql', {'query': CLEAN_DATABASE}).execute()
        print("✅ Database cleaned! All data has been deleted.")
        sys.exit(0)
    
    # Create tables
    print("\n📊 Creating tables...")
    
    # Execute SQL statements using Supabase's PostgreSQL interface
    # Users table
    print("Creating users table...")
    supabase.postgrest.rpc('exec_sql', {'query': CREATE_USERS_TABLE}).execute()
    print("✅ Users table created")
    
    # URL history table
    print("Creating url_history table...")
    supabase.postgrest.rpc('exec_sql', {'query': CREATE_URL_HISTORY_TABLE}).execute()
    print("✅ URL history table created")
    
    # User state table
    print("Creating user_state table...")
    supabase.postgrest.rpc('exec_sql', {'query': CREATE_USER_STATE_TABLE}).execute()
    print("✅ User state table created")
    
    # Create indexes
    print("Creating indexes...")
    supabase.postgrest.rpc('exec_sql', {'query': CREATE_INDEXES}).execute()
    print("✅ Indexes created")
    
    # Insert test data if requested
    if mode == "test":
        print("\n🧪 Inserting test data...")
        
        # Test user
        print("Inserting test user...")
        supabase.postgrest.rpc('exec_sql', {'query': INSERT_TEST_USER}).execute()
        print("✅ Test user inserted")
        
        # Test URLs
        print("Inserting test URLs...")
        supabase.postgrest.rpc('exec_sql', {'query': INSERT_TEST_URLS}).execute()
        print("✅ Test URLs inserted")
        
        # Test state
        print("Inserting test state data...")
        supabase.postgrest.rpc('exec_sql', {'query': INSERT_TEST_STATE}).execute()
        print("✅ Test state data inserted")
    
    print("\n🎉 Database setup complete!")
    print("You can now run your Flask backend with: python simple_app.py")
    
except Exception as e:
    print(f"\n❌ Error setting up database: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure your Supabase URL and API key are correct")
    print("2. Check if you have the 'exec_sql' RPC function enabled in your Supabase project")
    print("3. If 'exec_sql' is not available, you may need to run the SQL manually in the Supabase SQL Editor")
    
    # If exec_sql fails, print the SQL for manual execution
    print("\n📝 SQL for manual execution in Supabase SQL Editor:")
    print("\n-- Users table")
    print(CREATE_USERS_TABLE)
    print("\n-- URL history table")
    print(CREATE_URL_HISTORY_TABLE)
    print("\n-- User state table")
    print(CREATE_USER_STATE_TABLE)
    print("\n-- Indexes")
    print(CREATE_INDEXES)
    print("\n-- Test data (optional)")
    print(INSERT_TEST_USER)
    print(INSERT_TEST_URLS)
    print(INSERT_TEST_STATE)
    
    sys.exit(1)
