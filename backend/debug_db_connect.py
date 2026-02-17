import sys
import os
sys.path.append(os.getcwd())

from backend.core.config import settings
from sqlalchemy import create_engine

# Print what setting has been loaded
print(f"DEBUG: Loaded DATABASE_URL: '{settings.DATABASE_URL}'")

try:
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    print("SUCCESS! Connected via SQLAlchemy.")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
