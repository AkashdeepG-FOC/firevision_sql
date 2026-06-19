import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# Import ConfigManager
try:
    from config_manager import ConfigManager
except ImportError:
    # Handle if path structure varies
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from config_manager import ConfigManager

# Resource path helper
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class LoadingWidget(QWidget):
    """Loading animation widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        self.spinner = QLabel("⏳")
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setStyleSheet("""
            QLabel {
                font-size: 48px;
                color: #8B5CF6;
                background: transparent;
            }
        """)
        
        self.loading_text = QLabel("Authenticating...")
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: white;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        layout.addWidget(self.spinner)
        layout.addWidget(self.loading_text)
        self.start_animation()
        
    def start_animation(self):
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_spinner)
        self.animation_timer.start(100)
        self.animation_frame = 0
        
    def animate_spinner(self):
        spinners = ["⏳", "⏰", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
        self.spinner.setText(spinners[self.animation_frame % len(spinners)])
        self.animation_frame += 1
        
    def stop_animation(self):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
            
    def set_loading_text(self, text):
        self.loading_text.setText(text)


class ModernLoginDialog(QDialog):
    """Modern login dialog matching the provided design exactly"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fire Vision Pro - Login")
        self.setFixedSize(1366, 768)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        self.config_manager = ConfigManager()
        self.is_signup_mode = False
        
        self.setup_ui()
        self.load_saved_login()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QWidget()
        left_panel.setFixedWidth(600)
        left_panel.setStyleSheet("border-radius: 32px; background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(resource_path("assests/surveillance-data-security-technology.jpg"))
        if not pixmap.isNull():
            scaled = pixmap.scaled(600, 768, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            image_label.setPixmap(scaled)
        else:
            image_label.setText("[Image not found]")
            image_label.setStyleSheet("color: white; font-size: 18px;")
        image_label.setStyleSheet("border-radius: 32px; margin: 0px;")
        left_layout.addWidget(image_label, 1)

        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: #1F2937;
                border-radius: 0px;
            }
        """)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addStretch(1)

        form_centerer = QWidget()
        form_centerer.setFixedWidth(360)
        form_centerer_layout = QVBoxLayout(form_centerer)
        form_centerer_layout.setContentsMargins(0, 0, 0, 0)
        form_centerer_layout.setSpacing(22)

        self.title_label = QLabel("Create an account")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 10px;
            }
        """)

        form_centerer_layout.addWidget(self.title_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMaximumWidth(360)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMaximumWidth(360)
        self.password_input.returnPressed.connect(self.handle_action)
        
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(30, 30)
        self.show_password_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9CA3AF;
                font-size: 14px;
                margin-right: 8px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)
        
        self.password_input.setLayout(QHBoxLayout())
        self.password_input.layout().addStretch()
        self.password_input.layout().addWidget(self.show_password_btn)
        self.password_input.layout().setContentsMargins(0, 0, 8, 0)
        self.password_input.layout().setSpacing(0)
        
        password_layout.addWidget(self.password_input)

        input_style = """
            QLineEdit {
                background-color: #26243a;
                border: 1.5px solid #393552;
                border-radius: 10px;
                padding: 10px 16px;
                color: white;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-width: 140px;
                max-width: 360px;
            }
            QLineEdit:focus {
                border: 2px solid #8B5CF6;
                background-color: #2a273f;
            }
            QLineEdit::placeholder {
                color: #bfc9e0;
            }
        """
        for field in [self.username_input, self.password_input]:
            field.setStyleSheet(input_style)
            field.setFixedHeight(40)
            field.setMaximumWidth(360)

        self.remember_widget = QWidget()
        remember_layout = QHBoxLayout(self.remember_widget)
        remember_layout.setContentsMargins(0, 0, 0, 0)
        remember_layout.setSpacing(10)
        
        self.remember_checkbox = QCheckBox()
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4B5563;
                border-radius: 4px;
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                background-color: #8B5CF6;
                border-color: #8B5CF6;
            }
        """)
        
        remember_text = QLabel("Remember me")
        remember_text.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addWidget(remember_text)
        remember_layout.addStretch()
        self.remember_widget.hide()
        
        self.action_btn = QPushButton("Create account")
        self.action_btn.setFixedHeight(44)
        self.action_btn.setMaximumWidth(360)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
        """)
        self.action_btn.clicked.connect(self.handle_action)
        
        form_centerer_layout.addWidget(self.username_input)
        form_centerer_layout.addWidget(password_container)
        form_centerer_layout.addWidget(self.remember_widget)
        form_centerer_layout.addWidget(self.action_btn)

        right_layout.addWidget(form_centerer, alignment=Qt.AlignHCenter)
        right_layout.addStretch(2)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        self.loading_widget = LoadingWidget()
        self.loading_widget.hide()
        main_layout.addWidget(self.loading_widget)

        self.toggle_mode()

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁")

    def toggle_mode(self):
        self.is_signup_mode = False
        self.title_label.setText("Login to your account")
        self.action_btn.setText("Login")
        self.username_input.show()
        self.remember_widget.show()
        self.password_input.clear()
        self.load_saved_login()

    def load_saved_login(self):
        if not self.is_signup_mode:
            saved_username = self.config_manager.get_saved_login()
            if saved_username:
                self.username_input.setText(saved_username)
                self.remember_checkbox.setChecked(True)
                self.password_input.setFocus()
            else:
                if not self.config_manager.load_users():
                    self.username_input.setText("admin")
                    self.password_input.setText("admin")

    def handle_action(self):
        self.login()

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        self.process_authentication(username, password)
        
    def show_loading_animation(self):
        self.username_input.hide()
        self.password_input.hide()
        self.remember_widget.hide()
        self.action_btn.hide()
        
        self.loading_widget.show()
        self.loading_widget.set_loading_text("Logging in...")
        
    def process_authentication(self, username, password):
        try:
            success = self.config_manager.authenticate_user(username, password)
            if success:
                self.complete_login(username)
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")
            
    def complete_login(self, username):
        try:
            remember = self.remember_checkbox.isChecked()
            self.config_manager.save_login_details(username, remember)
            
            self.username = username
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")
            
    def hide_loading_animation(self):
        self.loading_widget.hide()
        self.loading_widget.stop_animation()
        
        self.username_input.show()
        self.password_input.show()
        self.remember_widget.show()
        self.action_btn.show()

    def signup(self):
        pass

    def get_username(self):
        return getattr(self, 'username', self.username_input.text().strip())
