import time
import uuid
from backend_client import backend_client
from database.local_db import LocalDB
from auth.password_utils import hash_password, verify_password
from auth.token_manager import TokenManager

class AuthManager:
    """Orchestrates Online and Offline authentication flows."""
    
    def __init__(self):
        self.db = LocalDB()
        self.token_manager = TokenManager()
        
    def authenticate(self, username: str, password: str) -> dict:
        """
        Main entry point for login.
        Attempts online login, falls back to offline.
        """
        # Try Online Login
        status, details = self._online_login(username, password)
        
        if status == "success":
            return {"status": "success", "mode": "online", "details": details}
        elif status == "invalid_credentials":
            return {"status": "invalid_credentials", "message": "Invalid username or password"}
        elif status == "offline":
            # Fall back to offline login
            offline_status, offline_details = self._offline_login(username, password)
            if offline_status == "success":
                return {"status": "success", "mode": "offline", "details": offline_details}
            else:
                return {"status": "offline_failed", "message": offline_details.get("reason", "Offline login failed")}
                
        return {"status": "error", "message": "Unknown error during authentication"}

    def _online_login(self, username: str, password: str):
        """Execute online login flow via API."""
        if not backend_client.test_connection():
            return "offline", {}
            
        login_result = backend_client.login(username, password)
        if login_result == "success":
            user_data = backend_client.user_data
            if not user_data:
                return "error", {"reason": "Missing user data from backend"}
                
            # Update Local DB Cache
            user_id = str(user_data.get("id", ""))
            if not user_id:
                # If API didn't return an ID, try fetching it or generate one locally
                user_id = str(uuid.uuid4()) # Fallback
                
            email = user_data.get("email", username)
            name = user_data.get("name", username)
            role = user_data.get("role", "operator")
            
            self._update_local_user_cache(user_id, name, email, password, role)
            
            # Cache Token
            self.token_manager.cache_token(user_id, backend_client.token)
            
            return "success", user_data
            
        elif login_result == "invalid_credentials":
            return "invalid_credentials", {}
        else:
            return "offline", {} # Consider other errors as offline fallback trigger

    def _offline_login(self, username: str, password: str):
        """Execute offline login flow using Local DB."""
        # We assume username could be email or username in the DB.
        user_row = self.db.fetch_one("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        
        if not user_row:
            return "failed", {"reason": "User not found in local cache. Please log in online first."}
            
        if not verify_password(password, user_row['password_hash']):
            return "failed", {"reason": "Invalid password."}
            
        if not user_row['is_active']:
            return "failed", {"reason": "Account is disabled."}
            
        # Validate offline token expiry and device binding
        user_id = user_row['id']
        token_validation = self.token_manager.validate_offline_token(user_id)
        
        if not token_validation["valid"]:
            return "failed", {"reason": f"Offline login expired or invalid: {token_validation['reason']}. Please log in online."}
            
        # Success! Update last_login
        self.db.execute_query("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user_id))
        
        return "success", {
            "id": user_id,
            "username": user_row['username'],
            "email": user_row['email'],
            "role": user_row['role'],
            "offline_days_remaining": token_validation["days_remaining"]
        }
        
    def _update_local_user_cache(self, user_id: str, username: str, email: str, password: str, role: str):
        """Update the local SQLite user cache with bcrypt hashed password."""
        hashed_pwd = hash_password(password)
        now = time.time()
        
        query = """
        INSERT INTO users (id, username, email, password_hash, role, created_at, last_login, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(id) DO UPDATE SET
            username=excluded.username,
            email=excluded.email,
            password_hash=excluded.password_hash,
            role=excluded.role,
            last_login=excluded.last_login
        """
        self.db.execute_query(query, (user_id, username, email, hashed_pwd, role, now, now))
