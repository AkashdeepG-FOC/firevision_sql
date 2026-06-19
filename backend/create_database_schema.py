import psycopg2
from urllib.parse import urlparse
from backend.core.config import settings

def create_database():
    db_url = settings.DATABASE_URL
    # psycopg2 expects postgresql:// or postgres://, not postgresql+psycopg2://
    if db_url.startswith("postgresql+psycopg2://"):
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
        
    print(f"Checking database connection for URL: {db_url}")
    
    # Try to connect directly to the target database
    try:
        conn = psycopg2.connect(db_url)
        print("Successfully connected to the database!")
        conn.close()
        return
    except Exception as e:
        print(f"Could not connect directly to the target database: {e}")
        print("Attempting to connect to default 'postgres' database to check/create target database...")
        
    try:
        # Parse connection URL to connect to default 'postgres' DB and create the target
        parsed = urlparse(db_url)
        db_name = parsed.path.lstrip('/')
        
        # Build url for default postgres database
        # Replace the database name at the end of path
        netloc = parsed.netloc
        # Use postgresql schema (psycopg2 can use postgres:// or postgresql://)
        default_url = f"postgresql://{netloc}/postgres"
        
        # For connection string format to work with psycopg2, we need to convert driver from postgresql+psycopg2 to postgresql
        if default_url.startswith("postgresql+psycopg2://"):
            default_url = default_url.replace("postgresql+psycopg2://", "postgresql://")
            
        conn = psycopg2.connect(default_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists on server.")
            
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error checking/creating database: {err}")
        print("Note: Make sure the database is created manually in your Supabase dashboard or local Postgres.")

if __name__ == "__main__":
    create_database()
