import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Centralized configuration management for FireVision.
    """
    
    # Base Directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # API & Network Settings
    MOBILE_ALERT_IP = os.getenv("MOBILE_ALERT_IP", "127.0.0.1")
    ALERT_API_PORT = int(os.getenv("ALERT_API_PORT", 58766))
    
    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///firevision.db")
    
    # Path Configurations
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    # Ensure necessary directories exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Debug mode
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

settings = Settings()
