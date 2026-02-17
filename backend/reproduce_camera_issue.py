import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/token"
CAMERAS_URL = f"{BASE_URL}/api/cameras/"

def reproduce():
    # 1. Login
    print("Attempting to login...")
    response = requests.post(LOGIN_URL, data={"username": "admin", "password": "1234"})
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. List initial cameras
    print("Listing initial cameras...")
    response = requests.get(CAMERAS_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to list cameras: {response.status_code} {response.text}")
        sys.exit(1)
    initial_cameras = response.json()
    print(f"Initial camera count: {len(initial_cameras)}")
    
    # 3. Create a camera
    new_camera = {
        "camera_name": "Test Camera",
        "ip_address": "192.168.1.100",
        "location": "Test Location",
        "status": "active"
    }
    print(f"Creating camera: {new_camera}")
    response = requests.post(CAMERAS_URL, json=new_camera, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create camera: {response.status_code} {response.text}")
        sys.exit(1)
    created_camera = response.json()
    print(f"Camera created successfully: {created_camera}")
    created_id = created_camera["id"]

    # 4. Verify it exists in list
    print("Verifying camera in list...")
    response = requests.get(CAMERAS_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to list cameras: {response.status_code} {response.text}")
        sys.exit(1)
    final_cameras = response.json()
    print(f"Final camera count: {len(final_cameras)}")
    
    found = False
    for cam in final_cameras:
        if cam["id"] == created_id:
            found = True
            break
            
    if found:
        print("SUCCESS: Camera found in list!")
    else:
        print("FAILURE: Camera NOT found in list!")

if __name__ == "__main__":
    reproduce()
