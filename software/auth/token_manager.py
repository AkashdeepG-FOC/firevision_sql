import time
from database.local_db import LocalDB
from auth.key_manager import KeyManager
from auth.device_binding import get_device_fingerprint, verify_device_fingerprint

# 7 days in seconds
OFFLINE_EXPIRY_SECONDS = 7 * 24 * 60 * 60

class TokenManager:
    def __init__(self):
        self.db = LocalDB()
        
    def cache_token(self, user_id: str, access_token: str, refresh_token: str = None):
        """Encrypt and cache token locally after a successful online login."""
        encrypted_access = KeyManager.encrypt_data(access_token)
        encrypted_refresh = KeyManager.encrypt_data(refresh_token) if refresh_token else None
        
        now = time.time()
        expiry = now + OFFLINE_EXPIRY_SECONDS
        device_fingerprint = get_device_fingerprint()
        
        query = """
        INSERT INTO tokens (user_id, access_token, refresh_token, expiry, last_validation, device_fingerprint)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            access_token=excluded.access_token,
            refresh_token=excluded.refresh_token,
            expiry=excluded.expiry,
            last_validation=excluded.last_validation,
            device_fingerprint=excluded.device_fingerprint
        """
        self.db.execute_query(query, (user_id, encrypted_access, encrypted_refresh, expiry, now, device_fingerprint))
        
    def validate_offline_token(self, user_id: str) -> dict:
        """
        Validate offline token for expiry and device binding.
        Returns dict with status and details.
        """
        row = self.db.fetch_one("SELECT * FROM tokens WHERE user_id = ?", (user_id,))
        if not row:
            return {"valid": False, "reason": "no_token"}
            
        now = time.time()
        if now > row['expiry']:
            return {"valid": False, "reason": "expired"}
            
        if not verify_device_fingerprint(row['device_fingerprint']):
            return {"valid": False, "reason": "device_mismatch"}
            
        try:
            decrypted_token = KeyManager.decrypt_data(row['access_token'])
            return {
                "valid": True, 
                "token": decrypted_token,
                "days_remaining": (row['expiry'] - now) / (24*3600)
            }
        except Exception as e:
            return {"valid": False, "reason": f"decryption_failed: {str(e)}"}

    def clear_token(self, user_id: str):
        """Remove cached token on explicit logout."""
        self.db.execute_query("DELETE FROM tokens WHERE user_id = ?", (user_id,))
