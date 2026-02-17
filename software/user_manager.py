from config_manager import ConfigManager
import requests

class UserManager:
    """User management using ConfigManager for persistence and backend API for cameras/employees"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.backend_url = "http://localhost:5000/api"
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        return self.config_manager.authenticate_user(username, password)
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> bool:
        """Create a new user"""
        return self.config_manager.create_user(username, password, email, role)
    
    def get_user_info(self, username: str):
        """Get user information from backend if available, else from config"""
        try:
            url = f"{self.backend_url}/config/users"
            resp = requests.get(url)
            if resp.ok:
                users = resp.json().get("data", [])
                for user in users:
                    if user["username"] == username:
                        return user
        except Exception as e:
            print(f"Error fetching user info from backend: {e}")
        # fallback to local config
        users = self.config_manager.load_users()
        return users.get(username)

    def add_camera_to_user(self, username: str, camera_data: dict) -> bool:
        """Add a camera to the user's cameras array via backend API, ensuring all required fields are present"""
        try:
            camera_payload = self._build_camera_payload(camera_data)
            url = f"{self.backend_url}/users/{username}/cameras"
            resp = requests.post(url, json=camera_payload)
            return resp.ok
        except Exception as e:
            print(f"Error adding camera to user: {e}")
            return False

    def add_employee_to_user(self, username: str, employee_data: dict) -> bool:
        """Add an employee/member to the user's employees array via backend API, ensuring all required fields are present"""
        try:
            employee_payload = self._build_employee_payload(employee_data)
            url = f"{self.backend_url}/users/{username}/employees"
            resp = requests.post(url, json=employee_payload)
            return resp.ok
        except Exception as e:
            print(f"Error adding employee to user: {e}")
            return False

    def _build_camera_payload(self, data: dict) -> dict:
        """Ensure all required camera fields are present for backend schema"""
        from datetime import datetime
        return {
            "camera_id": data.get("camera_id") or data.get("id") or "cam_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "name": data.get("name", "Unnamed Camera"),
            "source": data.get("source", ""),
            "type": data.get("type", "ip_camera"),
            "added_date": data.get("added_date") or datetime.now().isoformat(),
            "status": data.get("status", "inactive")
        }

    def _build_employee_payload(self, data: dict) -> dict:
        """Ensure all required employee fields are present for backend schema"""
        from datetime import datetime
        return {
            "employee_id": data.get("employee_id") or "emp_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "name": data.get("name", "Unnamed Employee"),
            "email": data.get("email", ""),
            "access": data.get("access", "viewer")
        }
