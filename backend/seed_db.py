from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models import models
from backend.core.security import get_password_hash

def seed_db():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin_email = "admin@example.com" # Default admin
        # Also maintain compatibility with old "admin" username if possible, 
        # but our schema enforces email. We'll use "admin" as email for strictly local lookalike 
        # or just a proper email. Let's use "admin" as email to match partial username logic if validation permits,
        # otherwise "admin@example.com".
        
        # In `users.py` schema, it's just a string, but `email-validator` might be used in logic.
        # Let's create a robust admin.
        
        user = db.query(models.User).filter(models.User.email == "admin").first()
        if not user:
            print("Creating default admin user...")
            db_user = models.User(
                email="admin",
                name="Administrator",
                password_hash=get_password_hash("1234"), # Default password from previous system
                role="admin"
            )
            db.add(db_user)
            db.commit()
            print("Default admin created: admin / 1234")
        else:
            print("Admin user already exists.")
            
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
