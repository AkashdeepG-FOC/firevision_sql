from sqlalchemy import create_engine, text
from backend.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if columns exist (MySQL specific query for brevity, or just try-except)
            print("Attempting to rename assigned_user_id to user_id in 'cameras' table...")
            conn.execute(text("ALTER TABLE cameras CHANGE COLUMN assigned_user_id user_id INT"))
            conn.commit()
            print("Successfully renamed column.")
        except Exception as e:
            print(f"Note: {e}")
            print("Column might already be renamed or another issue occurred. Checking if user_id exists...")
            try:
                # If the above failed, maybe user_id already exists from a fresh create_all
                result = conn.execute(text("SHOW COLUMNS FROM cameras LIKE 'user_id'")).fetchone()
                if result:
                    print("Column 'user_id' already exists.")
                else:
                    print("Adding 'user_id' column...")
                    conn.execute(text("ALTER TABLE cameras ADD COLUMN user_id INT, ADD FOREIGN KEY (user_id) REFERENCES users(id)"))
                    conn.commit()
            except Exception as e2:
                print(f"Migration error: {e2}")

if __name__ == "__main__":
    migrate()
