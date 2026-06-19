from sqlalchemy import create_engine, text
from backend.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if columns exist using standard ANSI SQL information_schema
            print("Checking if 'user_id' already exists in 'cameras' table...")
            check_user_id_query = text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'cameras' AND column_name = 'user_id'"
            )
            result = conn.execute(check_user_id_query).fetchone()
            
            if result:
                print("Column 'user_id' already exists.")
                return
                
            # Check if assigned_user_id exists to rename it
            print("Checking if 'assigned_user_id' exists in 'cameras' table...")
            check_assigned_query = text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'cameras' AND column_name = 'assigned_user_id'"
            )
            assigned_result = conn.execute(check_assigned_query).fetchone()
            
            if assigned_result:
                print("Attempting to rename assigned_user_id to user_id in 'cameras' table...")
                conn.execute(text("ALTER TABLE cameras RENAME COLUMN assigned_user_id TO user_id"))
                conn.commit()
                print("Successfully renamed column.")
            else:
                print("Adding 'user_id' column...")
                conn.execute(text(
                    "ALTER TABLE cameras ADD COLUMN user_id INT, "
                    "ADD CONSTRAINT fk_cameras_user FOREIGN KEY (user_id) REFERENCES users(id)"
                ))
                conn.commit()
                print("Successfully added 'user_id' column and foreign key constraint.")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate()
