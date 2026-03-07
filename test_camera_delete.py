import requests

BASE_URL = "http://localhost:8000"

# login
login_data = {"username": "akash", "password": "1234"}
response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get cameras
response = requests.get(f"{BASE_URL}/api/cameras/", headers=headers)
cameras = response.json()
print(f"Cameras found: {len(cameras)}")

if cameras:
    cam_id = cameras[0]['id']
    print(f"Attempting to delete camera ID: {cam_id}")
    del_resp = requests.delete(f"{BASE_URL}/api/cameras/{cam_id}", headers=headers)
    print(f"Delete response ({del_resp.status_code}): {del_resp.text}")

# Verify deletion
response = requests.get(f"{BASE_URL}/api/cameras/", headers=headers)
cameras = response.json()
print(f"Cameras remaining: {len(cameras)}")
