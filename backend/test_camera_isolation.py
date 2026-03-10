import requests
import time

BASE_URL = "http://127.0.0.1:8000/api"

def test_camera_isolation():
    print("Starting verification for Camera Isolation...")

    # 1. Create two users
    user_a_email = f"user_a_{int(time.time())}@example.com"
    user_b_email = f"user_b_{int(time.time())}@example.com"
    password = "password123"

    print(f"Creating User A: {user_a_email}")
    requests.post(f"{BASE_URL}/users/", json={"email": user_a_email, "name": "User A", "password": password})
    
    print(f"Creating User B: {user_b_email}")
    requests.post(f"{BASE_URL}/users/", json={"email": user_b_email, "name": "User B", "password": password})

    # 2. Login as User A
    print("Logging in as User A...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": user_a_email, "password": password})
    token_a = resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 3. Create Camera as User A
    print("Creating Camera as User A...")
    cam_resp = requests.post(f"{BASE_URL}/cameras/", json={"camera_name": "Camera A", "ip_address": "1.1.1.1"}, headers=headers_a)
    camera_a_id = cam_resp.json()["id"]
    print(f"Camera A created with ID: {camera_a_id}")

    # 4. Login as User B
    print("Logging in as User B...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": user_b_email, "password": password})
    token_b = resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 5. Verify User B cannot see User A's camera
    print("Verifying User B cannot see User A's camera in list...")
    list_resp = requests.get(f"{BASE_URL}/cameras/", headers=headers_b)
    cameras_b = list_resp.json()
    if any(c["id"] == camera_a_id for c in cameras_b):
        print("FAIL: User B can see User A's camera in list!")
    else:
        print("SUCCESS: User B cannot see User A's camera in list.")

    print("Verifying User B cannot fetch User A's camera directly...")
    single_resp = requests.get(f"{BASE_URL}/cameras/{camera_a_id}", headers=headers_b)
    if single_resp.status_code == 403:
        print("SUCCESS: User B got 403 when trying to fetch User A's camera.")
    else:
        print(f"FAIL: User B got {single_resp.status_code} when trying to fetch User A's camera.")

    # 6. Login as Admin
    print("Logging in as Admin...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": "admin", "password": "1234"})
    token_admin = resp.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 7. Verify Admin can see User A's camera
    print("Verifying Admin can see User A's camera...")
    list_resp = requests.get(f"{BASE_URL}/cameras/", headers=headers_admin)
    cameras_admin = list_resp.json()
    if any(c["id"] == camera_a_id for c in cameras_admin):
        print("SUCCESS: Admin can see User A's camera.")
    else:
        print("FAIL: Admin cannot see User A's camera.")

if __name__ == "__main__":
    try:
        test_camera_isolation()
    except Exception as e:
        print(f"An error occurred: {e}")
