import keyring
import base64
from cryptography.fernet import Fernet
import os

APP_NAME = "FireVisionPro"
KEY_NAME = "LocalEncryptionKey"

class KeyManager:
    @staticmethod
    def get_or_create_key() -> str:
        """
        Retrieve the master encryption key from the OS secure keystore (Credential Locker).
        If it doesn't exist, generate a new one and securely store it.
        """
        try:
            key = keyring.get_password(APP_NAME, KEY_NAME)
            if not key:
                # Generate a new Fernet-compatible URL-safe base64 key
                key = Fernet.generate_key().decode('utf-8')
                keyring.set_password(APP_NAME, KEY_NAME, key)
            return key
        except Exception as e:
            print(f"Warning: Secure keystore unavailable ({e}). Using local fallback.")
            # Fallback for environments where keyring fails
            return KeyManager._get_fallback_key()

    @staticmethod
    def _get_fallback_key() -> str:
        """Fallback key generation if OS credential store is unavailable."""
        fallback_path = os.path.join(os.path.expanduser("~"), ".firevision", ".enc_key")
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r') as f:
                return f.read().strip()
        else:
            key = Fernet.generate_key().decode('utf-8')
            with open(fallback_path, 'w') as f:
                f.write(key)
            # Make the fallback file read-only on Windows
            if os.name == 'nt':
                os.system(f'attrib +h "{fallback_path}"')
            return key

    @staticmethod
    def get_fernet_instance() -> Fernet:
        """Get an initialized Fernet instance for data encryption/decryption."""
        key = KeyManager.get_or_create_key()
        return Fernet(key.encode('utf-8'))

    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt string data."""
        f = KeyManager.get_fernet_instance()
        return f.encrypt(data.encode('utf-8')).decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypt string data."""
        f = KeyManager.get_fernet_instance()
        return f.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
