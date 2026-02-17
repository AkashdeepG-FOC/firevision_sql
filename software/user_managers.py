import json
import os
import hashlib
import time
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QLineEdit, QHeaderView, QDialog,
                             QFormLayout, QCheckBox, QMessageBox, QTabWidget,
                             QTextEdit, QDateTimeEdit, QSpinBox, QScrollArea)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDateTime

@dataclass
class User:
    """User data structure"""
    id: str
    username: str
    email: str
    password_hash: str
    role: str  # 'admin', 'operator', 'viewer'
    permissions: List[str]
    created_at: float
    last_login: Optional[float] = None
    is_active: bool = True
    camera_access: List[str] = None  # List of camera IDs user can access
    session_timeout: int = 3600  # Session timeout in seconds

@dataclass
class UserSession:
    """User session data structure"""
    session_id: str
    user_id: str
    username: str
    role: str
    login_time: float
    last_activity: float
    ip_address: str
    user_agent: str

@dataclass
class ActivityLog:
    """Activity log data structure"""
    id: str
    user_id: str
    username: str
    action: str
    resource: str
    timestamp: float
    ip_address: str
    details: Optional[Dict] = None

from backend_client import backend_client

class UserManager(QObject):
    """Manager for user accounts, permissions, and activity logging via Backend API"""
    
    user_created = pyqtSignal(User)
    user_updated = pyqtSignal(User)
    user_deleted = pyqtSignal(str)  # user_id
    user_logged_in = pyqtSignal(UserSession)
    user_logged_out = pyqtSignal(str)  # session_id
    activity_logged = pyqtSignal(ActivityLog)
    
    def __init__(self):
        super().__init__()
        
        # Permission definitions
        self.permissions = {
            'admin': [
                'view_cameras', 'manage_cameras', 'view_recordings', 'manage_recordings',
                'view_alerts', 'manage_alerts', 'view_users', 'manage_users',
                'view_settings', 'manage_settings', 'view_analytics', 'manage_system'
            ],
            'operator': [
                'view_cameras', 'manage_cameras', 'view_recordings', 'manage_recordings',
                'view_alerts', 'manage_alerts', 'view_analytics'
            ],
            'viewer': [
                'view_cameras', 'view_recordings', 'view_alerts', 'view_analytics'
            ]
        }
    
    def init_databases(self):
        """Initialize databases - No-op for API version"""
        pass
    
    def create_default_admin(self):
        """No-op, backend handles this via seed"""
        pass
    
    def hash_password(self, password: str) -> str:
        """Hash password - No-op, backend handles hashing"""
        return password
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password - Handled by backend login"""
        return False
    
    def create_user(self, username: str, email: str, password: str, 
                   role: str, camera_access: List[str] = None) -> Optional[User]:
        """Create a new user"""
        try:
            # We treat username as 'name' for backend
            success = backend_client.create_user(email=email, password=password, name=username, role=role)
            
            if success:
                # Need to fetch the created user to get ID and details
                # For now, we return a mock object or try to find it
                # Logic: Fetch all users and find the one with this email
                users = self.get_all_users()
                for user in users:
                    if user.email == email:
                        self.user_created.emit(user)
                        
                        # Log activity
                        backend_client.create_log(
                            action_type="create_user",
                            description=f"Created user {username} ({email})",
                            performed_by=backend_client.user_data.get('email', 'system') if backend_client.user_data else 'system'
                        )
                        return user
            return None
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def save_user(self, user: User):
        """Save user to database - Handled by update_user"""
        pass
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self.get_all_users()
        for user in users:
            if str(user.id) == str(user_id):
                return user
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (name in backend)"""
        users = self.get_all_users()
        for user in users:
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self.get_all_users()
        for user in users:
            if user.email == email:
                return user
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        try:
            api_users = backend_client.get_users()
            users = []
            for u in api_users:
                # Map backend fields to User dataclass
                # Timestamp handling: backend strings to float
                created_at_str = u.get("created_at")
                created_at = datetime.fromisoformat(created_at_str).timestamp() if created_at_str else time.time()
                
                users.append(User(
                    id=str(u.get("id")),
                    username=u.get("name") or u.get("email").split('@')[0],
                    email=u.get("email"),
                    password_hash="", # Hidden
                    role=u.get("role", "viewer"),
                    permissions=self.permissions.get(u.get("role", "viewer"), []),
                    created_at=created_at,
                    last_login=None, # Not yet exposed in simple User response or separate
                    is_active=True,
                    camera_access=[], # Not yet implemented in backend
                    session_timeout=3600
                ))
            return users
            
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = "127.0.0.1", 
                         user_agent: str = "FireVision") -> Optional[UserSession]:
        """Authenticate user and create session"""
        try:
            # Login via backend (username here acts as email if that's what backend expects)
            # Check backend: FormBody(username), usually mapped to email in many setups, 
            # but my backend auth.py uses `email == form_data.username`.
            # So `username` argument to this func MUST be `email` or we need `email` arg.
            # But legacy calls might pass username.
            
            # Since my `get_all_users` maps username to name, and login likely uses email,
            # we might have a mismatch if passing "admin" instead of "admin@example.com".
            # My seed created "admin" as email too, so it works for admin.
            
            if backend_client.login(username, password):
                # Fetch user data
                user_data = backend_client.user_data
                if not user_data:
                    return None
                
                # Create session (client-side tracking only for now)
                session_id = f"session_{int(time.time())}"
                
                session = UserSession(
                    session_id=session_id,
                    user_id=str(user_data.get("id")),
                    username=user_data.get("name"),
                    role=user_data.get("role"),
                    login_time=time.time(),
                    last_activity=time.time(),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                self.user_logged_in.emit(session)
                
                # Log activity
                backend_client.create_log(
                    action_type="login",
                    description=f"User {username} logged in",
                    performed_by=username
                )
                
                return session
            return None
            
        except Exception as e:
            print(f"❌ Error authenticating user: {e}")
            return None
    
    def save_session(self, session: UserSession):
        pass
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        return None
    
    def update_session_activity(self, session_id: str):
        pass
    
    def logout_user(self, session_id: str):
        self.user_logged_out.emit(session_id)
    
    def cleanup_expired_sessions(self):
        pass
    
    def log_activity(self, user_id: str, username: str, action: str, 
                    resource: str, ip_address: str = "127.0.0.1", 
                    details: Dict = None):
        """Log user activity"""
        description = f"{action} on {resource}"
        if details:
            description += f" Details: {json.dumps(details)}"
        backend_client.create_log(action_type=action, description=description, performed_by=username)
    
    def get_activity_logs(self, user_id: str = None, action: str = None,
                         start_date: datetime = None, end_date: datetime = None,
                         limit: int = 100) -> List[ActivityLog]:
        """Get activity logs via API"""
        try:
            api_logs = backend_client.get_logs(limit=limit)
            logs = []
            for l in api_logs:
                # Filter locally if API doesn't support complex filtering yet
                # Map fields
                # Backend: id, action_type, description, performed_by, created_at
                
                # Timestamp parsing
                created_at_str = l.get("created_at")
                timestamp = datetime.fromisoformat(created_at_str).timestamp() if created_at_str else time.time()

                logs.append(ActivityLog(
                    id=str(l.get("id")),
                    user_id="0", # Unknown from simple log
                    username=l.get("performed_by"),
                    action=l.get("action_type"),
                    resource="", # Parsed from description maybe
                    timestamp=timestamp,
                    ip_address="",
                    details={"description": l.get("description")}
                ))
            return logs
            
        except Exception as e:
            print(f"❌ Error getting activity logs: {e}")
            return []
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information"""
        try:
            # Prepare update data
            data = {}
            if 'username' in kwargs: data['name'] = kwargs['username']
            if 'email' in kwargs: data['email'] = kwargs['email']
            if 'role' in kwargs: data['role'] = kwargs['role']
            # Password not supported in simple update yet, or needs specific endpoint
            
            success = backend_client.update_user(int(user_id), data)
            if success:
                 # Log activity
                backend_client.create_log(
                    action_type="update_user",
                    description=f"Updated user {user_id}",
                    performed_by="system"
                )
                # Emit signal
                user = self.get_user(user_id)
                if user:
                    self.user_updated.emit(user)
                return True
            return False
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            success = backend_client.delete_user(int(user_id))
            if success:
                self.user_deleted.emit(user_id)
                backend_client.create_log(
                    action_type="delete_user",
                    description=f"Deleted user {user_id}",
                    performed_by="system"
                )
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user = self.get_user(user_id)
        if not user: return False
        return permission in user.permissions
    
    def check_camera_access(self, user_id: str, camera_id: str) -> bool:
        """Check if user has access to specific camera"""
        user = self.get_user(user_id)
        if not user: return False
        if user.role == 'admin': return True
        return True # Default to true for now since backend access list not impl

class UserManagementWidget(QWidget):
    """Widget for managing users and permissions"""
    
    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager
        self.current_users = []
        
        self.setup_ui()
        self.connect_signals()
        self.load_users()
    
    def setup_ui(self):
        """Setup the user management interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_widget = self.create_header()
        layout.addWidget(header_widget)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        
        # Users tab
        self.users_tab = self.create_users_tab()
        self.tab_widget.addTab(self.users_tab, "\U0001F465 Users")
        
        # Activity logs tab
        self.activity_tab = self.create_activity_tab()
        self.tab_widget.addTab(self.activity_tab, "\U0001F4CB Activity Logs")
        
        # Sessions tab
        self.sessions_tab = self.create_sessions_tab()
        self.tab_widget.addTab(self.sessions_tab, "\U0001F510 Active Sessions")
        
        # Wrap tab widget in a scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.tab_widget)
        layout.addWidget(scroll)
    
    def create_header(self) -> QWidget:
        """Create header with controls"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title
        title = QLabel("👥 User Access Management")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        
        add_user_btn = QPushButton("➕ Add User")
        add_user_btn.clicked.connect(self.show_add_user_dialog)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_users)
        
        cleanup_btn = QPushButton("🧹 Cleanup Sessions")
        cleanup_btn.clicked.connect(self.cleanup_sessions)
        
        actions_layout.addWidget(add_user_btn)
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(cleanup_btn)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(actions_widget)
        
        return header
    
    def create_users_tab(self) -> QWidget:
        """Create users management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "Username", "Email", "Role", "Status", "Last Login", 
            "Camera Access", "Actions", "Permissions"
        ])
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.users_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                gridline-color: #505050;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QTableWidget::item:selected {
                background-color: #ff3333;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                border: 1px solid #505050;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.users_table)
        
        return widget
    
    def create_activity_tab(self) -> QWidget:
        """Create activity logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        
        user_label = QLabel("User:")
        user_label.setStyleSheet("color: white;")
        
        self.activity_user_filter = QComboBox()
        self.activity_user_filter.addItem("All Users")
        self.activity_user_filter.currentTextChanged.connect(self.load_activity_logs)
        
        action_label = QLabel("Action:")
        action_label.setStyleSheet("color: white;")
        
        self.activity_action_filter = QComboBox()
        self.activity_action_filter.addItems([
            "All Actions", "login", "logout", "create_user", "update_user", 
            "delete_user", "view_camera", "manage_camera", "view_recording"
        ])
        self.activity_action_filter.currentTextChanged.connect(self.load_activity_logs)
        
        filters_layout.addWidget(user_label)
        filters_layout.addWidget(self.activity_user_filter)
        filters_layout.addWidget(action_label)
        filters_layout.addWidget(self.activity_action_filter)
        filters_layout.addStretch()
        
        layout.addWidget(filters_widget)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Resource", "IP Address", "Details"
        ])
        
        # Set column widths
        header = self.activity_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.activity_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                gridline-color: #505050;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QTableWidget::item:selected {
                background-color: #ff3333;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                border: 1px solid #505050;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.activity_table)
        
        return widget
    
    def create_sessions_tab(self) -> QWidget:
        """Create active sessions tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sessions table
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(6)
        self.sessions_table.setHorizontalHeaderLabels([
            "User", "Role", "Login Time", "Last Activity", "IP Address", "Actions"
        ])
        
        # Set column widths
        header = self.sessions_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.sessions_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                gridline-color: #505050;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QTableWidget::item:selected {
                background-color: #ff3333;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                border: 1px solid #505050;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.sessions_table)
        
        return widget
    
    def connect_signals(self):
        """Connect signals"""
        self.user_manager.user_created.connect(self.on_user_created)
        self.user_manager.user_updated.connect(self.on_user_updated)
        self.user_manager.user_deleted.connect(self.on_user_deleted)
        self.user_manager.activity_logged.connect(self.on_activity_logged)
    
    def load_users(self):
        """Load users from database"""
        try:
            self.current_users = self.user_manager.get_all_users()
            self.update_users_table()
            
            # Update activity user filter
            self.activity_user_filter.clear()
            self.activity_user_filter.addItem("All Users")
            for user in self.current_users:
                self.activity_user_filter.addItem(user.username)
            
        except Exception as e:
            print(f"❌ Error loading users: {e}")
    
    def update_users_table(self):
        """Update the users table"""
        self.users_table.setRowCount(len(self.current_users))
        
        for row, user in enumerate(self.current_users):
            # Username
            self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
            
            # Email
            self.users_table.setItem(row, 1, QTableWidgetItem(user.email))
            
            # Role
            role_item = QTableWidgetItem(user.role.title())
            if user.role == 'admin':
                role_item.setBackground(Qt.red)
            elif user.role == 'operator':
                role_item.setBackground(Qt.yellow)
            self.users_table.setItem(row, 2, role_item)
            
            # Status
            status_item = QTableWidgetItem("Active" if user.is_active else "Inactive")
            status_item.setBackground(Qt.green if user.is_active else Qt.gray)
            self.users_table.setItem(row, 3, status_item)
            
            # Last Login
            last_login = "Never"
            if user.last_login:
                last_login = datetime.fromtimestamp(user.last_login).strftime("%Y-%m-%d %H:%M:%S")
            self.users_table.setItem(row, 4, QTableWidgetItem(last_login))
            
            # Camera Access
            camera_access = "All" if user.role == 'admin' else f"{len(user.camera_access or [])} cameras"
            self.users_table.setItem(row, 5, QTableWidgetItem(camera_access))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 25)
            edit_btn.setToolTip("Edit User")
            edit_btn.clicked.connect(lambda checked, uid=user.id: self.edit_user(uid))
            actions_layout.addWidget(edit_btn)
            
            if user.username != "admin":  # Don't allow deleting admin user
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(30, 25)
                delete_btn.setToolTip("Delete User")
                delete_btn.clicked.connect(lambda checked, uid=user.id: self.delete_user(uid))
                actions_layout.addWidget(delete_btn)
            
            toggle_btn = QPushButton("🔒" if user.is_active else "🔓")
            toggle_btn.setFixedSize(30, 25)
            toggle_btn.setToolTip("Toggle Active Status")
            toggle_btn.clicked.connect(lambda checked, uid=user.id: self.toggle_user_status(uid))
            actions_layout.addWidget(toggle_btn)
            
            self.users_table.setCellWidget(row, 6, actions_widget)
            
            # Permissions
            permissions_text = ", ".join(user.permissions[:3])
            if len(user.permissions) > 3:
                permissions_text += f" (+{len(user.permissions) - 3} more)"
            self.users_table.setItem(row, 7, QTableWidgetItem(permissions_text))
    
    def load_activity_logs(self):
        """Load activity logs"""
        try:
            user_filter = self.activity_user_filter.currentText()
            action_filter = self.activity_action_filter.currentText()
            
            user_id = None
            if user_filter != "All Users":
                for user in self.current_users:
                    if user.username == user_filter:
                        user_id = user.id
                        break
            
            action = None if action_filter == "All Actions" else action_filter
            
            # Get logs for last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            logs = self.user_manager.get_activity_logs(
                user_id=user_id,
                action=action,
                start_date=start_date,
                end_date=end_date,
                limit=500
            )
            
            self.update_activity_table(logs)
            
        except Exception as e:
            print(f"❌ Error loading activity logs: {e}")
    
    def update_activity_table(self, logs: List[ActivityLog]):
        """Update activity logs table"""
        self.activity_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # Timestamp
            timestamp = datetime.fromtimestamp(log.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            self.activity_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # User
            self.activity_table.setItem(row, 1, QTableWidgetItem(log.username))
            
            # Action
            action_item = QTableWidgetItem(log.action)
            if log.action in ['login', 'logout']:
                action_item.setBackground(Qt.blue)
            elif log.action in ['create_user', 'update_user', 'delete_user']:
                action_item.setBackground(Qt.yellow)
            self.activity_table.setItem(row, 2, action_item)
            
            # Resource
            self.activity_table.setItem(row, 3, QTableWidgetItem(log.resource))
            
            # IP Address
            self.activity_table.setItem(row, 4, QTableWidgetItem(log.ip_address))
            
            # Details
            details_text = ""
            if log.details:
                details_text = ", ".join([f"{k}: {v}" for k, v in log.details.items()])
            self.activity_table.setItem(row, 5, QTableWidgetItem(details_text))
    
    def show_add_user_dialog(self):
        """Show add user dialog"""
        dialog = AddUserDialog(self.user_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
    
    def edit_user(self, user_id: str):
        """Edit user"""
        user = self.user_manager.get_user(user_id)
        if user:
            dialog = EditUserDialog(self.user_manager, user, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_users()
    
    def delete_user(self, user_id: str):
        """Delete user"""
        user = self.user_manager.get_user(user_id)
        if not user:
            return
        
        reply = QMessageBox.question(
            self, 'Delete User',
            f'Are you sure you want to delete user "{user.username}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.user_manager.delete_user(user_id)
            if success:
                self.load_users()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete user")
    
    def toggle_user_status(self, user_id: str):
        """Toggle user active status"""
        user = self.user_manager.get_user(user_id)
        if user:
            success = self.user_manager.update_user(user_id, is_active=not user.is_active)
            if success:
                self.load_users()
            else:
                QMessageBox.warning(self, "Error", "Failed to update user status")
    
    def cleanup_sessions(self):
        """Cleanup expired sessions"""
        self.user_manager.cleanup_expired_sessions()
        QMessageBox.information(self, "Success", "Expired sessions cleaned up")
    
    def on_user_created(self, user: User):
        """Handle user created"""
        self.load_users()
    
    def on_user_updated(self, user: User):
        """Handle user updated"""
        self.load_users()
    
    def on_user_deleted(self, user_id: str):
        """Handle user deleted"""
        self.load_users()
    
    def on_activity_logged(self, activity: ActivityLog):
        """Handle new activity logged"""
        if self.tab_widget.currentWidget() == self.activity_tab:
            self.load_activity_logs()

class AddUserDialog(QDialog):
    """Dialog for adding new users"""
    
    def __init__(self, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setWindowTitle("Add New User")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addRow("Username:", self.username_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        form_layout.addRow("Email:", self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow("Password:", self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm password")
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["viewer", "operator", "admin"])
        form_layout.addRow("Role:", self.role_combo)
        
        # Camera Access
        self.camera_access_widget = QWidget()
        camera_layout = QVBoxLayout(self.camera_access_widget)
        
        self.all_cameras_checkbox = QCheckBox("Access to all cameras")
        self.all_cameras_checkbox.setChecked(True)
        self.all_cameras_checkbox.toggled.connect(self.toggle_camera_selection)
        camera_layout.addWidget(self.all_cameras_checkbox)
        
        # TODO: Add specific camera selection
        self.camera_checkboxes = []
        
        form_layout.addRow("Camera Access:", self.camera_access_widget)
        
        layout.addWidget(form_widget)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create User")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        create_btn.clicked.connect(self.create_user)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(create_btn)
        
        layout.addWidget(buttons_widget)
    
    def toggle_camera_selection(self, checked):
        """Toggle camera selection widgets"""
        # TODO: Implement specific camera selection
        pass
    
    def create_user(self):
        """Create new user"""
        try:
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            role = self.role_combo.currentText()
            
            # Validation
            if not username or not email or not password:
                QMessageBox.warning(self, "Error", "Please fill in all required fields")
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
            
            if len(password) < 6:
                QMessageBox.warning(self, "Error", "Password must be at least 6 characters long")
                return
            
            # Camera access
            camera_access = None
            if not self.all_cameras_checkbox.isChecked():
                # TODO: Get selected cameras
                camera_access = []
            
            # Create user
            user = self.user_manager.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                camera_access=camera_access
            )
            
            if user:
                QMessageBox.information(self, "Success", f"User '{username}' created successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to create user")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating user: {str(e)}")

class EditUserDialog(QDialog):
    """Dialog for editing existing users"""
    
    def __init__(self, user_manager: UserManager, user: User, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user = user
        self.setWindowTitle(f"Edit User: {user.username}")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_user_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Username (read-only)
        self.username_label = QLabel(self.user.username, self)
        form_layout.addRow("Username:", self.username_label)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setText(self.user.email)
        form_layout.addRow("Email:", self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        form_layout.addRow("Password:", self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm password")
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["viewer", "operator", "admin"])
        self.role_combo.setCurrentText(self.user.role)
        form_layout.addRow("Role:", self.role_combo)
        
        # Camera Access
        self.camera_access_widget = QWidget()
        camera_layout = QVBoxLayout(self.camera_access_widget)
        
        self.all_cameras_checkbox = QCheckBox("Access to all cameras")
        self.all_cameras_checkbox.setChecked(True)
        self.all_cameras_checkbox.toggled.connect(self.toggle_camera_selection)
        camera_layout.addWidget(self.all_cameras_checkbox)
        
        # TODO: Add specific camera selection
        self.camera_checkboxes = []
        
        form_layout.addRow("Camera Access:", self.camera_access_widget)
        
        layout.addWidget(form_widget)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        update_btn = QPushButton("Update User")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        update_btn.clicked.connect(self.update_user)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(update_btn)
        
        layout.addWidget(buttons_widget)
    
    def toggle_camera_selection(self, checked):
        """Toggle camera selection widgets"""
        # TODO: Implement specific camera selection
        pass
    
    def load_user_data(self):
        """Load user data into dialog"""
        # TODO: Implement loading user data into dialog
        pass
    
    def update_user(self):
        """Update user information"""
        try:
            username = self.username_label.text()
            email = self.email_input.text().strip()
            password = self.password_input.text()
            role = self.role_combo.currentText()
            
            # Validation
            if not username or not email or not password:
                QMessageBox.warning(self, "Error", "Please fill in all required fields")
                return
            
            if password != self.confirm_password_input.text():
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
            
            if len(password) < 6:
                QMessageBox.warning(self, "Error", "Password must be at least 6 characters long")
                return
            
            # Camera access
            camera_access = None
            if not self.all_cameras_checkbox.isChecked():
                # TODO: Get selected cameras
                camera_access = []
            
            # Update user
            success = self.user_manager.update_user(
                self.user.id,
                username=username,
                email=email,
                password=password,
                role=role,
                camera_access=camera_access
            )
            
            if success:
                QMessageBox.information(self, "Success", "User updated successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to update user")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating user: {str(e)}")
