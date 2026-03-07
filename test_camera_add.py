import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Login to get token
login_data = {"username": "akash", "password": "1234"}
response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
if response.status_code != 200:
    print(f"Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Try creating a camera with int source (like webcam 0)
payload = {
    "camera_name": "Test Webcam",
    "ip_address": 0,
    "location": "Local",
    "status": "active",
    "assigned_user_id": 1 # Assume akash is ID 1
}

print(f"Testing with payload: {payload}")
response = requests.post(f"{BASE_URL}/api/cameras/", json=payload, headers=headers)
print(f"Response ({response.status_code}): {response.text}")

# 3. Try with string source
payload["ip_address"] = "0"
print(f"Testing with payload: {payload}")
response = requests.post(f"{BASE_URL}/api/cameras/", json=payload, headers=headers)
print(f"Response ({response.status_code}): {response.text}")
