try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class DeviceSettingsPage(QWidget):
    device_changed = pyqtSignal(str)

    def __init__(self, model=None, camera_manager=None, parent=None):
        super().__init__(parent)
        self.model = model
        self.camera_manager = camera_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(28)

        # Card container
        card = QFrame()
        card.setStyleSheet('''
            QFrame {
                background: #181a20;
                border-radius: 18px;
                border: 1.5px solid #23284a;
                box-shadow: 0 4px 24px rgba(0,0,0,0.18);
            }
        ''')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(22)

        # Title
        title = QLabel("🖥️ Device Settings")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #fff; letter-spacing: 1px;")
        card_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Configure which device is used for AI model inference. Switch between CPU and GPU for best performance.")
        subtitle.setStyleSheet("font-size: 15px; color: #bfc9e0; margin-bottom: 8px;")
        card_layout.addWidget(subtitle)

        # Device Info Section
        device_info_box = QFrame()
        device_info_box.setStyleSheet('''
            QFrame {
                background: #222436;
                border-radius: 10px;
                border: 1px solid #23284a;
            }
        ''')
        device_info_layout = QVBoxLayout(device_info_box)
        device_info_layout.setContentsMargins(18, 18, 18, 18)
        device_info_layout.setSpacing(8)
        device_info_title = QLabel("System & Device Info")
        device_info_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #8B5CF6;")
        device_info_layout.addWidget(device_info_title)
        self.device_info = QLabel()
        self.device_info.setStyleSheet("font-size: 14px; color: #bfc9e0;")
        self.device_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        device_info_layout.addWidget(self.device_info)
        card_layout.addWidget(device_info_box)

        # Device Selection Section
        device_select_box = QFrame()
        device_select_box.setStyleSheet('''
            QFrame {
                background: #232136;
                border-radius: 10px;
                border: 1px solid #23284a;
            }
        ''')
        device_select_layout = QVBoxLayout(device_select_box)
        device_select_layout.setContentsMargins(18, 18, 18, 18)
        device_select_layout.setSpacing(10)
        device_select_title = QLabel("Select Inference Device")
        device_select_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4F8CFF;")
        device_select_layout.addWidget(device_select_title)
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet('''
            QComboBox {
                font-size: 15px;
                background: #1a1a2e;
                color: #fff;
                border-radius: 8px;
                padding: 8px 16px;
                border: 1.5px solid #393552;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                background: #232136;
                color: #fff;
                selection-background-color: #4F8CFF;
            }
        ''')
        self.populate_devices()
        device_select_layout.addWidget(self.device_combo)
        
        # Apply Button
        apply_btn = QPushButton("Apply Device")
        apply_btn.setStyleSheet('''
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #4F8CFF);
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px 0;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #1976D2);
            }
        ''')
        apply_btn.clicked.connect(self.apply_device)
        device_select_layout.addWidget(apply_btn)
        card_layout.addWidget(device_select_box)
        layout.addWidget(card)
        layout.addStretch()
        self.update_device_info()

    def populate_devices(self):
        """Populate available devices"""
        self.device_combo.clear()
        self.device_combo.addItem("CPU")
        if HAS_TORCH and torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                self.device_combo.addItem(f"CUDA:{i} - {torch.cuda.get_device_name(i)}")
        elif not HAS_TORCH:
            self.device_combo.addItem("PyTorch not available - Lightweight mode")

    def apply_device(self):
        """Apply selected device"""
        new_device = self.device_combo.currentText()
        if "CUDA" in new_device:
            new_device = new_device.split(" - ")[0].lower()
        else:
            new_device = "cpu"
        
        if not HAS_TORCH:
            QMessageBox.information(self, "Lightweight Mode", "PyTorch not available. AI features are disabled in this build.")
            return
            
        try:
            if self.model is not None:
                self.model.to(new_device)
            if self.camera_manager is not None:
                if hasattr(self.camera_manager, 'people_detector') and hasattr(self.camera_manager.people_detector, 'model'):
                    self.camera_manager.people_detector.model.to(new_device)
                if hasattr(self.camera_manager, 'fire_smoke_detector') and hasattr(self.camera_manager.fire_smoke_detector, 'model'):
                    self.camera_manager.fire_smoke_detector.model.to(new_device)
            QMessageBox.information(self, "Device Changed", f"Model(s) moved to {new_device} successfully.")
            self.device_changed.emit(new_device)
        except Exception as e:
            QMessageBox.critical(self, "Device Change Error", f"Failed to move model(s) to {new_device}: {e}")
        self.update_device_info()

    def update_device_info(self):
        """Update device information display"""
        if not HAS_TORCH:
            info_text = "⚠️ <b>Lightweight Mode</b><br>PyTorch not available - AI features disabled"
        else:
            info_text = f"<b>PyTorch Version:</b> {torch.__version__}<br>"
            info_text += f"<b>CUDA Available:</b> {torch.cuda.is_available()}<br>"
            if torch.cuda.is_available():
                info_text += f"<b>CUDA Version:</b> {torch.version.cuda}<br>"
                info_text += f"<b>GPU Count:</b> {torch.cuda.device_count()}<br>"
                info_text += f"<b>Current Device:</b> {torch.cuda.current_device()}<br>"
                info_text += f"<b>GPU Name:</b> {torch.cuda.get_device_name(0)}"
        self.device_info.setText(info_text)