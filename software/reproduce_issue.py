
import sys
import os
import time

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from backend_client import BackendClient

def verify_camera_creation():
    client = BackendClient()
    
    print(f"Testing connectivity to {client.base_url}...")
    
    # Login
    print("Attempting login...")
    if not client.login("admin@example.com", "1234"): # Try email first
         if not client.login("admin", "1234"): # Fallback to username
             print("❌ Login failed. Cannot proceed.")
             return

    print("✅ Login successful.")
    
    # Check user data
    if client.user_data:
        print(f"User Data: {client.user_data}")
    else:
        print("⚠️ User data is empty!")

    # Create Camera
    camera_name = f"Test_Cam_{int(time.time())}"
    print(f"Creating camera: {camera_name}")
    
    result = client.create_camera(
        name=camera_name,
        ip_address="192.168.1.100",
        location="Lab",
        status="active"
    )
    
    if result:
        print(f"✅ Camera created successfully: {result}")
        print("Verifying persistence...")
        cameras = client.get_cameras()
        print(f"Fetched {len(cameras)} cameras.")
        found = any(c['camera_name'] == camera_name for c in cameras)
        if found:
            print("✅ Camera found in fetched list. Persistence verified.")
        else:
            print("❌ Camera NOT found in fetched list. Persistence FAILED.")
    else:
        print("❌ Camera creation failed.")

if __name__ == "__main__":
    verify_camera_creation()
