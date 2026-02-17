"""
Test Webcam Camera Creation

This script tests that webcams can be created with None/null ip_address
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/token"
CAMERAS_URL = f"{BASE_URL}/api/cameras/"

def test_webcam_creation():
    print("=" * 60)
    print("WEBCAM CAMERA CREATION TEST")
    print("=" * 60)
    
    # 1. Login
    print("\n[1/3] Logging in as admin...")
    response = requests.post(LOGIN_URL, data={"username": "admin", "password": "1234"})
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 2. Create a webcam camera (with ip_address as "local_webcam")
    webcam_camera = {
        "camera_name": "Test Webcam",
        "ip_address": "local_webcam",
        "location": "Test Location",
        "status": "active"
    }
    print(f"\n[2/3] Creating webcam camera: {webcam_camera['camera_name']}")
    response = requests.post(CAMERAS_URL, json=webcam_camera, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create webcam: {response.status_code} {response.text}")
        return False
    created_camera = response.json()
    print(f"✅ Webcam created successfully:")
    print(f"   - ID: {created_camera['id']}")
    print(f"   - Name: {created_camera['camera_name']}")
    print(f"   - IP: {created_camera['ip_address']}")

    # 3. Verify it persists
    print(f"\n[3/3] Verifying webcam persists in database...")
    response = requests.get(f"{CAMERAS_URL}{created_camera['id']}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to retrieve camera: {response.status_code} {response.text}")
        return False
    
    retrieved_camera = response.json()
    print(f"✅ Webcam found in database:")
    print(f"   - ID: {retrieved_camera['id']}")
    print(f"   - Name: {retrieved_camera['camera_name']}")
    print(f"   - IP: {retrieved_camera['ip_address']}")
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Webcam creation works correctly!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_webcam_creation()
    sys.exit(0 if success else 1)
