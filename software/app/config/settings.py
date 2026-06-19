import os
from dotenv import load_dotenv

# Load .env file if present in the software directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

class ClientSettings:
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    MOBILE_APP_URL: str = os.getenv("MOBILE_APP_URL", "http://192.168.1.4:58766")
    ALERT_API_PORT: int = int(os.getenv("ALERT_API_PORT", 58766))
    
    # AI thresholds
    FIRE_THRESHOLD: float = float(os.getenv("FIRE_THRESHOLD", 0.5))
    SMOKE_THRESHOLD: float = float(os.getenv("SMOKE_THRESHOLD", 0.6))
    PROCESS_EVERY_N_FRAMES: int = int(os.getenv("PROCESS_EVERY_N_FRAMES", 2))
    NIGHT_MODE_ENABLED: bool = os.getenv("NIGHT_MODE_ENABLED", "True").lower() == "true"
    TEMPORAL_CHECK_ENABLED: bool = os.getenv("TEMPORAL_CHECK_ENABLED", "True").lower() == "true"

client_settings = ClientSettings()
