"""
Verification Script: Test Camera Creation After Fix

This script verifies that the camera storage issue has been fixed by:
1. Logging in as admin
2. Creating a camera via the API
3. Verifying it persists in the database
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/token"
CAMERAS_URL = f"{BASE_URL}/api/cameras/"

def verify_fix():
    print("=" * 60)
    print("CAMERA STORAGE FIX VERIFICATION")
    print("=" * 60)
    
    # 1. Login
    print("\n[1/4] Logging in as admin...")
    response = requests.post(LOGIN_URL, data={"username": "admin", "password": "1234"})
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # 2. Get initial camera count
    print("\n[2/4] Getting initial camera count...")
    response = requests.get(CAMERAS_URL, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to list cameras: {response.status_code} {response.text}")
        return False
    initial_cameras = response.json()
    initial_count = len(initial_cameras)
    print(f"✅ Initial camera count: {initial_count}")
    
    # 3. Create a new camera
    new_camera = {
        "camera_name": "Verification Test Camera",
        "ip_address": "192.168.1.200",
        "location": "Verification Test Location",
        "status": "active"
    }
    print(f"\n[3/4] Creating camera: {new_camera['camera_name']}")
    response = requests.post(CAMERAS_URL, json=new_camera, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create camera: {response.status_code} {response.text}")
        return False
    created_camera = response.json()
    created_id = created_camera["id"]
    print(f"✅ Camera created successfully with ID: {created_id}")

    # 4. Verify it persists
    print(f"\n[4/4] Verifying camera persists in database...")
    response = requests.get(CAMERAS_URL, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to list cameras: {response.status_code} {response.text}")
        return False
    final_cameras = response.json()
    final_count = len(final_cameras)
    
    found = False
    for cam in final_cameras:
        if cam["id"] == created_id:
            found = True
            print(f"✅ Camera found in database:")
            print(f"   - ID: {cam['id']}")
            print(f"   - Name: {cam['camera_name']}")
            print(f"   - IP: {cam['ip_address']}")
            print(f"   - Location: {cam['location']}")
            print(f"   - Status: {cam['status']}")
            break
    
    print(f"\n📊 Summary:")
    print(f"   - Initial cameras: {initial_count}")
    print(f"   - Final cameras: {final_count}")
    print(f"   - Camera persisted: {'✅ YES' if found else '❌ NO'}")
    
    if found and final_count == initial_count + 1:
        print("\n" + "=" * 60)
        print("✅ VERIFICATION PASSED: Camera storage is working correctly!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ VERIFICATION FAILED: Camera was not properly stored")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = verify_fix()
    sys.exit(0 if success else 1)
