import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables for DB connection
load_dotenv('backend/.env')

def migrate():
    db_name = os.getenv('DB_NAME', 'firevision')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()

        print(f"Applying migrations to database: {db_name}...")

        # Add missing columns to alerts table
        columns_to_add = [
            ("severity", "VARCHAR(50) DEFAULT 'low'"),
            ("description", "VARCHAR(255)"),
            ("status", "VARCHAR(50) DEFAULT 'active'"),
            ("footage_path", "VARCHAR(255)"),
            ("acknowledged_at", "DATETIME(6)"),
            ("resolved_at", "DATETIME(6)")
        ]

        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added column: {col_name}")
            except mysql.connector.Error as err:
                if err.errno == 1060: # Column already exists
                    print(f"ℹ️ Column already exists: {col_name}")
                else:
                    print(f"❌ Error adding column {col_name}: {err}")

        conn.commit()
        print("🎉 Migration completed successfully!")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
