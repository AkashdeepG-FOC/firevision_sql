import hashlib
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal

class LoginManager(QObject):
    login_success = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)   # error message

    def __init__(self, users_file="users.json"):
        super().__init__()
        self.users_file = users_file
        self.current_user = None
        self.users = self._load_users()

    def _load_users(self):
        """
        Load users from file

        Returns:
            dict: Users dictionary
        """
        default_users = {
            "admin": {
                "password_hash": self._hash_password("1234"),
                "role": "admin",
                "created": "2025-01-01",
                "last_login": None
            }
        }

        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, "r") as f:
                    users = json.load(f)
                return users
        except Exception as e:
            print(f"Error loading users: {e}")

        # Save default users
        self._save_users(default_users)
        return default_users

    def _save_users(self, users=None):
        """
        Save users to file

        Args:
            users (dict, optional): Users dictionary, uses self.users if None

        Returns:
            bool: True if users saved successfully, False otherwise
        """
        if users is None:
            users = self.users

        try:
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False

    def _hash_password(self, password):
        """
        Hash a password using SHA-256

        Args:
            password (str): Plain text password

        Returns:
            str: Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """
        Authenticate a user

        Args:
            username (str): Username
            password (str): Password

        Returns:
            bool: True if authentication successful, False otherwise
        """
        if username not in self.users:
            self.login_failed.emit("Invalid username or password")
            return False

        user = self.users[username]
        password_hash = self._hash_password(password)

        if user["password_hash"] != password_hash:
            self.login_failed.emit("Invalid username or password")
            return False

        # Update last login
        import datetime
        user["last_login"] = datetime.datetime.now().isoformat()
        self._save_users()

        # Set current user
        self.current_user = username

        # Emit success signal
        self.login_success.emit(username)

        return True

    def logout(self):
        """
        Logout the current user
        """
        self.current_user = None

    def add_user(self, username, password, role="user"):
        """
        Add a new user

        Args:
            username (str): Username
            password (str): Password
            role (str): User role (admin, user)

        Returns:
            bool: True if user added successfully, False otherwise
        """
        if username in self.users:
            return False  # User already exists

        import datetime

        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "created": datetime.datetime.now().isoformat(),
            "last_login": None
        }

        return self._save_users()

    def remove_user(self, username):
        """
        Remove a user

        Args:
            username (str): Username

        Returns:
            bool: True if user removed successfully, False otherwise
        """
        if username not in self.users:
            return False  # User doesn't exist

        if username == "admin":
            return False  # Can't remove admin user

        del self.users[username]
        return self._save_users()

    def change_password(self, username, old_password, new_password):
        """
        Change a user's password

        Args:
            username (str): Username
            old_password (str): Current password
            new_password (str): New password

        Returns:
            bool: True if password changed successfully, False otherwise
        """
        if username not in self.users:
            return False

        user = self.users[username]
        old_password_hash = self._hash_password(old_password)

        if user["password_hash"] != old_password_hash:
            return False  # Wrong current password

        # Update password
        user["password_hash"] = self._hash_password(new_password)

        return self._save_users()

    def get_current_user(self):
        """
        Get the current logged-in user

        Returns:
            str or None: Username if logged in, None otherwise
        """
        return self.current_user

    def get_user_role(self, username=None):
        """
        Get a user's role

        Args:
            username (str, optional): Username, uses current user if None

        Returns:
            str or None: User role if user exists, None otherwise
        """
        if username is None:
            username = self.current_user

        if username and username in self.users:
            return self.users[username]["role"]

        return None

    def is_admin(self, username=None):
        """
        Check if a user is an admin

        Args:
            username (str, optional): Username, uses current user if None

        Returns:
            bool: True if user is admin, False otherwise
        """
        role = self.get_user_role(username)
        return role == "admin"

    def get_users_list(self):
        """
        Get a list of all users

        Returns:
            list: List of user dictionaries
        """
        users_list = []

        for username, user_data in self.users.items():
            users_list.append({
                "username": username,
                "role": user_data["role"],
                "created": user_data["created"],
                "last_login": user_data["last_login"]
            })

        return users_list