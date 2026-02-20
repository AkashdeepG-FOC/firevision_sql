
import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from backend_client import backend_client

def test_camera_fetch():
    print("Testing Camera Fetch...")
    
    # Initialize ConfigManager
    config_manager = ConfigManager()
    
    # Simulate login (you might need to provide valid credentials if auth is required)
    # For now, let's see if we can fetch without login or if we need it.
    # The code in backend_client.get_cameras uses self.get_headers() which uses self.token.
    # So we probably need to login first.
    
    # Try with a default user if known, or just check what happens without login.
    print("Attempting to fetch cameras without login...")
    cameras = config_manager.load_cameras()
    print(f"Cameras fetched (no login): {cameras}")
    
    # If empty, maybe try to login?
    # backend_client.login("admin", "password") # Hypothetical
    
    # Check if backend is reachable
    try:
        import requests
        resp = requests.get("http://localhost:5000/api/health") # Adjust URL if needed
        print(f"Backend Health Check: {resp.status_code}")
    except Exception as e:
        print(f"Backend unreachable: {e}")

if __name__ == "__main__":
    test_camera_fetch()
