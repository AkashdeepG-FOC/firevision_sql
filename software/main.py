import sys
import cv2
import os
import time
import datetime
import threading
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QPushButton, QGridLayout,
                           QStackedWidget, QLineEdit, QComboBox, QFileDialog,
                           QMessageBox, QFrame, QSplitter, QCheckBox, QSlider,
                           QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
                           QDialog, QFormLayout, QSpinBox, QGroupBox, QTextEdit,
                           QSystemTrayIcon, QMenu, QAction, QSizePolicy, QDoubleSpinBox,
                           QTimeEdit, QListWidgetItem, QTabWidget, QListWidget, QSlider)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont, QPalette, QColor, QCursor, QPainter, QBrush, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QDateTime, QObject, pyqtSlot, QTime
import folium
import webbrowser
import tempfile
import json
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtWebChannel import QWebChannel

# Import System Profiler
try:
    from utils.system_profiler import profiler
except ImportError:
    print("Warning: System Profiler not available")
    profiler = None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

try:
    from ultralytics import YOLO
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("Warning: Torch/YOLO not available. AI features disabled.")
    class YOLO:
        def __init__(self, *args, **kwargs):
            self.device = 'cpu'
        def __call__(self, *args, **kwargs):
            return []
        def to(self, device):
            self.device = device
            return self

# Removed DeviceSettingsPage import

# Import the Advanced Camera Management from separate file
try:
    from AdvancedCamera import AdvancedCameraManagementPage
except ImportError:
    print("Warning: AdvancedCamera not available")
    class AdvancedCameraManagementPage(QWidget):
        def __init__(self, *args, **kwargs): super().__init__()


# Import voice command system
try:
    from voice_command_manager import VoiceCommandManager, VoiceCommandWidget
except ImportError:
    print("Warning: Voice command system not available")
    class VoiceCommandManager:
        def __init__(self, main_window=None): pass
        def start_listening(self): pass
        def stop_listening(self): pass
        def is_voice_enabled(self): return False
    class VoiceCommandWidget(QWidget):
        def __init__(self, voice_manager, parent=None): super().__init__(parent)

# Import the splash screen
try:
    from splash_screen import SplashScreen
except ImportError:
    class SplashScreen:
        def show_with_progress(self): pass
        def close(self): pass

# Import the loading screen
try:
    from loading_screen import LoadingScreen
except ImportError:
    print("Warning: Loading screen not available")
    class LoadingScreen:
        def __init__(self): pass
        def show_with_fade(self): pass
        def update_status(self, message, progress=None): pass
        def complete_loading(self): pass
        def hide_with_fade(self): pass

# Import other modules with individual fallbacks
try:
    from config_manager import ConfigManager
except ImportError as e:
    print(f"Warning: Could not import ConfigManager: {e}")
    class ConfigManager:
        def __init__(self): pass
        def authenticate_user(self, username, password): return True
        def save_login_details(self, username, remember): pass
        def get_saved_login(self): return None
        def load_users(self): return {}
        def create_user(self, username, password, email): return True
        def load_cameras(self): return {}
        def get_camera(self, camera_id): return None
        def get_config(self, key, default=None): return default
        def update_config(self, key, value): pass
        def remove_camera(self, camera_id): pass
        def set_current_user(self, username): pass

# BackgroundService removed

try:
    from google_drive_manager import GoogleDriveManager
except ImportError:
    class GoogleDriveManager:
        def __init__(self): pass
        def is_authenticated(self): return False
        def authenticate(self): return False

try:
    from recordings_page import RecordingsPage
except ImportError:
    class RecordingsPage(QWidget):
        back_to_cameras = pyqtSignal()
        def __init__(self, gdm): super().__init__()

try:
    from recording_manager import RecordingManager
except ImportError:
    class RecordingManager:
        def __init__(self): pass

try:
    from stream_manager import StreamManager
except ImportError:
    class StreamManager(QObject):
        stream_started = pyqtSignal(str)
        stream_stopped = pyqtSignal(str)
        stream_error = pyqtSignal(str, str)
        def __init__(self):
            super().__init__()

try:
    from enhanced_camera_manager import EnhancedCameraManager
except ImportError:
    class EnhancedCameraManager(QObject):
        frame_ready = pyqtSignal(str, object)
        detection_frame_ready = pyqtSignal(str, object, list, int)
        fire_smoke_frame_ready = pyqtSignal(str, object, list, dict)
        camera_error = pyqtSignal(str, str)
        fire_smoke_alert = pyqtSignal(str, str, float)
        def __init__(self):
            super().__init__()
        def is_people_detection_enabled(self, camera_id): return False
        def enable_people_detection(self, camera_id, enabled): pass
        def is_fire_smoke_detection_enabled(self, camera_id): return False
        def enable_fire_smoke_detection(self, camera_id, enabled): pass
        def stop_camera(self, camera_id): pass
        def remove_camera(self, camera_id): pass

import traceback
try:
    from ui_components import AddCameraDialog
    print("UI Dialog Loaded: REAL ONE")
except Exception as e:
    print("UI COMPONENT IMPORT ERROR:", e)
    # Log to file as well since console might close
    try:
        with open("ui_import_error.log", "w") as f:
            f.write(f"UI COMPONENT IMPORT ERROR: {e}\n")
            traceback.print_exc(file=f)
    except:
        pass
    traceback.print_exc()

try:
    from ui_components import StorageChoiceDialog, EnhancedCameraWidget, AddCameraDialog
except ImportError as e:
    print(f"Warning: Could not import ui_components: {e}")
    class StorageChoiceDialog(QDialog):
        def __init__(self, parent=None): super().__init__(parent)
        def get_choice(self): return "local"
    
    class EnhancedCameraWidget(QLabel):
        clicked = pyqtSignal(str)
        delete_clicked = pyqtSignal(str)
        def __init__(self, camera_id, camera_name): 
            super().__init__()
            self.camera_id = camera_id
            self.camera_name = camera_name
        def update_frame(self, frame): pass
        def update_detection_frame(self, frame): pass
        def update_fire_smoke_frame(self, frame, detections, alert_info): pass
        def set_detection_enabled(self, enabled): pass
    
    class AddCameraDialog(QDialog):
        def __init__(self, parent=None): 
            super().__init__(parent)
            self.setModal(True)
        def exec_(self): return QDialog.Rejected
        def get_camera_data(self): return None

try:
    from enhanced_fullscreen_widget import EnhancedFullScreenCameraWidget
except ImportError:
    class EnhancedFullScreenCameraWidget(QWidget):
        back_clicked = pyqtSignal()
        def __init__(self, camera_id, camera_name, clip_manager=None, fire_detection_backend=None):
            super().__init__()
            self.camera_id = camera_id
            self.camera_name = camera_name
        def update_frame(self, frame): pass
        def update_detection_frame(self, frame, detections, people_count): pass
        def update_fire_smoke_detection_frame(self, frame, detections, alert_info): pass
        def set_detection_systems(self, people_detector, fire_smoke_detector, camera_manager): pass

try:
    from enhanced_review_system import EventClipManager
except ImportError:
    class EventClipManager:
        def __init__(self): pass

try:
    from fire_detection_backend import FireDetectionBackend
except ImportError:
    class FireDetectionBackend(QObject):
        alert_created = pyqtSignal(str, str)
        alert_updated = pyqtSignal(str, str)
        backend_error = pyqtSignal(str)
        def __init__(self, backend_url="http://localhost:5000", user_id="system"):
            super().__init__()
        def create_fire_alert(self, *args): return None
        def test_connection(self): return False
        def set_current_user(self, user_id): pass
        def close(self): pass

try:
    from notification_manager import NotificationManager
except ImportError:
    class NotificationManager(QObject):
        def __init__(self, *args, **kwargs):
            super().__init__()
        def show_notification(self, *args, **kwargs): pass
        def show_fire_alert(self, *args, **kwargs): pass

try:
    from alerts_manager import AlertsManager, AlertsWidget
except ImportError:
    class AlertsManager:
        def __init__(self): pass
    
    class AlertsWidget(QWidget):
        def __init__(self, alerts_manager): super().__init__()

# CloudBackupManager removed

try:
    from user_managers import UserManager, UserManagementWidget
except ImportError:
    class UserManager:
        def __init__(self): pass
    
    class UserManagementWidget(QWidget):
        def __init__(self, user_manager): super().__init__()

try:
    from settings_manager import SettingsManager
    from settings_widget import SettingsWidget
except ImportError:
    print("Warning: Settings system not available")
    class SettingsManager:
        def __init__(self, *args, **kwargs): pass
        def get_setting(self, key, default=None): return default
        def set_setting(self, key, value): pass
        def save_settings(self): pass
    
    class SettingsWidget(QWidget):
        settings_applied = pyqtSignal()
        def __init__(self, settings_manager, parent=None): super().__init__(parent)



class CameraLocationManager(QWidget):
    """Camera location management widget for adding/editing camera coordinates"""
    
    location_updated = pyqtSignal(str, float, float)  # camera_id, lat, lng
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.camera_locations = {}
        self.setup_ui()
        self.load_camera_locations()
        
    def setup_ui(self):
        """Setup the camera location management UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("📍 Camera Location Manager")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                padding: 10px 0px;
            }
        """)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_camera_list)
        
        view_map_btn = QPushButton("🗺️ View All Locations")
        view_map_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        view_map_btn.clicked.connect(self.show_all_locations_map)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(view_map_btn)
        
        # Camera locations table
        self.setup_camera_table()
        
        # Add location form
        self.setup_add_location_form()
        
        layout.addWidget(header)
        layout.addWidget(self.camera_table_group)
        layout.addWidget(self.add_location_group)
        
    def setup_camera_table(self):
        """Setup camera locations table"""
        self.camera_table_group = QGroupBox("Camera Locations")
        self.camera_table_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        table_layout = QVBoxLayout(self.camera_table_group)
        
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(7)
        self.camera_table.setHorizontalHeaderLabels([
            "Camera Name", "Camera ID", "Latitude", "Longitude", "Floor", "Common", "Actions"
        ])
        
        # Style the table
        self.camera_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
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
        
        # Set column widths
        header = self.camera_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.camera_table)
        
    def setup_add_location_form(self):
        """Setup add/edit location form"""
        self.add_location_group = QGroupBox("Add/Edit Camera Location")
        self.add_location_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        form_layout = QVBoxLayout(self.add_location_group)
        
        # Form fields
        form_widget = QWidget()
        form_grid = QFormLayout(form_widget)
        
        # Camera selection
        self.camera_combo = QPushButton("Select Camera")
        self.camera_combo.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        self.camera_combo.clicked.connect(self.show_camera_selection)
        
        # Latitude input
        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90.0, 90.0)
        self.latitude_input.setDecimals(8)
        self.latitude_input.setValue(0.0)
        self.latitude_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        
        # Longitude input
        self.longitude_input = QDoubleSpinBox()
        self.longitude_input.setRange(-360.0, 360.0)
        self.longitude_input.setDecimals(8)
        self.longitude_input.setValue(0.0)
        self.longitude_input.setStyleSheet(self.latitude_input.styleSheet())
        
        # Floor selection
        self.floor_combo = QComboBox()
        self.floor_combo.addItems(["Ground", "1", "2", "3", "4", "Roof", "Other"])
        self.floor_combo.setEditable(True)
        self.floor_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        
        # Common field (QComboBox, editable, auto-suggest)
        self.common_combo = QComboBox()
        self.common_combo.setEditable(True)
        self.common_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        self.common_combo.setInsertPolicy(QComboBox.InsertAtTop)
        
        # Location name/description
        self.location_description = QLineEdit()
        self.location_description.setPlaceholderText("e.g., Main Entrance, Parking Lot, etc.")
        self.location_description.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ff3333;
            }
        """)
        
        form_grid.addRow("Camera:", self.camera_combo)
        form_grid.addRow("Latitude:", self.latitude_input)
        form_grid.addRow("Longitude:", self.longitude_input)
        form_grid.addRow("Floor:", self.floor_combo)
        form_grid.addRow("Common:", self.common_combo)
        form_grid.addRow("Description:", self.location_description)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        save_btn = QPushButton("💾 Save Location")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_camera_location)
        
        clear_btn = QPushButton("🗑️ Clear Form")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)
        
        get_location_btn = QPushButton("📍 Get Current Location")
        get_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        get_location_btn.clicked.connect(self.get_current_location)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(get_location_btn)
        buttons_layout.addStretch()
        
        form_layout.addWidget(form_widget)
        form_layout.addWidget(buttons_widget)
        
        # Selected camera info
        self.selected_camera_id = None
        self.selected_camera_name = None
        
    def show_camera_selection(self):
        """Show camera selection dialog"""
        cameras = self.config_manager.load_cameras()
        
        if not cameras:
            QMessageBox.information(self, "No Cameras", "No cameras found. Please add cameras first.")
            return
            
        dialog = CameraSelectionDialog(cameras, self)
        if dialog.exec_() == QDialog.Accepted:
            camera_id, camera_name = dialog.get_selected_camera()
            if camera_id:
                self.selected_camera_id = camera_id
                self.selected_camera_name = camera_name
                self.camera_combo.setText(f"📹 {camera_name}")
                
                # Load existing location if available
                if camera_id in self.camera_locations:
                    location = self.camera_locations[camera_id]
                    self.latitude_input.setValue(location['latitude'])
                    self.longitude_input.setValue(location['longitude'])
                    self.location_description.setText(location.get('description', ''))
                    self.floor_combo.setCurrentText(location.get('floor', ''))
                    self.common_combo.setCurrentText(location.get('common', ''))
                    
    def save_camera_location(self):
        """Save camera location"""
        if not self.selected_camera_id:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera first.")
            return
            
        latitude = self.latitude_input.value()
        longitude = self.longitude_input.value()
        description = self.location_description.text().strip()
        floor = self.floor_combo.currentText().strip()
        common = self.common_combo.currentText().strip()
        if common and self.common_combo.findText(common) == -1:
            self.common_combo.addItem(common)
        
        if latitude == 0.0 and longitude == 0.0:
            reply = QMessageBox.question(self, "Confirm Location", 
                                       "Latitude and Longitude are both 0.0. Are you sure this is correct?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Save location
        self.camera_locations[self.selected_camera_id] = {
            'camera_name': self.selected_camera_name,
            'latitude': latitude,
            'longitude': longitude,
            'floor': floor,
            'common': common,
            'description': description,
            'timestamp': time.time()
        }
        
        self.save_camera_locations()
        self.refresh_camera_table()
        self.clear_form()
        
        # Emit signal
        self.location_updated.emit(self.selected_camera_id, latitude, longitude)
        
        QMessageBox.information(self, "Location Saved", 
                              f"Location saved for camera '{self.selected_camera_name}'")
    
    def clear_form(self):
        """Clear the form"""
        self.selected_camera_id = None
        self.selected_camera_name = None
        self.camera_combo.setText("Select Camera")
        self.latitude_input.setValue(0.0)
        self.longitude_input.setValue(0.0)
        self.location_description.clear()
        self.floor_combo.setCurrentText('')
        self.common_combo.setCurrentText('')
        
    def get_current_location(self):
        """Get current location (placeholder - would need geolocation API)"""
        QMessageBox.information(self, "Get Location", 
                              "This feature would integrate with geolocation services.\n"
                              "For now, please enter coordinates manually.\n\n"
                              "You can use Google Maps to find coordinates:\n"
                              "1. Right-click on location in Google Maps\n"
                              "2. Click on coordinates to copy them")
        
    def refresh_camera_list(self):
        """Refresh the camera list"""
        self.load_camera_locations()
        self.refresh_camera_table()
        
    def refresh_camera_table(self):
        """Refresh the camera table"""
        self.camera_table.setRowCount(len(self.camera_locations))
        
        for row, (camera_id, location) in enumerate(self.camera_locations.items()):
            # Camera name
            name_item = QTableWidgetItem(location['camera_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 0, name_item)
            
            # Camera ID
            id_item = QTableWidgetItem(camera_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 1, id_item)
            
            # Latitude
            lat_item = QTableWidgetItem(f"{location['latitude']:.6f}")
            lat_item.setFlags(lat_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 2, lat_item)
            
            # Longitude
            lng_item = QTableWidgetItem(f"{location['longitude']:.6f}")
            lng_item.setFlags(lng_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 3, lng_item)
            
            # Floor
            floor_item = QTableWidgetItem(location.get('floor', ''))
            floor_item.setFlags(floor_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 4, floor_item)
            
            # Common
            common_item = QTableWidgetItem(location.get('common', ''))
            common_item.setFlags(common_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 5, common_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setToolTip("Edit Location")
            edit_btn.clicked.connect(lambda checked, cid=camera_id: self.edit_camera_location(cid))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setToolTip("Delete Location")
            delete_btn.clicked.connect(lambda checked, cid=camera_id: self.delete_camera_location(cid))
            
            map_btn = QPushButton("🗺️")
            map_btn.setFixedSize(30, 30)
            map_btn.setToolTip("Show on Map")
            map_btn.clicked.connect(lambda checked, cid=camera_id: self.show_camera_on_map(cid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(map_btn)
            actions_layout.addStretch()
            
            self.camera_table.setCellWidget(row, 6, actions_widget)
            
    def edit_camera_location(self, camera_id):
        """Edit camera location"""
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            self.selected_camera_id = camera_id
            self.selected_camera_name = location['camera_name']
            self.camera_combo.setText(f"📹 {location['camera_name']}")
            self.latitude_input.setValue(location['latitude'])
            self.longitude_input.setValue(location['longitude'])
            self.location_description.setText(location.get('description', ''))
            self.floor_combo.setCurrentText(location.get('floor', ''))
            self.common_combo.setCurrentText(location.get('common', ''))
            
    def delete_camera_location(self, camera_id):
        """Delete camera location"""
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            reply = QMessageBox.question(self, "Delete Location",
                                       
                                       f"Are you sure you want to delete the location for camera '{location['camera_name']}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.camera_locations[camera_id]
                self.save_camera_locations()
                self.refresh_camera_table()
                QMessageBox.information(self, "Location Deleted", "Camera location deleted successfully.")
                
    def show_camera_on_map(self, camera_id):
        """Show single camera on map"""
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            self.show_map_with_cameras({camera_id: location})
            
    def show_all_locations_map(self):
        """Show all camera locations on map"""
        if not self.camera_locations:
            QMessageBox.information(self, "No Locations", "No camera locations found.")
            return
        self.show_map_with_cameras(self.camera_locations)
        
    def show_map_with_cameras(self, cameras_dict):
        """Show map with specified cameras"""
        try:
            # Create map centered on first camera or default location
            if cameras_dict:
                first_location = list(cameras_dict.values())[0]
                center_lat = first_location['latitude']
                center_lng = first_location['longitude']
            else:
                center_lat, center_lng = 0.0, 0.0
                
            # Create folium map
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=15 if cameras_dict else 2,
                tiles='OpenStreetMap'
            )
            
            # Add camera markers
            for camera_id, location in cameras_dict.items():
                popup_text = f"""
                <b>📹 {location['camera_name']}</b><br>
                <b>ID:</b> {camera_id}<br>
                <b>Location:</b> {location.get('description', 'No description')}<br>
                <b>Coordinates:</b> {location['latitude']:.6f}, {location['longitude']:.6f}
                """
                
                folium.Marker(
                    location=[location['latitude'], location['longitude']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=location['camera_name'],
                    icon=folium.Icon(color='blue', icon='video-camera', prefix='fa')
                ).add_to(m)
            
            # Save map to temporary file and open
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            m.save(temp_file.name)
            
            # Open in default browser
            webbrowser.open(f'file://{temp_file.name}')
            
        except Exception as e:
            QMessageBox.critical(self, "Map Error", f"Error creating map: {str(e)}")
            
    def load_camera_locations(self):
        """Load camera locations from file"""
        try:
            locations_file = resource_path("config/camera_locations.json")
            if os.path.exists(locations_file):
                with open(locations_file, 'r') as f:
                    self.camera_locations = json.load(f)
            else:
                self.camera_locations = {}
        except Exception as e:
            print(f"❌ Error loading camera locations: {e}")
            self.camera_locations = {}
            
    def save_camera_locations(self):
        """Save camera locations to file"""
        try:
            locations_file = resource_path("config/camera_locations.json")
            os.makedirs(os.path.dirname(locations_file), exist_ok=True)
            with open(locations_file, 'w') as f:
                json.dump(self.camera_locations, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving camera locations: {e}")
            
    def get_camera_location(self, camera_id):
        """Get location for a specific camera"""
        return self.camera_locations.get(camera_id)


class CameraSelectionDialog(QDialog):
    """Dialog for selecting a camera"""
    
    def __init__(self, cameras, parent=None):
        super().__init__(parent)
        self.cameras = cameras
        self.selected_camera_id = None
        self.selected_camera_name = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Select Camera")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select a Camera")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
            }
        """)
        
        # Camera list
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(2)
        self.camera_table.setHorizontalHeaderLabels(["Camera Name", "Camera ID"])
        self.camera_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Populate table
        self.camera_table.setRowCount(len(self.cameras))
        for row, (camera_id, camera_data) in enumerate(self.cameras.items()):
            name_item = QTableWidgetItem(camera_data.get('name', 'Unknown'))
            id_item = QTableWidgetItem(camera_id)
            
            self.camera_table.setItem(row, 0, name_item)
            self.camera_table.setItem(row, 1, id_item)
            
        self.camera_table.doubleClicked.connect(self.on_camera_double_clicked)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(select_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.camera_table)
        layout.addWidget(buttons_widget)
        
    def on_camera_double_clicked(self):
        """Handle camera double click"""
        self.accept()
        
    def accept(self):
        """Accept dialog and get selected camera"""
        current_row = self.camera_table.currentRow()
        if current_row >= 0:
            self.selected_camera_name = self.camera_table.item(current_row, 0).text()
            self.selected_camera_id = self.camera_table.item(current_row, 1).text()
        super().accept()
        
    def get_selected_camera(self):
        """Get selected camera ID and name"""
        return self.selected_camera_id, self.selected_camera_name


class FireLocationMapWidget(QWidget):
    """Widget to show fire detection location on map"""
    
    def __init__(self, camera_location_manager):
        super().__init__()
        self.camera_location_manager = camera_location_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the fire location map UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #ff0000;
                border-radius: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        title = QLabel("🚨 FIRE DETECTED - LOCATION MAP 🚨")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        close_btn = QPushButton("✖️ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        # Map container (placeholder)
        self.map_container = QLabel()
        self.map_container.setAlignment(Qt.AlignCenter)
        self.map_container.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 8px;
                color: white;
                font-size: 16px;
            }
        """)
        self.map_container.setText("🗺️ Map will be displayed here")
        
        layout.addWidget(header)
        layout.addWidget(self.map_container)
        
    def show_fire_location(self, camera_id, camera_name):
        """Show fire location on map"""
        location = self.camera_location_manager.get_camera_location(camera_id)
        
        if not location:
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Camera ID: {camera_id}
            
            ⚠️ No location data available for this camera.
            Please add location coordinates in Camera Manager.
            """)
            return
            
        try:
            # Create emergency fire map
            m = folium.Map(
                location=[location['latitude'], location['longitude']],
                zoom_start=18,
                tiles='OpenStreetMap'
            )
            
            # Add fire marker
            popup_text = f"""
            <div style="text-align: center;">
                <h3 style="color: red;">🚨 FIRE ALERT 🚨</h3>
                <b>Camera:</b> {camera_name}<br>
                <b>Location:</b> {location.get('description', 'No description')}<br>
                <b>Coordinates:</b> {location['latitude']:.6f}, {location['longitude']:.6f}<br>
                <b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            """
            
            # Add pulsing fire marker
            folium.Marker(
                location=[location['latitude'], location['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"🔥 FIRE: {camera_name}",
                icon=folium.Icon(color='red', icon='fire', prefix='fa')
            ).add_to(m)
            
            # Add circle to highlight area
            folium.Circle(
                location=[location['latitude'], location['longitude']],
                radius=100,  # 100 meter radius
                color='red',
                fillColor='red',
                fillOpacity=0.3,
                popup='Fire Detection Area'
            ).add_to(m)
            
            # Save and display map
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            m.save(temp_file.name)
            
            # Open in browser for fullscreen view
            webbrowser.open(f'file://{temp_file.name}')
            
            # Update container text
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Location: {location.get('description', 'No description')}
            Coordinates: {location['latitude']:.6f}, {location['longitude']:.6f}
            
            🗺️ Map opened in browser for fullscreen view
            """)
            
        except Exception as e:
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Camera ID: {camera_id}
            
            ❌ Error loading map: {str(e)}
            """)


class LoadingWidget(QWidget):
    """Loading animation widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Loading spinner
        self.spinner = QLabel("⏳")
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner.setStyleSheet("""
            QLabel {
                font-size: 48px;
                color: #8B5CF6;
                background: transparent;
            }
        """)
        
        # Loading text
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
        
        # Start animation
        self.start_animation()
        
    def start_animation(self):
        """Start the loading animation"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_spinner)
        self.animation_timer.start(100)  # Update every 100ms
        self.animation_frame = 0
        
    def animate_spinner(self):
        """Animate the spinner"""
        spinners = ["⏳", "⏰", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
        self.spinner.setText(spinners[self.animation_frame % len(spinners)])
        self.animation_frame += 1
        
    def stop_animation(self):
        """Stop the loading animation"""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
            
    def set_loading_text(self, text):
        """Update loading text"""
        self.loading_text.setText(text)


class ModernLoginDialog(QDialog):
    """Modern login dialog matching the provided design exactly"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fire Vision Pro - Login")
        self.setFixedSize(1366, 768)  # Match splash screen size
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        self.is_signup_mode = False  # Always start in login mode
        
        self.setup_ui()
        
        # Load saved login if available
        self.load_saved_login()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Panel with Full Image ---
        left_panel = QWidget()
        left_panel.setFixedWidth(600)
        left_panel.setStyleSheet("border-radius: 32px; background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        # Full image only
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

        # --- Right Panel with Form ---
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

        # Centered form container
        form_centerer = QWidget()
        form_centerer.setFixedWidth(360)
        form_centerer_layout = QVBoxLayout(form_centerer)
        form_centerer_layout.setContentsMargins(0, 0, 0, 0)
        form_centerer_layout.setSpacing(22)

        # Title section
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

        # Subtitle with login link
        subtitle_widget = QWidget()
        subtitle_layout = QHBoxLayout(subtitle_widget)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(5)

        subtitle_text = QLabel("Already have an account?")
        subtitle_text.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        self.toggle_link = QPushButton("Log in")
        self.toggle_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8B5CF6;
                border: none;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                text-decoration: underline;
                padding: 0px;
            }
            QPushButton:hover {
                color: #A855F7;
            }
        """)
        self.toggle_link.clicked.connect(self.toggle_mode)

        subtitle_layout.addWidget(subtitle_text)
        subtitle_layout.addWidget(self.toggle_link)
        subtitle_layout.addStretch()

        # Add title and subtitle to the form layout
        form_centerer_layout.addWidget(self.title_label)
        form_centerer_layout.addWidget(subtitle_widget)

        # First row - First name and Last name (only for signup)
        self.name_row = QWidget()
        name_layout = QHBoxLayout(self.name_row)
        name_layout.setSpacing(12)
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Fletcher")
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        self.first_name_input.setMaximumWidth(170)
        self.last_name_input.setMaximumWidth(170)
        name_layout.addWidget(self.first_name_input)
        name_layout.addWidget(self.last_name_input)

        # Username field (for login mode)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.hide()
        self.username_input.setMaximumWidth(360)
        # Enable Enter key to move to password field
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setMaximumWidth(360)
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMaximumWidth(360)
        # Enable Enter key to submit login
        self.password_input.returnPressed.connect(self.handle_action)
        
        # Password visibility toggle - positioned inside the field
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
        
        # Create password container
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)
        
        # Add the button to the password input field
        self.password_input.setLayout(QHBoxLayout())
        self.password_input.layout().addStretch()
        self.password_input.layout().addWidget(self.show_password_btn)
        self.password_input.layout().setContentsMargins(0, 0, 8, 0)
        self.password_input.layout().setSpacing(0)
        
        password_layout.addWidget(self.password_input)

        # Style all input fields
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
        for field in [self.first_name_input, self.last_name_input, self.username_input, self.email_input, self.password_input]:
            field.setStyleSheet(input_style)
            field.setFixedHeight(40)
            field.setMaximumWidth(360)

        # Terms checkbox (only for signup)
        self.terms_widget = QWidget()
        terms_layout = QHBoxLayout(self.terms_widget)
        terms_layout.setContentsMargins(0, 0, 0, 0)
        terms_layout.setSpacing(10)
        
        self.terms_checkbox = QCheckBox()
        self.terms_checkbox.setStyleSheet("""
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
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
            }
        """)
        
        terms_text = QLabel("I agree to the Terms & Conditions")
        terms_text.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        terms_layout.addWidget(self.terms_checkbox)
        terms_layout.addWidget(terms_text)
        terms_layout.addStretch()
        
        # Remember me checkbox (only for login)
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
        
        # Main action button
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
        
        # Or register with section
        or_widget = QWidget()
        or_layout = QVBoxLayout(or_widget)
        or_layout.setSpacing(15)
        
        or_label = QLabel("Or register with")
        or_label.setAlignment(Qt.AlignCenter)
        or_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Social buttons
        social_container = QWidget()
        social_layout = QHBoxLayout(social_container)
        social_layout.setSpacing(15)
        
        google_btn = QPushButton("Google")
        google_btn.setFixedHeight(44)
        google_btn.setMaximumWidth(170)
        google_btn.setStyleSheet("""
            QPushButton {
                background-color: #232136;
                color: white;
                border: 1px solid #4B5563;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 0px 20px;
            }
            QPushButton:hover {
                background-color: #4B5563;
                border-color: #6B7280;
            }
        """)
        
        apple_btn = QPushButton("Apple")
        apple_btn.setFixedHeight(44)
        apple_btn.setMaximumWidth(170)
        apple_btn.setStyleSheet("""
            QPushButton {
                background-color: #232136;
                color: white;
                border: 1px solid #4B5563;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 0px 20px;
            }
            QPushButton:hover {
                background-color: #4B5563;
                border-color: #6B7280;
            }
        """)
        
        social_layout.addWidget(google_btn)
        social_layout.addWidget(apple_btn)
        
        or_layout.addWidget(or_label)
        or_layout.addWidget(social_container)
        
        # Add fields to form_centerer_layout
        form_centerer_layout.addWidget(self.name_row)
        form_centerer_layout.addWidget(self.username_input)
        form_centerer_layout.addWidget(self.email_input)
        form_centerer_layout.addWidget(password_container)
        form_centerer_layout.addWidget(self.terms_widget)
        form_centerer_layout.addWidget(self.remember_widget)
        form_centerer_layout.addWidget(self.action_btn)
        form_centerer_layout.addWidget(or_widget)

        # Add the centered form to the right_layout
        right_layout.addWidget(form_centerer, alignment=Qt.AlignHCenter)
        right_layout.addStretch(2)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Create loading widget (initially hidden)
        self.loading_widget = LoadingWidget()
        self.loading_widget.hide()
        main_layout.addWidget(self.loading_widget)

        self.toggle_mode(force_signup=False)

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁")

    def toggle_mode(self, force_signup=None):
        if force_signup is not None:
            self.is_signup_mode = bool(force_signup)
        else:
            self.is_signup_mode = not self.is_signup_mode
        if self.is_signup_mode:
            self.title_label.setText("Create an account")
            self.action_btn.setText("Create account")
            self.toggle_link.setText("Log in")
            self.name_row.show()
            self.email_input.show()
            self.terms_widget.show()
            self.username_input.hide()
            self.remember_widget.hide()
            self.first_name_input.clear()
            self.last_name_input.clear()
            self.email_input.clear()
            self.password_input.clear()
        else:
            self.title_label.setText("Login to your account")
            self.action_btn.setText("Login")
            self.toggle_link.setText("Sign up")
            self.name_row.hide()
            self.email_input.hide()
            self.terms_widget.hide()
            self.username_input.show()
            self.remember_widget.show()
            self.password_input.clear()
            self.load_saved_login()

    def load_saved_login(self):
        """Load saved login details if available"""
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
        """Handle login or signup action"""
        if self.is_signup_mode:
            self.signup()
        else:
            self.login()

    def login(self):
        """Handle user login with immediate authentication"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        # Authenticate immediately without delay
        self.process_authentication(username, password)
        
    def show_loading_animation(self):
        """Show loading animation and hide form - kept for signup compatibility"""
        # Hide the form elements
        self.name_row.hide()
        self.username_input.hide()
        self.email_input.hide()
        self.password_input.hide()
        self.terms_widget.hide()
        self.remember_widget.hide()
        self.action_btn.hide()
        
        # Show loading widget
        self.loading_widget.show()
        self.loading_widget.set_loading_text("Creating account...")
        
    def process_authentication(self, username, password):
        """Process authentication immediately without backend calls"""
        try:
            success = self.config_manager.authenticate_user(username, password)
            
            if success:
                # Complete login immediately without any backend validation
                self.complete_login(username)
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")
            
    def complete_login(self, username):
        """Complete the login process immediately"""
        try:
            remember = self.remember_checkbox.isChecked()
            self.config_manager.save_login_details(username, remember)
            
            self.username = username
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")
            
    def hide_loading_animation(self):
        """Hide loading animation and show form"""
        self.loading_widget.hide()
        self.loading_widget.stop_animation()
        
        # Show the form elements again
        if not self.is_signup_mode:
            self.name_row.hide()  # Hide for login mode
            self.username_input.show()
            self.email_input.hide()  # Hide for login mode
            self.password_input.show()
            self.terms_widget.hide()  # Hide for login mode
            self.remember_widget.show()
            self.action_btn.show()
        else:
            self.name_row.show()  # Show for signup mode
            self.username_input.hide()  # Hide for signup mode
            self.email_input.show()
            self.password_input.show()
            self.terms_widget.show()  # Show for signup mode
            self.remember_widget.hide()  # Hide for signup mode
            self.action_btn.show()

    def signup(self):
        """Handle user signup with immediate processing"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not first_name or not last_name or not email or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        if not self.terms_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please agree to the Terms & Conditions.")
            return

        # Create username from first name + last name
        username = f"{first_name.lower()}{last_name.lower()}"
        
        # Process signup immediately
        success = self.config_manager.create_user(username, password, email)
        
        if success:
            QMessageBox.information(self, "Success", "Account created successfully! You can now login.")
            self.toggle_mode()
            self.username_input.setText(username)
            self.password_input.setFocus()  # Focus on password field for quick login
        else:
            QMessageBox.warning(self, "Error", "Username already exists. Please try different names.")

    def get_username(self):
        """Get the logged in username"""
        return getattr(self, 'username', self.username_input.text().strip())


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
        """Setup the card UI to match the reference design"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        # Top row: Date (right aligned)
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

        # Alert type title
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

        # Camera info
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

        # Time info
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

        # Location info
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

        # Bottom row: Status icons (right aligned)
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
        """Handle mouse click to show camera"""
        if event.button() == Qt.LeftButton and self.camera_id:
            self.clicked.emit(self.camera_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter for hover effect"""
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
        """Handle mouse leave to restore normal appearance"""
        self.setStyleSheet("""
            QWidget {
                background-color: #020203;
                border: 2px solid #f44336;
                border-radius: 10px;
                margin: 2px;
            }
        """)
        super().leaveEvent(event)


# --- Skeleton Camera Widget ---
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
        # Ignore frames while loading
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
# --- Camera Loader Thread ---
class CameraLoaderThread(QThread):
    camera_loaded = pyqtSignal(dict)
    camera_failed = pyqtSignal(str, str)  # camera_id, error message

    def __init__(self, camera_data, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_data = camera_data
        self.camera_manager = camera_manager

    def run(self):
        try:
            # Actually start the camera directly in camera_manager
            self.camera_manager.add_camera(
                self.camera_data['id'],
                self.camera_data['name'],
                self.camera_data['source'],
                self.camera_data['type'],
                skip_test=True
            )
            self.camera_manager.start_camera(self.camera_data['id'])
            self.camera_loaded.emit(self.camera_data)
        except Exception as e:
            self.camera_failed.emit(self.camera_data['id'], str(e))


class InitWorker(QThread):
    """Worker thread for heavy initialization tasks to keep UI responsive and speed up startup"""
    finished = pyqtSignal()
    progress = pyqtSignal(int, str)

    def __init__(self, main_window):
        super().__init__()
        self.window = main_window

    def run(self):
        try:
            print("🚀 Background initialization started...")
            
            # 1. Load YOLO model (HEAVY)
            self.progress.emit(30, "Loading AI models...")
            try:
                from ultralytics import YOLO
                self.window.model = YOLO(resource_path('yolov8n.pt'))
                print(f"✅ AI Model loaded. Device: {self.window.model.device}")
            except Exception as e:
                print(f"⚠️ Failed to load YOLO in background: {e}")

            # Background initialization finished

            # 3. Initialize Clip Manager
            self.progress.emit(90, "Finalizing configuration...")
            try:
                self.window.clip_manager = EventClipManager()
            except Exception as e:
                print(f"⚠️ Failed to init ClipManager: {e}")
            
            self.progress.emit(100, "System Ready")
            print("✅ Background initialization complete.")
            self.finished.emit()
        except Exception as e:
            print(f"❌ Critical error in InitWorker: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit()


class PersistentMainWindow(QMainWindow):
    """Enhanced main window with fire/smoke detection integration"""
    initialization_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        # Frameless window for custom title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(1400, 900)
        self._drag_pos = None
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.stream_manager = StreamManager()
        self.camera_manager = EnhancedCameraManager(config_manager=self.config_manager)
        if hasattr(self.stream_manager, 'set_config_manager'):
            self.stream_manager.set_config_manager(self.config_manager)
        self.background_service = None # Set to None to avoid breaking other references
        self.recording_manager = RecordingManager()
        self.google_drive_manager = GoogleDriveManager()
        
        # --- Background Initialization ---
        self.model = None
        self.init_worker = InitWorker(self)
        self.init_worker.finished.connect(self._on_initialization_complete)
        # We'll start the worker after UI setup is complete
        
        # Initialize map components BEFORE setup_ui
        self.camera_location_manager = CameraLocationManager(self.config_manager)
        self.fire_location_map = FireLocationMapWidget(self.camera_location_manager)
        
        # Initialize fire detection backend
        backend_url = self.config_manager.get_config("server_settings.stream_server_url", "http://localhost:5000")
        self.fire_detection_backend = FireDetectionBackend(backend_url, "system")
        
        # Initialize notification manager for mobile app integration
        mobile_app_url = self.config_manager.get_config("mobile_settings.app_url", "http://192.168.1.4:58766")
        self.notification_manager = NotificationManager(
            backend_url=backend_url,
            mobile_app_url=mobile_app_url,
            user_id="system",
            config_manager=self.config_manager
        )
        
        # Camera widgets storage
        self.camera_widgets = {}
        self.fullscreen_widgets = {}
        
        # --- Integrate new managers and widgets ---
        self.alerts_manager = AlertsManager()
        self.user_manager = UserManager()
        self.alerts_widget = AlertsWidget(self.alerts_manager)
        self.user_management_widget = UserManagementWidget(self.user_manager)
        
        # Initialize voice command system
        self.voice_manager = VoiceCommandManager(self)
        self.voice_widget = VoiceCommandWidget(self.voice_manager)
        
        # Initialize settings system
        self.settings_manager = SettingsManager()
        self.settings_widget = SettingsWidget(self.settings_manager, config_manager=self.config_manager)
        self.settings_widget.settings_applied.connect(self.reload_configuration)
        
        # Setup system tray
        self.setup_system_tray()
        
        # Apply dark theme
        self.apply_dark_theme()

        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()

        # Start background initialization (DEFERRED)
        self.init_worker.start()

        # Test backend connection asynchronously (don't block UI)
        QTimer.singleShot(1000, self.test_backend_connection)

        # --- Auto Mode Optimizer ---
        # --- Auto Mode Optimizer & Manual NVR ---
        auto_optimize = self.settings_manager.get_setting("system.auto_mode_optimizer", True)
        manual_nvr = self.settings_manager.get_setting("system.nvr_mode_enabled", False)
        
        # 1. Manual NVR Mode (Highest Priority)
        if manual_nvr:
            print("🛑 Manual NVR-Only Mode is ENABLED. Disabling AI features on startup.")
            def force_nvr_startup():
                try:
                    if hasattr(self.camera_manager, 'fire_smoke_detector'):
                         self.camera_manager.fire_smoke_detector.set_nvr_mode(True)
                except Exception as e:
                    print(f"⚠️ Failed to enforce NVR mode on startup: {e}")
            QTimer.singleShot(500, force_nvr_startup)
            
        # 2. Auto Optimizer (If manual mode is OFF)
        elif profiler and auto_optimize:
            # Run in background to avoid freezing startup
            def run_optimization():
                print("🚀 Running Auto Mode Optimizer...")
                is_low_end, specs = profiler.profile_system()
                self.settings_manager.set_setting("system.hardware_specs", specs)
                
                if is_low_end:
                    # Respect user choice if they explicitly set Standard mode
                    if self.settings_manager.get_setting("system.optimization_mode") == "Standard":
                        print("⚠️ Low-end detected but User explicitly chose Standard mode. Respecting choice.")
                        return

                    current_nvr = self.settings_manager.get_setting("system.nvr_mode_enabled", False)
                    if not current_nvr:
                        print("⚠️ Low-end device detected! Switching to NVR-Only Mode.")
                        self.settings_manager.set_setting("system.nvr_mode_enabled", True)
                        self.settings_manager.set_setting("system.optimization_mode", "NVR")
                        
                        # Apply settings
                        self.settings_manager.set_setting("fire_detection.model_selection", "Disabled (NVR Mode)")
                        self.settings_manager.set_setting("camera.ai_processing_mode", "None")
                        self.settings_manager.save_settings()
                        
                        # Unload AI models
                        try:
                            if hasattr(self.camera_manager, 'fire_smoke_detector'):
                                self.camera_manager.fire_smoke_detector.set_nvr_mode(True)
                        except Exception as e:
                            print(f"⚠️ Failed to unload fire detector: {e}")
                        
                        # Notify user
                        QMessageBox.information(
                            self, 
                            "Performance Optimization", 
                            "Low-end hardware detected.\n\nSwitched to 'NVR-Only Mode' to ensure smooth performance.\nAI detections have been disabled.\n(You can disable this in Settings)"
                        )
                else:
                    self.settings_manager.set_setting("system.optimization_mode", "Standard")
                    self.settings_manager.save_settings()
            
            QTimer.singleShot(500, run_optimization)

        self._last_map_highlight = None
        self._last_map_camera_locations = None
        self._last_map_tempfile = None

        self.map_bridge = MapBridge(self)
        self.web_channel = QWebChannel()
        self.web_channel.registerObject('bridge', self.map_bridge)
        self.map_view.page().setWebChannel(self.web_channel)

    def _on_initialization_complete(self):
        """Called when background initialization is finished"""
        print("🎉 All background systems initialized.")
        self.initialization_finished.emit()


    def setup_system_tray(self):
        """Setup system tray for background operation"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            icon = self.style().standardIcon(self.style().SP_ComputerIcon)
            self.tray_icon.setIcon(icon)
            
            tray_menu = QMenu()
            
            show_action = QAction("Show Fire Vision Pro", self)
            show_action.triggered.connect(self.show_from_tray)
            
            # Voice command actions
            voice_start_action = QAction("🎤 Start Voice Commands", self)
            voice_start_action.triggered.connect(self.voice_manager.start_listening)
            
            voice_stop_action = QAction("🔇 Stop Voice Commands", self)
            voice_stop_action.triggered.connect(self.voice_manager.stop_listening)
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            
            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(voice_start_action)
            tray_menu.addAction(voice_stop_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            self.tray_icon.show()
            self.tray_icon.setToolTip("Fire Vision Pro - Background Service Running")
        else:
            self.tray_icon = None
            print("⚠️ System tray not available")

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_from_tray()

    def show_from_tray(self):
        """Show window from system tray and require login"""
        self.config_manager.set_current_user(None)
        
        # Clear UI camera widgets
        for widget in list(self.camera_widgets.values()):
            widget.setParent(None)
        self.camera_widgets.clear()
        for widget in list(self.fullscreen_widgets.values()):
            widget.setParent(None)
        self.fullscreen_widgets.clear()
        self.update_camera_grid()
        
        # Show login screen
        self.show_login_screen()
        
        # Show window after login
        self.show()
        self.raise_()
        self.activateWindow()

    # Removed show_service_status
        
    def reload_configuration(self):
        """
        Reload configuration for all subsystems.
        
        Configuration Reload Rules:
        - NotificationManager: Immediate (URLs updated instantly)
        - FireSmokeDetector: Immediate (thresholds/modes updated instantly)
        - StreamManager: Next Stream Start (config applied when new stream starts)
        
        This ensures consistency without disrupting active operations.
        """
        print("🔄 Reloading all configurations...")
        
        try:
            # 1. Reload Notification Manager
            if hasattr(self, 'notification_manager'):
                self.notification_manager.reload_config()
                
            # 2. Reload Fire Detection (via Camera Manager)
            if hasattr(self, 'camera_manager') and hasattr(self.camera_manager, 'fire_smoke_detector'):
                 self.camera_manager.fire_smoke_detector.reload_config()
                 
            # 3. Reload Stream Manager
            if hasattr(self, 'stream_manager'):
                # Pass config manager again just in case (though it's reference)
                if hasattr(self.stream_manager, 'set_config_manager'):
                    self.stream_manager.set_config_manager(self.config_manager)
            
            print("✅ Configuration reload complete.")
        except Exception as e:
            print(f"❌ Error reloading configuration: {e}")

    def quit_application(self):
        """Quit the entire application"""
        reply = QMessageBox.question(
            self, 'Quit Application',
            'This will stop all cameras and streams. Are you sure?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.stop_all_cameras_and_clear_session()
            if self.tray_icon:
                self.tray_icon.hide()
            QApplication.quit()

    def stop_all_cameras_and_clear_session(self):
        """Stop all cameras and clear the session"""
        try:
            print("🛑 Stopping all cameras and clearing session...")
            
            # Stop all cameras in the camera manager
            for camera_id in list(self.camera_widgets.keys()):
                try:
                    self.camera_manager.stop_camera(camera_id)
                    print(f"🛑 Stopped camera: {camera_id}")
                except Exception as e:
                    print(f"❌ Error stopping camera {camera_id}: {e}")
            
            # Clear current user session to force re-login when reopened
            self.config_manager.set_current_user(None)
                
            # Clear UI camera widgets
            for widget in list(self.camera_widgets.values()):
                widget.setParent(None)
            self.camera_widgets.clear()
            
            for widget in list(self.fullscreen_widgets.values()):
                widget.setParent(None)
            self.fullscreen_widgets.clear()
            
            self.update_camera_grid()
            
            # Update status
                
            print("✅ All cameras stopped and session cleared")
            
        except Exception as e:
            print(f"❌ Error stopping cameras and clearing session: {e}")

    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff; /* Ensure text/icon is visible */
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                color: #ffffff; /* Ensure text/icon is visible on hover */
            }
            QPushButton:pressed {
                background-color: #505050;
                color: #ffffff; /* Ensure text/icon is visible when pressed */
            }
            QPushButton#navButton {
                text-align: left;
                padding: 16px 20px;
                font-size: 16px;
                border-radius: 0px;
                background-color: transparent;
                color: #ffffff; /* Ensure text/icon is visible */
            }
            QPushButton#navButton:hover {
                background-color: #2d2d2d;
                color: #ffffff; /* Ensure text/icon is visible on hover */
            }
            QPushButton#activeNavButton {
                text-align: left;
                padding: 16px 20px;
                font-size: 16px;
                background-color: #3d3d3d;
                color: #ff3333;
                border-radius: 0px;
                border-left: 3px solid #ff3333;
            }
            QPushButton#logoutButton {
                background-color: #ff3333;
                color: white;
                padding: 5px 10px;
                font-size: 10px;
            }
            QPushButton#addButton {
                background-color: #ff3333;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #505050;
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #ff3333;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px 0px;
            }
            QLabel#logoLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ff3333;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #cccccc;
            }
        """)

    def setup_ui(self):
        """Setup the main user interface (modern dashboard style with custom title bar)"""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        self.create_custom_title_bar(main_layout)

        # Main dashboard area (horizontal layout)
        dashboard_area = QWidget()
        dashboard_layout = QHBoxLayout(dashboard_area)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(0)
        # Sidebar
        self.create_dashboard_sidebar(dashboard_layout)
        # Main camera grid area
        self.create_dashboard_main_grid(dashboard_layout)

        main_layout.addWidget(dashboard_area, 1)

        self.setCentralWidget(central_widget)

    def create_custom_title_bar(self, main_layout):
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        title_bar.setStyleSheet("background-color: #111111; border-bottom: 1.5px solid #23284a;")

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(10)

        # App name label
        title_label = QLabel("Fire Vision Pro - CCTV Surveillance System with AI Detection")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Button style for icon buttons
        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

        # Minimize button with icon
        min_btn = QPushButton()
        min_icon = QIcon(resource_path("assests/icons/minimize.png"))
        min_btn.setIcon(min_icon)
        min_btn.setIconSize(QSize(20, 20))
        min_btn.setStyleSheet(btn_style)
        min_btn.setFixedSize(40, 32)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setToolTip("Minimize")

        # Maximize/Restore button with icon
        self._is_maximized = False
        self.max_btn = QPushButton()
        max_icon = QIcon(resource_path("assests/icons/restore.png"))
        self.max_btn.setIcon(max_icon)
        self.max_btn.setIconSize(QSize(20, 20))
        self.max_btn.setStyleSheet(btn_style)
        self.max_btn.setFixedSize(40, 32)
        self.max_btn.clicked.connect(self.toggle_max_restore)
        self.max_btn.setToolTip("Maximize")

        # Close button with icon and red hover
        close_btn = QPushButton()
        close_icon = QIcon(resource_path("assests/icons/close.png"))
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(QSize(20, 20))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        close_btn.setFixedSize(40, 32)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)

        # Assemble layout
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(min_btn)
        title_layout.addWidget(self.max_btn)
        title_layout.addWidget(close_btn)

        title_bar.setLayout(title_layout)
        main_layout.addWidget(title_bar)

        # Enable dragging
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def toggle_max_restore(self):
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
        else:
            self.showMaximized()
            self._is_maximized = True

    def create_dashboard_sidebar(self, dashboard_layout):
        """Create the sidebar navigation"""
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("background-color: #111111; border: none;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(10)

        # Load Inter font
        font_id = QFontDatabase.addApplicationFont(resource_path("assests/fonts/Inter/Inter-VariableFont_opsz,wght.ttf"))
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                inter_font_family = font_families[0]
            else:
                inter_font_family = "Inter"
        else:
            inter_font_family = "Inter"  # Fallback

        # Logo section - FireVision logo centered with settings icon
        logo_widget = QWidget()
        logo_widget.setFixedHeight(70)
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(8, 8, 8, 8)
        logo_layout.setSpacing(0)

        # FireVision Logo image centered
        logo_container = QWidget()
        logo_container_layout = QVBoxLayout(logo_container)
        logo_container_layout.setContentsMargins(0, 0, 0, 0)
        logo_container_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("assests/sidebar_icons/firevision_logo.png"))
        if not logo_pixmap.isNull():
            scaled_logo = logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_logo)
        else:
            # Fallback to FV text if image not found
            logo_label.setText("FV")
            logo_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_container_layout.addWidget(logo_label)
        
        logo_layout.addWidget(logo_container, 1)
        
        # Settings icon in top right
        settings_icon_btn = QPushButton()
        settings_icon_pixmap = QPixmap(resource_path("assests/sidebar_icons/settings.png"))
        if not settings_icon_pixmap.isNull():
            settings_icon_btn.setIcon(QIcon(settings_icon_pixmap))
            settings_icon_btn.setIconSize(QSize(22, 22))
        settings_icon_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        settings_icon_btn.setFixedSize(30, 30)
        settings_icon_btn.clicked.connect(self.show_settings_page)
        logo_layout.addWidget(settings_icon_btn, alignment=Qt.AlignTop | Qt.AlignRight)
        
        sidebar_layout.addWidget(logo_widget)
        
        # Add spacing to move navigation links down
        sidebar_layout.addSpacing(20)

        # Helper function to create nav button with icon
        def create_nav_button(text, icon_name, is_active=False):
            btn = QPushButton()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(16, 12, 16, 12)
            btn_layout.setSpacing(14)
            
            # Icon
            icon_label = QLabel()
            icon_pixmap = QPixmap(resource_path(f"assests/sidebar_icons/{icon_name}.png"))
            if not icon_pixmap.isNull():
                scaled_icon = icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(scaled_icon)
            icon_label.setFixedSize(24, 24)
            
            # Text
            text_label = QLabel(text)
            text_label.setStyleSheet(f"color: white; font-size: 15px; font-weight: 500; font-family: '{inter_font_family}';")
            
            btn_layout.addWidget(icon_label)
            btn_layout.addWidget(text_label)
            btn_layout.addStretch()
            
            # Create container widget for the layout
            container = QWidget()
            container.setAttribute(Qt.WA_TranslucentBackground)
            container.setStyleSheet("background: transparent;")
            container.setLayout(btn_layout)
            
            # Set the container as the button's layout
            main_layout = QVBoxLayout(btn)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(container)
            
            if is_active:
                btn.setObjectName("activeNavButton")
                btn.setStyleSheet("""
                    QPushButton#activeNavButton {
                        background-color: #1e3a5f;
                        border-radius: 10px;
                        border: none;
                        border-left: 3px solid #4a90e2;
                    }
                    QPushButton#activeNavButton:hover {
                        background-color: #2a4a6f;
                    }
                """)
            else:
                btn.setObjectName("navButton")
                btn.setStyleSheet("""
                    QPushButton#navButton {
                        background-color: transparent;
                        border-radius: 10px;
                        border: none;
                    }
                    QPushButton#navButton:hover {
                        background-color: #2a2a2a;
                    }
                """)
            
            btn.setFixedHeight(48)
            btn.setCursor(Qt.PointingHandCursor)
            return btn

        # Navigation buttons
        self.cameras_btn = create_nav_button("Cameras", "dashboard", is_active=True)
        self.cameras_btn.clicked.connect(self.show_cameras_page)

        self.recordings_btn = create_nav_button("Recordings", "recordings")
        self.recordings_btn.clicked.connect(self.show_recordings_page)

        # Service button removed

        self.alerts_btn = create_nav_button("Alerts", "alerts")
        self.alerts_btn.clicked.connect(self.show_alerts_page)

        # Backup button removed

        self.camera_manager_btn = create_nav_button("Camera manager", "camera_manager")
        self.camera_manager_btn.clicked.connect(self.show_camera_manager_page)

        self.map_overview_btn = create_nav_button("Map overview", "map")
        self.map_overview_btn.clicked.connect(self.show_map_overview_page)

        # Device settings button removed

        self.settings_btn = create_nav_button("Settings", "settings")
        self.settings_btn.clicked.connect(self.show_settings_page)

        # Create hidden users_btn placeholder to avoid errors in navigation methods
        self.users_btn = create_nav_button("Users", "user")
        self.users_btn.hide()  # Hide it since it's not in the reference design
        
        sidebar_layout.addWidget(self.cameras_btn)
        sidebar_layout.addWidget(self.recordings_btn)
        sidebar_layout.addWidget(self.alerts_btn)
        sidebar_layout.addWidget(self.camera_manager_btn)
        sidebar_layout.addWidget(self.map_overview_btn)
        sidebar_layout.addWidget(self.settings_btn)
        
        sidebar_layout.addStretch()
        
        # User profile section at bottom
        user_widget = QWidget()
        user_widget.setFixedHeight(65)
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(10, 10, 10, 10)
        user_layout.setSpacing(14)

        # User icon with circular background
        user_icon_container = QWidget()
        user_icon_container.setFixedSize(48, 48)
        user_icon_container.setStyleSheet("""
            background-color: #1a1a1a;
            border-radius: 24px;
        """)
        
        user_icon_layout = QVBoxLayout(user_icon_container)
        user_icon_layout.setContentsMargins(0, 0, 0, 0)
        user_icon_layout.setAlignment(Qt.AlignCenter)
        
        user_icon_label = QLabel()
        user_icon_pixmap = QPixmap(resource_path("assests/sidebar_icons/user.png"))
        if not user_icon_pixmap.isNull():
            scaled_user_icon = user_icon_pixmap.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            user_icon_label.setPixmap(scaled_user_icon)
        user_icon_label.setAlignment(Qt.AlignCenter)
        user_icon_layout.addWidget(user_icon_label)

        self.user_label = QLabel("Admin")
        self.user_label.setStyleSheet(f"color: white; font-size: 15px; font-weight: 500; font-family: '{inter_font_family}';")

        user_layout.addWidget(user_icon_container)
        user_layout.addWidget(self.user_label)
        user_layout.addStretch()

        sidebar_layout.addWidget(user_widget)
        dashboard_layout.addWidget(self.sidebar)

    def hide_to_tray(self):
        """Hide window to system tray and clear user session"""
        # Clear current user session to force re-login when reopened
        self.config_manager.set_current_user(None)
        
        # Clear UI camera widgets
        for widget in list(self.camera_widgets.values()):
            widget.setParent(None)
        self.camera_widgets.clear()
        for widget in list(self.fullscreen_widgets.values()):
            widget.setParent(None)
        self.fullscreen_widgets.clear()
        self.update_camera_grid()
        
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            if not self.config_manager.get_config("app_settings.tray_notification_shown", False):
                self.tray_icon.showMessage(
                    "Fire Vision Pro",
                    "Application was minimized to tray. Cameras and streaming continue running in background. Login required when reopened.",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.config_manager.update_config("app_settings.tray_notification_shown", True)
        else:
            self.showMinimized()

    def create_dashboard_main_grid(self, dashboard_layout):
        self.stacked_widget = QStackedWidget()
        self.cameras_page = self.create_cameras_page()
        self.stacked_widget.addWidget(self.cameras_page)
        self.recordings_page = RecordingsPage(self.google_drive_manager)
        self.recordings_page.back_to_cameras.connect(self.show_cameras_page)
        self.stacked_widget.addWidget(self.recordings_page)
        self.stacked_widget.addWidget(self.alerts_widget)
        self.stacked_widget.addWidget(self.user_management_widget)
        self.camera_manager_page = self.camera_location_manager
        self.stacked_widget.addWidget(self.camera_manager_page)
        self.stacked_widget.addWidget(self.voice_widget)
        # --- Map Overview Page ---
        self.map_overview_page = QWidget()
        # Use QHBoxLayout for sidebar + map
        map_layout = QHBoxLayout(self.map_overview_page)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)
        # Sidebar (created ONCE)
        self.map_filter_sidebar = QWidget()
        self.map_filter_sidebar.setFixedWidth(180)
        self.map_filter_sidebar.setStyleSheet("background-color: #181a20; border-right: 1px solid #30363d;")
        sidebar_layout = QVBoxLayout(self.map_filter_sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 10)
        sidebar_layout.setSpacing(8)
        label = QLabel("Filter by Common")
        label.setStyleSheet("color: #fff; font-size: 15px; font-weight: bold; margin-bottom: 8px;")
        sidebar_layout.addWidget(label)
        self._map_filter_btns = []
        self._map_filter_sidebar_layout = sidebar_layout
        map_layout.addWidget(self.map_filter_sidebar)
        # Map container (vertical layout for map + fire alert sidebox)
        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)
        self.map_view = QWebEngineView()
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        map_container_layout.addWidget(self.map_view)
        # Add fire alert sidebox (initially hidden)
        self.fire_alert_sidebox = QFrame(map_container)
        self.fire_alert_sidebox.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #ff3333;
                border-radius: 12px;
            }
        """)
        self.fire_alert_sidebox.setFixedWidth(320)
        self.fire_alert_sidebox.setVisible(False)
        sidebox_layout = QVBoxLayout(self.fire_alert_sidebox)
        sidebox_layout.setContentsMargins(18, 18, 18, 18)
        self.fire_alert_title = QLabel("🔥 Fire Detected!")
        self.fire_alert_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff3333;")
        self.fire_alert_caminfo = QLabel()
        self.fire_alert_caminfo.setStyleSheet("font-size: 14px; color: #222;")
        self.fire_alert_btn = QPushButton("View Fullscreen")
        self.fire_alert_btn.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold; font-size: 15px; border-radius: 8px; padding: 8px 0;")
        self.fire_alert_btn.clicked.connect(self._fire_alert_view_fullscreen)
        sidebox_layout.addWidget(self.fire_alert_title)
        sidebox_layout.addWidget(self.fire_alert_caminfo)
        sidebox_layout.addStretch()
        sidebox_layout.addWidget(self.fire_alert_btn)
        map_container_layout.addWidget(self.fire_alert_sidebox, alignment=Qt.AlignBottom | Qt.AlignRight)
        map_layout.addWidget(map_container, 1)
        self.stacked_widget.addWidget(self.map_overview_page)
        
        # --- Advanced Camera Management Page ---
        self.advanced_camera_page = AdvancedCameraManagementPage(self.camera_manager, self.config_manager)
        self.stacked_widget.addWidget(self.advanced_camera_page)
        
        # --- Settings Page ---
        self.stacked_widget.addWidget(self.settings_widget)
        
        dashboard_layout.addWidget(self.stacked_widget, 1)

    def _fire_alert_view_fullscreen(self):
        camera_id = getattr(self.fire_alert_btn, 'camera_id', None)
        if camera_id:
            self.show_fullscreen_camera(camera_id)
            self.fire_alert_sidebox.setVisible(False)

    def show_cameras_page(self):
        """Show cameras page"""
        self.stacked_widget.setCurrentWidget(self.cameras_page)
        self.set_active_nav_button(self.cameras_btn)

    def show_recordings_page(self):
        """Show recordings page"""
        self.stacked_widget.setCurrentWidget(self.recordings_page)
        self.set_active_nav_button(self.recordings_btn)

    def show_alerts_page(self):
        self.stacked_widget.setCurrentWidget(self.alerts_widget)
        self.set_active_nav_button(self.alerts_btn)

    # Removed show_cloud_backup_page

    def show_users_page(self):
        self.stacked_widget.setCurrentWidget(self.user_management_widget)
        self.set_active_nav_button(self.users_btn)

    def show_camera_manager_page(self):
        self.stacked_widget.setCurrentWidget(self.camera_location_manager)
        self.set_active_nav_button(self.camera_manager_btn)

    def show_map_overview_page(self, highlight_camera_id=None, common_filter=None):
        camera_locations = self.camera_location_manager.camera_locations
        # --- Extract unique 'common' values ---
        common_values = set()
        for loc in camera_locations.values():
            val = loc.get('common', '').strip()
            if val:
                common_values.add(val)
        common_values = sorted(common_values)
        # --- Sidebar filter UI ---
        # Only update filter buttons, never re-insert sidebar widget
        # Remove old filter buttons
        for btn in getattr(self, '_map_filter_btns', []):
            self._map_filter_sidebar_layout.removeWidget(btn)
            btn.deleteLater()
        self._map_filter_btns = []
        # Remove any old stretch/spacer at the end
        count = self._map_filter_sidebar_layout.count()
        if count > 0:
            last_item = self._map_filter_sidebar_layout.itemAt(count - 1)
            if last_item and last_item.spacerItem():
                self._map_filter_sidebar_layout.removeItem(last_item)
        # Add 'All' filter
        def filter_callback_factory(val):
            return lambda: self.show_map_overview_page(common_filter=val)
        all_btn = QPushButton("All")
        all_btn.setCheckable(True)
        all_btn.setChecked(common_filter is None)
        all_btn.setStyleSheet("""
            QPushButton { color: #fff; background: #232136; border-radius: 6px; padding: 7px 0; font-size: 14px; }
            QPushButton:checked { background: #ff3333; color: #fff; font-weight: bold; }
        """)
        all_btn.clicked.connect(filter_callback_factory(None))
        self._map_filter_sidebar_layout.addWidget(all_btn)
        self._map_filter_btns.append(all_btn)
        # Add buttons for each unique common value
        for val in common_values:
            btn = QPushButton(val)
            btn.setCheckable(True)
            btn.setChecked(common_filter == val)
            btn.setStyleSheet("""
                QPushButton { color: #fff; background: #232136; border-radius: 6px; padding: 7px 0; font-size: 14px; }
                QPushButton:checked { background: #ff3333; color: #fff; font-weight: bold; }
            """)
            btn.clicked.connect(filter_callback_factory(val))
            self._map_filter_sidebar_layout.addWidget(btn)
            self._map_filter_btns.append(btn)
        # Always add stretch at the end so buttons stay at the top
        self._map_filter_sidebar_layout.addStretch()
        # --- Filter camera_locations if needed ---
        filtered_locations = camera_locations
        if common_filter:
            filtered_locations = {cid: loc for cid, loc in camera_locations.items() if loc.get('common', '').strip() == common_filter}
        # Only regenerate map if locations or highlight or filter changed
        need_regen = (
            self._last_map_highlight != highlight_camera_id or
            self._last_map_camera_locations != filtered_locations or
            getattr(self, '_last_map_common_filter', None) != common_filter
        )
        if filtered_locations:
            import folium
            if need_regen:
                if highlight_camera_id and highlight_camera_id in filtered_locations:
                    center_lat = filtered_locations[highlight_camera_id]['latitude']
                    center_lng = filtered_locations[highlight_camera_id]['longitude']
                    zoom = 20
                else:
                    first_location = list(filtered_locations.values())[0]
                    center_lat = first_location['latitude']
                    center_lng = first_location['longitude']
                    zoom = 18
                m = folium.Map(
                    location=[center_lat, center_lng],
                    zoom_start=zoom,
                    tiles='OpenStreetMap'
                )
                for camera_id, location in filtered_locations.items():
                    popup_html = (
                        f"""
                        <b>📹 {location['camera_name']}</b><br>
                        <b>ID:</b> {camera_id}<br>
                        <b>Location:</b> {location.get('description', 'No description')}<br>
                        <b>Common:</b> {location.get('common', '')}<br>
                        <b>Coordinates:</b> {location['latitude']:.6f}, {location['longitude']:.6f}<br>
                        <button onclick=\"if(window.bridge){{window.bridge.pinClicked('{camera_id}');}}else if(window.qt && window.qt.webChannelTransport){{new QWebChannel(qt.webChannelTransport,function(channel){{channel.objects.bridge.pinClicked('{camera_id}');}});}}\">Go to Fullscreen</button>
                        """
                    )
                    folium.Marker(
                        location=[location['latitude'], location['longitude']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=location['camera_name'],
                        icon=folium.Icon(
                            color='red' if highlight_camera_id and camera_id == highlight_camera_id else 'blue',
                            icon='fire' if highlight_camera_id and camera_id == highlight_camera_id else 'video-camera',
                            prefix='fa'
                        )
                    ).add_to(m)
                import tempfile, os
                from PyQt5.QtCore import QUrl
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                m.save(temp_file.name)
                # Inject QWebChannel JS if not present
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    html = f.read()
                if 'qwebchannel.js' not in html:
                    # Insert QWebChannel script before </head>
                    qwebchannel_js = '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
                    html = html.replace('</head>', qwebchannel_js + '\n</head>')
                    with open(temp_file.name, 'w', encoding='utf-8') as f:
                        f.write(html)
                self._last_map_tempfile = temp_file.name
                self.map_view.load(QUrl.fromLocalFile(os.path.abspath(temp_file.name)))
                self._last_map_highlight = highlight_camera_id
                self._last_map_camera_locations = filtered_locations.copy()
                self._last_map_common_filter = common_filter
            elif self._last_map_tempfile:
                from PyQt5.QtCore import QUrl
                import os
                self.map_view.load(QUrl.fromLocalFile(os.path.abspath(self._last_map_tempfile)))
            # Always update the sidebox info
            if highlight_camera_id and highlight_camera_id in filtered_locations:
                cam = filtered_locations[highlight_camera_id]
                self.fire_alert_caminfo.setText(
                    f"<b>{cam['camera_name']}</b><br>{cam.get('description', '')}<br>Lat: {cam['latitude']:.6f}, Lng: {cam['longitude']:.6f}"
                )
                self.fire_alert_btn.camera_id = highlight_camera_id
                self.fire_alert_sidebox.setVisible(True)
            else:
                self.fire_alert_sidebox.setVisible(False)
        else:
            html = "<h2 style='color:#bfc9e0;text-align:center;margin-top:40px;'>No camera locations found.</h2>"
            self.map_view.setHtml(html)
            self.fire_alert_sidebox.setVisible(False)

        self.stacked_widget.setCurrentWidget(self.map_overview_page)
        self.set_active_nav_button(self.map_overview_btn)

    def update_nav_buttons(self):
        """Update navigation button styles"""
        for btn in [self.cameras_btn, self.recordings_btn, self.alerts_btn, self.users_btn, self.camera_manager_btn, self.map_overview_btn, self.settings_btn]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def reset_all_nav_buttons(self):
        """Reset all navigation buttons to default state"""
        all_buttons = [
            self.cameras_btn, self.recordings_btn, 
            self.alerts_btn, self.users_btn, 
            self.camera_manager_btn, self.map_overview_btn, 
            self.settings_btn
        ]
        for btn in all_buttons:
            btn.setObjectName("navButton")
            # Apply inactive styling
            btn.setStyleSheet("""
                QPushButton#navButton {
                    background-color: transparent;
                    border-radius: 30px;
                    border: none;
                }
                QPushButton#navButton:hover {
                    background-color: #1B3F58;
                }
            """)
        self.update_nav_buttons()

    def set_active_nav_button(self, active_button):
        """Set a specific button as active and reset all others"""
        self.reset_all_nav_buttons()
        active_button.setObjectName("activeNavButton")
        # Apply active styling with left border
        active_button.setStyleSheet("""
            QPushButton#activeNavButton {
                background-color: #1e3a5f;
                border-radius: 10px;
                border: none;
                border-left: 3px solid #4a90e2;
            }
            QPushButton#activeNavButton:hover {
                background-color: #2a4a6f;
            }
        """)
        self.update_nav_buttons()

    def create_cameras_page(self):
        """Create the cameras page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QWidget()
        header_layout = QHBoxLayout(header)

        title = QLabel("Cameras with AI People & Fire/Smoke Detection")
        title.setObjectName("titleLabel")

        self.status_indicator = QLabel("🟢 Service Running")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 12px;
                font-weight: bold;
                background-color: rgba(0, 255, 0, 20);
                padding: 5px 10px;
                border-radius: 4px;
                border: 1px solid #00ff00;
            }
        """)

        add_camera_btn = QPushButton("➕ Add Camera")
        add_camera_btn.setObjectName("addButton")
        add_camera_btn.clicked.connect(self.show_add_camera_dialog)

        # Add Delete Cameras button
        delete_cameras_btn = QPushButton("🗑️ Delete Cameras")
        delete_cameras_btn.setObjectName("addButton")
        delete_cameras_btn.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold;")
        delete_cameras_btn.clicked.connect(self.show_delete_cameras_dialog)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_camera_btn)
        header_layout.addWidget(delete_cameras_btn)

        layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.camera_grid = QGridLayout()
        self.camera_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.camera_grid.setSpacing(15)
        camera_container = QWidget()
        camera_container.setLayout(self.camera_grid)

        scroll_area.setWidget(camera_container)
        layout.addWidget(scroll_area, 1)

        self.load_saved_cameras()

        return page

    # Removed service page creation and management methods

    def connect_signals(self):
        """Connect UI signals"""
        self.camera_manager.frame_ready.connect(self.on_frame_ready)
        self.camera_manager.detection_frame_ready.connect(self.on_detection_frame_ready)
        self.camera_manager.fire_smoke_frame_ready.connect(self.on_fire_smoke_frame_ready)
        self.camera_manager.camera_error.connect(self.on_camera_error)
        self.camera_manager.fire_smoke_alert.connect(self.on_fire_smoke_alert)
        self.camera_manager.camera_tested.connect(self.on_camera_tested)  # Background testing result

        self.stream_manager.stream_started.connect(self.on_stream_started)
        self.stream_manager.stream_stopped.connect(self.on_stream_stopped)
        self.stream_manager.stream_error.connect(self.on_stream_error)
        
        # Connect fire detection backend signals
        self.fire_detection_backend.alert_created.connect(self.on_fire_alert_created)
        self.fire_detection_backend.alert_updated.connect(self.on_fire_alert_updated)
        self.fire_detection_backend.backend_error.connect(self.on_backend_error)

    def show_login_screen(self):
        """Show the modern login dialog and require successful authentication"""
        while True:
            login_dialog = ModernLoginDialog(self)
            result = login_dialog.exec_()
            if result == QDialog.Accepted:
                username = login_dialog.get_username()
                if not username:
                    continue
                
                # Show loading screen immediately after login success
                # This prevents the UI from freezing/showing a blank screen
                loading_screen = LoadingScreen()
                loading_screen.show_with_fade()
                QApplication.processEvents()
                
                loading_screen.update_status("Authenticating...", 10)
                QApplication.processEvents()

                # Set current user context for isolation
                self.config_manager.set_current_user(username)
                
                loading_screen.update_status("Loading user profile...", 20)
                QApplication.processEvents()

                # Update UI
                self.user_label.setText(username)
                
                # Reload cameras for this user
                self.camera_widgets.clear()
                self.fullscreen_widgets.clear()
                
                # Pass loading screen to load_saved_cameras for progress updates
                self.load_saved_cameras(loading_screen)
                
                # User context set
                self.config_manager.set_current_user(username)
                
                loading_screen.update_status("Finalizing setup...", 90)
                QApplication.processEvents()
                
                loading_screen.complete_loading()
                QApplication.processEvents()
                
                # Allow fade out animation - yielded loop for smoothness
                start_time = time.time()
                while time.time() - start_time < 0.6:  # Slightly longer to ensure full fade
                    QApplication.processEvents()
                    time.sleep(0.01)  # Faster polling for better smoothness
                
                break
            else:
                reply = QMessageBox.question(
                    self,
                    'Exit Application',
                    'You must log in to continue. Exit the application?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    QApplication.quit()
                    return

    # Removed update_status_indicator

    def logout(self):
        """Logout current user"""
        reply = QMessageBox.question(
            self, 'Logout',
            'Logout will hide the interface but cameras and streaming will continue running in background. Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            clear_reply = QMessageBox.question(
                self, 'Clear Saved Login',
                'Do you want to clear saved login details?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if clear_reply == QMessageBox.Yes:
                self.config_manager.save_login_details("", False)
            self.config_manager.set_current_user(None)
            # Clear UI camera widgets
            for widget in list(self.camera_widgets.values()):
                widget.setParent(None)
            self.camera_widgets.clear()
            for widget in list(self.fullscreen_widgets.values()):
                widget.setParent(None)
            self.fullscreen_widgets.clear()
            self.update_camera_grid()
            # Require login again
            self.show_login_screen()

    def show_add_camera_dialog(self):
        """Show the add camera dialog"""
        dialog = AddCameraDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            camera_data = dialog.get_camera_data()
            if camera_data:
                # Persist camera to backend
                try:
                    # Map frontend keys to backend keys if needed, but config_manager.add_camera handles it
                    # (it expects id, dict with name, source, type)
                    backend_camera = self.config_manager.add_camera(camera_data['id'], camera_data)
                    
                    if backend_camera:
                        print(f"✅ Camera persisted to backend: {backend_camera}")
                        # Update ID if backend assigned a different one (e.g. integer ID vs UUID)
                        if 'id' in backend_camera:
                            camera_data['id'] = str(backend_camera['id'])
                            
                    self.add_camera(camera_data)
                    
                except Exception as e:
                    print(f"⚠️ Failed to persist camera to backend: {e}")
                    QMessageBox.warning(self, "Warning", f"Camera added locally but failed to save to backend: {e}")
                    self.add_camera(camera_data)
    
    def show_fullscreen_camera(self, camera_id):
        """Show camera in fullscreen mode"""
        if camera_id not in self.fullscreen_widgets:
            camera_name = "Unknown Camera"
            camera_config = self.config_manager.get_camera(camera_id)
            if camera_config:
                camera_name = camera_config["name"]
            
            if camera_config:
                camera_name = camera_config["name"]
            
            fullscreen_widget = EnhancedFullScreenCameraWidget(
                camera_id, 
                camera_name, 
                self.clip_manager, 
                self.fire_detection_backend, 
                self.notification_manager,
                settings_manager=self.settings_manager
            )
            fullscreen_widget.set_detection_systems(
                people_detector=self.camera_manager.people_detector,
                fire_smoke_detector=self.camera_manager.fire_smoke_detector,
                camera_manager=self.camera_manager
            )
            fullscreen_widget.back_clicked.connect(self.return_to_grid)
            self.fullscreen_widgets[camera_id] = fullscreen_widget
            self.stacked_widget.addWidget(fullscreen_widget)
        
        self.stacked_widget.setCurrentWidget(self.fullscreen_widgets[camera_id])
        self.sidebar.hide()
    
    def return_to_grid(self):
        """Return to camera grid view"""
        self.stacked_widget.setCurrentWidget(self.cameras_page)
        self.sidebar.show()

    def add_camera(self, camera_data):
        try:
            print(f"🎬 Adding camera: {camera_data}")

            # Add skeleton widget immediately
            skeleton = SkeletonCameraWidget()
            self.camera_widgets[camera_data['id']] = skeleton
            self.update_camera_grid()

            # Start background thread to load camera
            loader_thread = CameraLoaderThread(camera_data, self.camera_manager)
            loader_thread.camera_loaded.connect(self.on_camera_loaded)
            loader_thread.camera_failed.connect(self.on_camera_failed)
            loader_thread.start()
            # Keep a reference to prevent garbage collection
            if not hasattr(self, '_camera_loader_threads'):
                self._camera_loader_threads = []
            self._camera_loader_threads.append(loader_thread)

        except Exception as e:
            print(f"❌ Error adding camera: {e}")
            QMessageBox.critical(self, "Error", f"Error adding camera: {str(e)}")
        
        # ✅ UPDATE ALERTS WIDGET CAMERA LIST
        try:
            cameras = self.config_manager.load_cameras()
            camera_list = [(camera_id, camera_data['name']) for camera_id, camera_data in cameras.items()]
            if hasattr(self, 'alerts_widget'):
                self.alerts_widget.set_camera_list(camera_list)
        except Exception as e:
            print(f"❌ Error updating alerts widget camera list: {e}")

    def on_camera_loaded(self, camera_data):
        # Replace skeleton with real camera widget
        camera_widget = EnhancedCameraWidget(camera_data['id'], camera_data['name'])
        self.camera_widgets[camera_data['id']] = camera_widget
        camera_widget.clicked.connect(self.show_fullscreen_camera)
        camera_widget.delete_clicked.connect(self.delete_camera)
        self.update_camera_grid()
        QMessageBox.information(self, "Success", f"Camera '{camera_data['name']}' added successfully!")

    def on_camera_failed(self, camera_id, error_message):
        # Remove skeleton
        if camera_id in self.camera_widgets:
            widget = self.camera_widgets[camera_id]
            self.camera_grid.removeWidget(widget)
            widget.setParent(None)
            del self.camera_widgets[camera_id]
        self.update_camera_grid()
        QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {error_message}")

    def delete_camera(self, camera_id):
        """Delete a camera"""
        try:
            camera_name = "Unknown Camera"
            if camera_id in self.camera_widgets:
                camera_name = self.camera_widgets[camera_id].camera_name
            
            reply = QMessageBox.question(
                self, 'Delete Camera',
                f'Are you sure you want to delete camera "{camera_name}"?\n\nThis will stop the camera and remove it from the system.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                print(f"🗑️ Deleting camera: {camera_id}")
                
                self.camera_manager.stop_camera(camera_id)
                self.camera_manager.remove_camera(camera_id)
                
                self.config_manager.remove_camera(camera_id)
                
                if camera_id in self.camera_widgets:
                    widget = self.camera_widgets[camera_id]
                    self.camera_grid.removeWidget(widget)
                    widget.setParent(None)
                    del self.camera_widgets[camera_id]
                
                if camera_id in self.fullscreen_widgets:
                    widget = self.fullscreen_widgets[camera_id]
                    self.stacked_widget.removeWidget(widget)
                    widget.setParent(None)
                    del self.fullscreen_widgets[camera_id]
                
                self.update_camera_grid()
                
                QMessageBox.information(self, "Success", 
                    f'Camera "{camera_name}" deleted successfully!')

        except Exception as e:
            print(f"❌ Error deleting camera: {e}")
            QMessageBox.critical(self, "Error", f"Error deleting camera: {str(e)}")

    def load_saved_cameras(self, loading_screen=None):
        """Load cameras from persistent storage"""
        print("🔄 Loading saved cameras...")
        
        if loading_screen:
            loading_screen.update_status("Reading camera configuration...", 35)
            QApplication.processEvents()
        
        # This API call can take time, yield before it
        QApplication.processEvents()
        cameras = self.config_manager.load_cameras()
        QApplication.processEvents()
        
        total_cameras = len(cameras)
        
        for i, (camera_id, camera_data) in enumerate(cameras.items()):
            try:
                print(f"🎥 Loading camera: {camera_data['name']}")
                
                if loading_screen:
                    progress = 35 + int((i / total_cameras) * 40)  # 35% to 75%
                    loading_screen.update_status(f"Loading camera: {camera_data['name']}...", progress)
                    QApplication.processEvents()
                
                # Add camera to manager without testing (skip_test=True for instant loading)
                # This allows the dashboard to appear immediately
                self.camera_manager.add_camera(
                    camera_id,
                    camera_data['name'],
                    camera_data['source'],
                    camera_data['type'],
                    skip_test=True  # Skip synchronous testing
                )
                
                # Create camera widget
                camera_widget = EnhancedCameraWidget(camera_id, camera_data['name'])
                self.camera_widgets[camera_id] = camera_widget
                camera_widget.clicked.connect(self.show_fullscreen_camera)
                camera_widget.delete_clicked.connect(self.delete_camera)
                
                # Set initial status to "testing"
                camera_widget.set_status("Testing...")
                
                # Enable fire/smoke detection if configured
                if camera_data.get("detection_enabled", False):
                    camera_widget.set_detection_enabled(True)
                    # Actually enable fire detection on the camera manager
                    self.camera_manager.enable_fire_smoke_detection(camera_id, True)
                    print(f"🔥 Fire detection enabled for camera {camera_id}")
                
                # Start background testing for this camera
                self.camera_manager.test_camera_async(camera_id)
                
            except Exception as e:
                print(f"❌ Error loading camera {camera_data.get('name', camera_id)}: {e}")

        self.update_camera_grid()
        
        if loading_screen:
            loading_screen.update_status("Populating dashboard...", 75)
            QApplication.processEvents()
        
        # ✅ UPDATE ALERTS WIDGET WITH CAMERA LIST
        try:
            camera_list = [(camera_id, camera_data['name']) for camera_id, camera_data in cameras.items()]
            if hasattr(self, 'alerts_widget'):
                self.alerts_widget.set_camera_list(camera_list)
                print(f"✅ Updated alerts widget with {len(camera_list)} cameras")
        except Exception as e:
            print(f"❌ Error updating alerts widget camera list: {e}")
        
        print(f"✅ Loaded {len(cameras)} cameras from configuration (testing in background)")

    def update_camera_grid(self):
        """Update the camera grid layout"""
        for i in reversed(range(self.camera_grid.count())):
            self.camera_grid.itemAt(i).widget().setParent(None)

        cameras = list(self.camera_widgets.values())
        cols = 2

        for i, widget in enumerate(cameras):
            row = i // cols
            col = i % cols
            self.camera_grid.addWidget(widget, row, col)

    def on_frame_ready(self, camera_id, frame):
        """Handle new frame from camera"""
        if camera_id in self.camera_widgets:
            self.camera_widgets[camera_id].update_frame(frame)

        if camera_id in self.fullscreen_widgets:
            self.fullscreen_widgets[camera_id].update_frame(frame)

    def on_detection_frame_ready(self, camera_id, annotated_frame, detections, people_count):
        """Handle people detection results"""
        if camera_id in self.camera_widgets:
            self.camera_widgets[camera_id].update_detection_frame(annotated_frame, detections, people_count)

        if camera_id in self.fullscreen_widgets:
            self.fullscreen_widgets[camera_id].update_people_detection_frame(annotated_frame, detections, people_count)
        
        # ✅ CREATE ALERT FOR PEOPLE DETECTION (if people detected)
        if people_count > 0 and detections:
            try:
                camera_name = "Unknown Camera"
                if camera_id in self.camera_widgets:
                    camera_name = self.camera_widgets[camera_id].camera_name
                
                # Calculate confidence from detections
                max_confidence = 0.0
                for detection in detections:
                    if hasattr(detection, 'confidence'):
                        max_confidence = max(max_confidence, detection.confidence)
                    elif isinstance(detection, dict) and 'confidence' in detection:
                        max_confidence = max(max_confidence, detection['confidence'])
                
                # Only create alert if confidence is reasonable and we haven't created one recently
                if max_confidence > 0.5:
                    # Check if we already have a recent people alert for this camera (within last 5 minutes)
                    recent_alerts = self.alerts_manager.get_alerts(
                        camera_id=camera_id,
                        alert_type='people',
                        limit=5
                    )
                    
                    # Check if there's a recent alert (within 5 minutes)
                    current_time = time.time()
                    has_recent_alert = False
                    for alert in recent_alerts:
                        if current_time - alert.timestamp < 300:  # 5 minutes
                            has_recent_alert = True
                            break
                    
                    if not has_recent_alert:
                        # Determine severity based on people count and confidence
                        if people_count >= 3 or max_confidence > 0.9:
                            severity = "high"
                        elif people_count >= 2 or max_confidence > 0.7:
                            severity = "medium"
                        else:
                            severity = "low"
                        
                        # Create alert
                        alert_id = self.alerts_manager.create_alert(
                            camera_id=camera_id,
                            camera_name=camera_name,
                            alert_type="people",
                            severity=severity,
                            confidence=max_confidence,
                            description=f"{people_count} person(s) detected with {max_confidence:.1%} confidence",
                            metadata={
                                'detection_time': datetime.datetime.now().isoformat(),
                                'people_count': people_count,
                                'camera_location': camera_name,
                                'alert_source': 'ai_detection'
                            }
                        )
                        print(f"👥 People detection alert created: {alert_id}")
                        
            except Exception as e:
                print(f"❌ Error creating people detection alert: {e}")

    def on_fire_smoke_frame_ready(self, camera_id, annotated_frame, detections, alert_info):
        """Handle fire/smoke detection results"""
        if camera_id in self.camera_widgets:
            self.camera_widgets[camera_id].update_fire_smoke_frame(annotated_frame, detections, alert_info)

        if camera_id in self.fullscreen_widgets:
            self.fullscreen_widgets[camera_id].update_fire_smoke_detection_frame(annotated_frame, detections, alert_info)

    def on_fire_smoke_alert(self, camera_id, alert_type, confidence):
        """Handle fire/smoke alert"""
        camera_name = "Unknown Camera"
        if camera_id in self.camera_widgets:
            camera_name = self.camera_widgets[camera_id].camera_name
        event = {
            "type": alert_type.capitalize(),
            "status": "Critical",
            "desc": f"{alert_type.capitalize()} detected on {camera_name}",
            "time": datetime.datetime.now().strftime("%d-%b-%Y %I:%M%p"),
            "location": camera_name,
            "img": resource_path("assests/foc1.jpg"),
            "camera_id": camera_id
        }
        
        # ✅ CREATE ALERT IN ALERTS MANAGER
        try:
            # Determine severity based on confidence
            if confidence >= 0.9:
                severity = "critical"
            elif confidence >= 0.7:
                severity = "high"
            elif confidence >= 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert in alerts manager
            alert_id = self.alerts_manager.create_alert(
                camera_id=camera_id,
                camera_name=camera_name,
                alert_type=alert_type.lower(),
                severity=severity,
                confidence=confidence,
                description=f"{alert_type.capitalize()} detected with {confidence:.1%} confidence",
                metadata={
                    'detection_time': datetime.datetime.now().isoformat(),
                    'camera_location': camera_name,
                    'alert_source': 'ai_detection'
                }
            )
            print(f"🚨 Alert created in alerts manager: {alert_id}")
        except Exception as e:
            print(f"❌ Error creating alert: {e}")
        
        # ✅ START AUTO-RECORDING OF EVENT CLIP
        if hasattr(self, 'clip_manager') and self.clip_manager:
            try:
                # Start event recording
                clip_id = self.clip_manager.start_event_recording(
                    camera_id=camera_id,
                    camera_name=camera_name,
                    event_type=alert_type,
                    trigger_data={
                        'confidence': confidence,
                        'severity': 'high' if confidence > 0.8 else 'medium'
                    }
                )
                print(f"🎬 Auto-recording started for fire event: {clip_id}")
                
                # Connect frame signals to recording
                # This will feed frames to the clip manager for the next 15 seconds
                def add_frame_handler(cam_id, frame):
                    if cam_id == camera_id:
                        self.clip_manager.add_frame_to_recording(cam_id, frame)
                
                # Store handler reference to disconnect later
                if not hasattr(self, '_clip_frame_handlers'):
                    self._clip_frame_handlers = {}
                self._clip_frame_handlers[camera_id] = add_frame_handler
                
                # Connect to fire_smoke_frame_ready to get annotated frames
                self.camera_manager.fire_smoke_frame_ready.connect(
                    lambda cam_id, frame, dets, info: add_frame_handler(cam_id, frame)
                )
                
                # Auto-disconnect after 15 seconds (clip duration)
                QTimer.singleShot(15000, lambda: self._disconnect_clip_handler(camera_id))
                
            except Exception as e:
                print(f"❌ Error starting event recording: {e}")
        
        # <CHANGE> Check if camera is in fullscreen mode before navigating to map
        current_widget = self.stacked_widget.currentWidget()
        is_fullscreen_active = False
        fullscreen_widget = None
        
        # Check if current widget is a fullscreen widget for this camera
        if camera_id in self.fullscreen_widgets:
            fullscreen_widget = self.fullscreen_widgets[camera_id]
            if current_widget == fullscreen_widget:
                is_fullscreen_active = True
        
        if is_fullscreen_active and fullscreen_widget:
            # <CHANGE> If in fullscreen mode, activate fire detection side panel instead of navigating
            print(f"🔥 Fire detected in fullscreen mode - activating side panel for camera {camera_id}")
            
            # Get the latest fire detection frames from the detector
            if hasattr(self.camera_manager, 'fire_smoke_detector'):
                detector = self.camera_manager.fire_smoke_detector
                if camera_id in detector.last_detections:
                    frame, detections, alert_info = detector.last_detections[camera_id]
                    
                    # Prepare frame data for side panel
                    frames_with_detections = [{
                        'frame': frame,
                        'detections': detections,
                        'alert_info': alert_info,
                        'timestamp': datetime.datetime.now()
                    }]
                    
                    # Activate fire detection mode in side panel
                    fullscreen_widget.fire_detection_widget.activate_fire_detection_mode(
                        frames_with_detections, 
                        alert_id=f"alert_{camera_id}_{int(datetime.datetime.now().timestamp())}"
                    )
                    
                    # Switch to fire detection tab in side panel
                    fullscreen_widget.side_tabs.setCurrentWidget(fullscreen_widget.fire_detection_widget)
                    
                    # Ensure the window is focused
                    self.show()
                    self.raise_()
                    self.activateWindow()
                    
                    print(f"✅ Fire detection side panel activated for camera {camera_id}")
                else:
                    print(f"⚠️ No detection data available for camera {camera_id}")
            else:
                print(f"⚠️ Fire/smoke detector not available")
        else:
            # <CHANGE> If not in fullscreen mode, use original behavior (show map alert page)
            print(f"🔥 Fire detected - showing map overview for camera {camera_id}")
            self.show_map_overview_page(highlight_camera_id=camera_id)
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _disconnect_clip_handler(self, camera_id):
        """Disconnect clip recording handler after recording is complete"""
        if hasattr(self, '_clip_frame_handlers') and camera_id in self._clip_frame_handlers:
            # Handler will be garbage collected
            del self._clip_frame_handlers[camera_id]
            print(f"✅ Event recording completed for camera {camera_id}")

    def send_fire_alert_to_backend(self, camera_id, camera_name, alert_type, confidence):
        """Send fire detection alert to backend server and mobile app"""
        try:
            if hasattr(self.camera_manager, 'fire_smoke_detector'):
                detector = self.camera_manager.fire_smoke_detector
                if camera_id in detector.last_detections:
                    frame, detections, alert_info = detector.last_detections[camera_id]
                    
                    # Use comprehensive notification manager to send to both backend and mobile
                    results = self.notification_manager.send_comprehensive_fire_alert(
                        camera_id=camera_id,
                        camera_name=camera_name,
                        frame=frame,
                        detections=detections,
                        alert_info=alert_info
                    )
                    
                    # Log results
                    backend_status = "✅" if results['backend'] else "❌"
                    mobile_status = "✅" if results['mobile'] else "❌"
                    print(f"🔥 Fire alert notification results:")
                    print(f"   Backend: {backend_status}")
                    print(f"   Mobile App: {mobile_status}")
                    
                    # Also send to original backend for compatibility
                    alert_id = self.fire_detection_backend.create_fire_alert(
                        camera_id=camera_id,
                        camera_name=camera_name,
                        frame=frame,
                        detections=detections,
                        alert_info=alert_info
                    )
                    
                    if alert_id:
                        print(f"✅ Fire alert sent to backend: {alert_id}")
                    else:
                        print(f"❌ Failed to send fire alert to backend")
                else:
                    print(f"⚠️ No detection data available for camera {camera_id}")
            else:
                print(f"⚠️ Fire/smoke detector not available")
                
        except Exception as e:
            print(f"❌ Error sending fire alert: {e}")

    def on_fire_alert_created(self, alert_id, status):
        """Handle fire alert creation success"""
        print(f"✅ Fire alert created on backend: {alert_id} (status: {status})")
        event = {
            "type": "Fire Alert",
            "status": status.capitalize(),
            "desc": f"Backend fire alert created: {alert_id}",
            "time": datetime.datetime.now().strftime("%d-%b-%Y %I:%M%p"),
            "location": "Backend",
            "img": resource_path("assests/foc1.jpg"),
            "camera_id": ""
        }
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Fire Alert Created",
                f"Fire detection alert {alert_id} has been sent to the backend server.",
                QSystemTrayIcon.Information,
                5000
            )

    def on_fire_alert_updated(self, alert_id, new_status):
        """Handle fire alert update success"""
        print(f"✅ Fire alert updated on backend: {alert_id} (new status: {new_status})")
        
        if new_status == 'dispatched':
            message = f"Emergency services have been dispatched for alert {alert_id}"
            icon = QSystemTrayIcon.Warning
        elif new_status == 'false_alarm':
            message = f"Alert {alert_id} has been marked as false alarm"
            icon = QSystemTrayIcon.Information
        elif new_status == 'resolved':
            message = f"Alert {alert_id} has been resolved"
            icon = QSystemTrayIcon.Information
        else:
            message = f"Alert {alert_id} status updated to {new_status}"
            icon = QSystemTrayIcon.Information
        
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Fire Alert Updated",
                message,
                icon,
                5000
            )

    def on_backend_error(self, error_message):
        """Handle backend communication errors"""
        print(f"❌ Backend error: {error_message}")
        
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Backend Error",
                f"Communication error with backend server: {error_message}",
                QSystemTrayIcon.Warning,
                8000
            )

    def on_camera_error(self, camera_id, error):
        """Handle camera error"""
        print(f"❌ Camera {camera_id} error: {error}")
        if camera_id in self.camera_widgets:
            self.camera_widgets[camera_id].setText(f"Camera Error:\n{error}")
    
    def on_camera_tested(self, camera_id, success, message):
        """Handle camera test completion"""
        print(f"{'✅' if success else '❌'} Camera test result for {camera_id}: {message}")
        
        if camera_id in self.camera_widgets:
            if success:
                self.camera_widgets[camera_id].set_status("Ready")
            else:
                self.camera_widgets[camera_id].set_status(f"Error: {message}")

    def on_stream_started(self, camera_id):
        """Handle stream started"""
        print(f"🚀 Stream started for camera {camera_id}")

    def on_stream_stopped(self, camera_id):
        """Handle stream stopped"""
        print(f"🛑 Stream stopped for camera {camera_id}")

    def on_stream_error(self, camera_id, error):
        """Handle stream error"""
        print(f"❌ Stream error for camera {camera_id}: {error}")

    def closeEvent(self, event):
        """Handle application close"""
        if self.tray_icon and self.tray_icon.isVisible():
            # Stop all cameras and clear connections when closing (non-blocking)
            self.fast_stop_all_cameras()
            
            self.hide()
            if not self.config_manager.get_config("app_settings.close_notification_shown", False):
                self.tray_icon.showMessage(
                    "Fire Vision Pro",
                    "Application minimized to tray. All cameras stopped. Login required when reopened.",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.config_manager.update_config("app_settings.close_notification_shown", True)
            event.ignore()
        else:
            # Skip confirmation dialog and just close immediately
            print("🛑 Fast shutdown initiated...")
            self.fast_stop_all_cameras()
            
            # Force quit without waiting
            QTimer.singleShot(100, lambda: QApplication.quit())
            event.accept()
    
    def fast_stop_all_cameras(self):
        """Fast, non-blocking camera shutdown"""
        try:
            print("⚡ Fast stopping all cameras...")
            
            # Signal all threads to stop (non-blocking)
            for camera_id in list(self.camera_widgets.keys()):
                try:
                    # Just signal stop, don't wait
                    if camera_id in self.camera_manager.capture_threads:
                        thread = self.camera_manager.capture_threads[camera_id]
                        thread.stop()  # Signal to stop
                        # Don't wait - let it finish in background
                    
                    # Stop detection threads
                    if hasattr(self.camera_manager, 'people_detector'):
                        if camera_id in self.camera_manager.people_detector.detection_threads:
                            det_thread = self.camera_manager.people_detector.detection_threads[camera_id]
                            det_thread.stop()
                    
                    if hasattr(self.camera_manager, 'fire_smoke_detector'):
                        if camera_id in self.camera_manager.fire_smoke_detector.detection_threads:
                            fire_thread = self.camera_manager.fire_smoke_detector.detection_threads[camera_id]
                            fire_thread.stop()
                    
                except Exception as e:
                    print(f"⚠️ Error signaling stop for camera {camera_id}: {e}")
            
            # Clear UI immediately (don't wait for threads)
            for widget in list(self.camera_widgets.values()):
                widget.setParent(None)
            self.camera_widgets.clear()
            
            for widget in list(self.fullscreen_widgets.values()):
                widget.setParent(None)
            self.fullscreen_widgets.clear()
            
            print("✅ Fast shutdown complete (threads stopping in background)")
            
        except Exception as e:
            print(f"❌ Error in fast shutdown: {e}")

    def show_delete_cameras_dialog(self):
        dialog = DeleteCamerasDialog(self.camera_widgets, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_ids = dialog.get_selected_ids()
            if not selected_ids:
                QMessageBox.information(self, "No Selection", "No cameras selected for deletion.")
                return
            for camera_id in selected_ids:
                self.delete_camera(camera_id)

    def test_backend_connection(self):
        """Test backend connection silently"""
        if not self.fire_detection_backend.test_connection():
            print("⚠️ Backend connection failed - Fire detection alerts may not be sent to the server.")
        else:
            print("✅ Backend connection test successful")
    
    def test_mobile_connection(self):
        """Test mobile app connection"""
        try:
            success = self.notification_manager.test_mobile_connection()
            if success:
                print("✅ Mobile app connection test successful")
            else:
                print("❌ Mobile app connection test failed")
        except Exception as e:
            print(f"❌ Mobile app connection test error: {e}")
    
    def test_all_connections(self):
        """Test all connections (backend and mobile app)"""
        print("🔗 Testing all connections...")
        self.test_backend_connection()
        self.test_mobile_connection()

    def start_camera_testing_in_background(self):
        QTimer.singleShot(100, self.test_all_cameras)

    def test_all_cameras(self):
        print("Testing all cameras in the background...")
        pass

    def show_device_settings_page(self):
        self.stacked_widget.setCurrentWidget(self.device_settings_page)
        self.set_active_nav_button(self.device_settings_btn)


    def show_advanced_camera_page(self):
        self.stacked_widget.setCurrentWidget(self.advanced_camera_page)
        self.set_active_nav_button(self.advanced_camera_btn)

    def show_voice_commands_page(self):
        self.stacked_widget.setCurrentWidget(self.voice_widget)
        self.set_active_nav_button(self.voice_commands_btn)

    def show_settings_page(self):
        self.stacked_widget.setCurrentWidget(self.settings_widget)
        self.set_active_nav_button(self.settings_btn)



class ClickableEventCard(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.camera_id = event.get("camera_id", "Unknown")
        self.setMaximumWidth(300)

        self.setStyleSheet("""
            QWidget {
                background-color:rgb(2, 2, 3);
                border: 2px solid #f44336;
                border-radius: 10px;
            }
            QWidget:hover {
                background-color: #1b1e36;
                border: 2px solid #4f8cff;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        date = event.get("date", "12/07/2025")
        time = event.get("time", "12:40")
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        date_label = QLabel(f"📅 {date}")
        date_label.setStyleSheet("color: #bfc9e0; font-size: 11px;")
        top_layout.addWidget(date_label)
        main_layout.addLayout(top_layout)

        type_text = event.get("type", "Fire Alert")
        type_label = QLabel(f"{type_text}")
        type_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
        """)
        main_layout.addWidget(type_label)

        cam_label = QLabel(f"Camera {event.get('camera_no', '1')}")
        cam_label.setStyleSheet("color: #9aa4c8; font-size: 12px;")
        time_label = QLabel(f"Time: {time}")
        time_label.setStyleSheet("color: #9aa4c8; font-size: 12px;")
        main_layout.addWidget(cam_label)
        main_layout.addWidget(time_label)

        location_info = event.get("location", "Location: Department")
        loc_label = QLabel(location_info)
        loc_label.setStyleSheet("color: #9aa4c8; font-size: 12px;")
        main_layout.addWidget(loc_label)

        icon_row = QHBoxLayout()
        icon_row.addStretch()
        for icon in ["⚠️", "✅", "🔁"]:
            btn = QLabel(icon)
            btn.setStyleSheet("font-size: 18px;")
            icon_row.addWidget(btn)
        main_layout.addLayout(icon_row)

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.camera_id:
            self.clicked.emit(self.camera_id)
        super().mousePressEvent(event)


def main():
    """Main function with splash screen integration"""
    app = QApplication(sys.argv)

    app.setApplicationName("Fire Vision Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("FOC Security")
    
    app.setQuitOnLastWindowClosed(False)

    # Show initial splash screen
    splash = SplashScreen()
    splash.show_with_progress()
    app.processEvents()
    
    # Initialize main window (now moves heavy tasks to background)
    window = PersistentMainWindow()
    
    # Define what happens when initialization is finished
    def on_initialization_finished():
        print("💡 Initialization finished, transitioning to login...")
        splash.finish(window)
        window.show_login_screen()
        window.show()

    # Link splash to background initialization progress
    if hasattr(window, 'init_worker'):
        # Stop the simulated timer and use real progress
        if hasattr(splash, 'timer'):
            splash.timer.stop()
            
        def update_splash(p, m):
            splash.progress = p
            splash.loading_text = m
            splash.showMessage(
                f"{m}\n\nLoading... {p}%",
                Qt.AlignBottom | Qt.AlignCenter,
                QColor(255, 255, 255)
            )
            app.processEvents()

        window.init_worker.progress.connect(update_splash)

    # Use the signal to trigger the transition
    window.initialization_finished.connect(on_initialization_finished)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
