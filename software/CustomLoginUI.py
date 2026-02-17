import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox, QWidget
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt


class CustomLoginUI(QDialog):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("Fire Vision Pro - Account")
        self.setFixedSize(1366, 768)
        self.setStyleSheet("background-color: #0b0f2c;")

        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(100, 100, 100, 100)
        welcome_label = QLabel("Welcome\nback . . .")
        welcome_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        welcome_label.setStyleSheet("color: white;")
        welcome_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        left_layout.addWidget(welcome_label)
        left_layout.addStretch()
        main_layout.addWidget(left_panel, stretch=2)

        # --- Right Panel ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(100, 100, 100, 100)

        title_label = QLabel("Create your account")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: white;")

        subtitle_label = QLabel("It's just few minutes and free!")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setStyleSheet("color: #cccccc;")

        username_input = QLineEdit()
        username_input.setPlaceholderText("Username")
        email_input = QLineEdit()
        email_input.setPlaceholderText("Email (e.g., web@example.com)")
        password_input = QLineEdit()
        password_input.setPlaceholderText("Password")
        password_input.setEchoMode(QLineEdit.Password)

        for field in [username_input, email_input, password_input]:
            field.setStyleSheet("""
                QLineEdit {
                    background-color: #151a3c;
                    color: white;
                    padding: 12px;
                    border: 1px solid #2e375a;
                    border-radius: 10px;
                }
                QLineEdit:focus {
                    border: 1px solid #0066ff;
                    background-color: #1d234a;
                }
            """)

        checkbox = QCheckBox("I agree with terms and conditions.")
        checkbox.setStyleSheet("color: #cccccc; font-size: 12px;")

        submit_btn = QPushButton("Create my account")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3385ff;
            }
        """)

        # Add widgets to layout
        right_layout.addWidget(title_label)
        right_layout.addWidget(subtitle_label)
        right_layout.addSpacing(20)
        right_layout.addWidget(username_input)
        right_layout.addWidget(email_input)
        right_layout.addWidget(password_input)
        right_layout.addWidget(checkbox)
        right_layout.addSpacing(15)
        right_layout.addWidget(submit_btn)
        right_layout.addStretch()

        main_layout.addWidget(right_panel, stretch=3)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomLoginUI()
    window.show()
    sys.exit(app.exec_())
