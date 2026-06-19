import time
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, pyqtSlot, QObject
from PyQt5.QtGui import QCursor

class DeleteCamerasDialog(QDialog):
    def __init__(self, camera_widgets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Cameras")
        self.setMinimumWidth(400)
        self.selected_ids = []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select cameras to delete:"))
        self.checkboxes = {}
        for cam_id, widget in camera_widgets.items():
            cb = QCheckBox(widget.camera_name)
            self.checkboxes[cam_id] = cb
            layout.addWidget(cb)
        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold;")
        delete_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def get_selected_ids(self):
        return [cid for cid, cb in self.checkboxes.items() if cb.isChecked()]


class ProfessionalEventCard(QWidget):
    """Professional event card matching the reference design exactly"""
    clicked = pyqtSignal(str)

    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.camera_id = event.get("camera_id", "")
        self.event_data = event
        self.setFixedSize(300, 140)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.setStyleSheet("""
            QWidget {
                background-color: #020203;
                border: 2px solid #f44336;
                border-radius: 10px;
                margin: 2px;
            }
            QWidget:hover {
                background-color: #1a1d2e;
                border: 2px solid #4f8cff;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.addStretch()
        
        date_label = QLabel(f"📅 {self.event_data.get('date', '12/07/2025')}")
        date_label.setStyleSheet("""
            QLabel {
                color: #bfc9e0;
                font-size: 11px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        top_row.addWidget(date_label)
        main_layout.addLayout(top_row)

        alert_type = self.event_data.get("type", "Fire Alert")
        type_label = QLabel(alert_type)
        type_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                border: none;
                padding: 2px 0px;
            }
        """)
        main_layout.addWidget(type_label)

        camera_info = f"Camera {self.event_data.get('camera_no', '1')}"
        camera_label = QLabel(camera_info)
        camera_label.setStyleSheet("""
            QLabel {
                color: #9aa4c8;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        main_layout.addWidget(camera_label)

        time_info = f"Time: {self.event_data.get('time', '12:40')}"
        time_label = QLabel(time_info)
        time_label.setStyleSheet("""
            QLabel {
                color: #9aa4c8;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        main_layout.addWidget(time_label)

        location_info = self.event_data.get("location", "Location: Department")
        if not location_info.startswith("Location:"):
            location_info = f"Location: {location_info}"
        
        location_label = QLabel(location_info)
        location_label.setStyleSheet("""
            QLabel {
                color: #9aa4c8;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        main_layout.addWidget(location_label)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        
        icons_container = QWidget()
        icons_layout = QHBoxLayout(icons_container)
        icons_layout.setContentsMargins(0, 0, 0, 0)
        icons_layout.setSpacing(8)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        warning_icon.setToolTip("Alert Status")
        
        check_icon = QLabel("✅")
        check_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        check_icon.setToolTip("Approved")
        
        action_icon = QLabel("🔁")
        action_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        action_icon.setToolTip("Actions Available")
        
        icons_layout.addWidget(warning_icon)
        icons_layout.addWidget(check_icon)
        icons_layout.addWidget(action_icon)
        
        bottom_row.addWidget(icons_container)
        main_layout.addLayout(bottom_row)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.camera_id:
            self.clicked.emit(self.camera_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d2e;
                border: 2px solid #4f8cff;
                border-radius: 10px;
                margin: 2px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                background-color: #020203;
                border: 2px solid #f44336;
                border-radius: 10px;
                margin: 2px;
            }
        """)
        super().leaveEvent(event)


class SkeletonCameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 180)
        layout = QVBoxLayout(self)
        self.label = QLabel("Loading camera...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            background: #232136;
            color: #bfc9e0;
            border-radius: 12px;
            font-size: 18px;
        """)
        layout.addWidget(self.label)
        self.setStyleSheet("""
            background: #232136;
            border-radius: 12px;
        """)

    def setText(self, text):
        self.label.setText(text)

    def update_frame(self, frame):
        pass


class MapBridge(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @pyqtSlot(str)
    def pinClicked(self, camera_id):
        reply = QMessageBox.question(
            self.main_window, "Go to Fullscreen?",
            f"Go to fullscreen for camera {camera_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.main_window.show_fullscreen_camera(camera_id)


class CameraLoaderThread(QThread):
    """Asynchronous camera loading thread for smooth UI transitions"""
    camera_loaded = pyqtSignal(str, dict)  # ID, Config
    finished_loading = pyqtSignal()
    progress_update = pyqtSignal(str, int)  # status message, progress percent
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
    def run(self):
        try:
            self.progress_update.emit("Connecting to backend database...", 10)
            self.msleep(150)
            
            self.progress_update.emit("Fetching camera list from API...", 30)
            cameras = self.config_manager.load_cameras()
            self.msleep(150)
            
            if not cameras:
                self.progress_update.emit("No cameras configured. Ready.", 100)
                self.finished_loading.emit()
                return
                
            total = len(cameras)
            for idx, (camera_id, camera_data) in enumerate(cameras.items()):
                progress = int(30 + (idx / total) * 60)
                self.progress_update.emit(f"Loading stream: {camera_data.get('name', 'Camera')}", progress)
                self.camera_loaded.emit(camera_id, camera_data)
                self.msleep(100)
                
            self.progress_update.emit("All cameras initialized. Starting streams...", 100)
            self.finished_loading.emit()
            
        except Exception as e:
            print(f"❌ CameraLoaderThread error: {e}")
            self.finished_loading.emit()
