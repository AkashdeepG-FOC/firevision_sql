import requests
import os
import json
from typing import Dict, Any, Optional, List

class BackendClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.user_data = None

    def login(self, username, password) -> bool:
        try:
            # Login expects username/password form data (OAuth2)
            # For our backend, username field maps to email in the user model if we look at auth.py
            # But let's check auth.py. "user = db.query(models.User).filter(models.User.email == form_data.username).first()"
            # So "username" param sent to token endpoint corresponds to email in DB.
            
            response = requests.post(
                f"{self.base_url}/api/auth/token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                # Fetch user details
                self.fetch_current_user()
                return True
            print(f"Login failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"Login connection failed: {e}")
            return False

    def get_headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_current_user(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/users/me",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                self.user_data = response.json()
                return self.user_data
        except Exception as e:
            print(f"Error fetching user: {e}")
        return None

    def create_user(self, email, password, name, role="operator") -> bool:
        try:
            payload = {
                "email": email,
                "password": password,
                "name": name,
                "role": role
            }
            response = requests.post(
                f"{self.base_url}/api/users/",
                json=payload,
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    # --- Cameras ---
    def get_cameras(self) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/cameras/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            print(f"DEBUG: get_cameras failed with status {response.status_code}: {response.text}")
            return []
        except Exception as e:
            print(f"Error getting cameras: {e}")
            return []

    def create_camera(self, name, ip_address, location="", status="active") -> Optional[Dict]:
        try:
            # Need to check assigned_user_id. The backend model expects it.
            # If logged in, we can use self.user_data['id']
            user_id = self.user_data['id'] if self.user_data else None
            
            # For webcams, ip_address might be None. Provide a descriptive default.
            if ip_address is None:
                ip_address = "local_webcam"
            
            payload = {
                "camera_name": name,
                "ip_address": ip_address,
                "location": location,
                "status": status,
                "assigned_user_id": user_id
            }
            print(f"DEBUG: Sending camera create payload: {payload}, Header: {self.get_headers()}")
            response = requests.post(
                f"{self.base_url}/api/cameras/",
                json=payload,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                print(f"✅ Camera created: {response.json()}")
                return response.json()
            else:
                print(f"❌ Create camera failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error creating camera: {e}")
            import traceback
            traceback.print_exc()
        return None

    # --- Users ---
    def get_users(self) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/users/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting users: {e}")
            return []

    def update_user(self, user_id: int, data: Dict) -> bool:
        try:
            response = requests.put(
                f"{self.base_url}/api/users/{user_id}",
                json=data,
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        try:
            response = requests.delete(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    # --- Logs ---
    def create_log(self, action_type: str, description: str, performed_by: str = "system") -> bool:
        try:
            payload = {
                "action_type": action_type,
                "description": description,
                "performed_by": performed_by
            }
            response = requests.post(
                f"{self.base_url}/api/logs/",
                json=payload,
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error creating log: {e}")
            return False

    def get_logs(self, limit: int = 100) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/logs/?limit={limit}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []

    # --- Alerts ---
    def create_alert(self, camera_id: int, alert_type: str, confidence: float, 
                    image_path: str = None, video_path: str = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "camera_id": camera_id,
                "alert_type": alert_type,
                "confidence_score": confidence,
                "image_path": image_path,
                "video_path": video_path
            }
            response = requests.post(
                f"{self.base_url}/api/alerts/",
                json=payload,
                headers=self.get_headers()
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error creating alert: {e}")
            return None

# Singleton instance
backend_client = BackendClient()
