from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+mysqlconnector://root:@localhost:3306/firevision"
    SECRET_KEY: str = "your_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # Go up 3 levels from config.py (core -> backend -> root) then into backend/.env
        # Actually config.py is in backend/core/config.py
        # os.path.dirname(__file__) -> backend/core
        # os.path.dirname(...) -> backend
        # So we want os.path.join(backend_dir, ".env")
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

settings = Settings()
