import os
import threading
from datetime import datetime

try:
    from pysqlcipher3 import dbapi2 as sqlite3
    HAS_SQLCIPHER = True
    print("Using SQLCipher for encrypted database.")
except ImportError:
    import sqlite3
    HAS_SQLCIPHER = False
    print("Warning: pysqlcipher3 not found. Falling back to standard sqlite3.")
    print("For enterprise deployment, ensure pysqlcipher3 is compiled and installed.")

from database.schema import SCHEMA

class LocalDB:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path="local_auth.db", key=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LocalDB, cls).__new__(cls)
                cls._instance._init_db(db_path, key)
            return cls._instance
            
    def _init_db(self, db_path, key):
        self.db_path = db_path
        self.key = key
        # We don't keep a single connection because SQLite connections shouldn't be shared across threads
        # Instead, we provide a context manager/getter
        
        # Initialize schema
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(SCHEMA)
            conn.commit()
            
    def get_connection(self):
        """Get a thread-safe database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        if HAS_SQLCIPHER and self.key:
            # Set the encryption key for SQLCipher
            conn.execute(f"PRAGMA key='{self.key}'")
            
        # Enable WAL mode for graceful shutdown recovery and concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def execute_query(self, query, params=()):
        """Execute a query and commit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_one(self, query, params=()):
        """Fetch a single row"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=()):
        """Fetch all rows"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
