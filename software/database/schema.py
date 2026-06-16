"""
Schema definitions for the local SQLCipher database.
"""

SCHEMA = """
-- Use Write-Ahead Logging for better concurrency and crash resilience
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'operator',
    created_at REAL NOT NULL,
    last_login REAL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tokens (
    user_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expiry REAL NOT NULL,
    last_validation REAL NOT NULL,
    device_fingerprint TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_status TEXT,
    plan TEXT,
    expiry REAL,
    camera_limit INTEGER,
    last_synced REAL
);

CREATE TABLE IF NOT EXISTS sync_queue (
    event_uuid TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,  -- Encrypted JSON payload
    timestamp REAL NOT NULL,
    retry_count INTEGER DEFAULT 0,
    priority TEXT DEFAULT 'LOW', -- CRITICAL, HIGH, MEDIUM, LOW
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    description TEXT,
    timestamp REAL NOT NULL,
    user_id TEXT,
    status TEXT
);
"""
