import sys
import cv2
import os
import time
import datetime
import threading
import numpy as np
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QLabel, QPushButton, QGridLayout,
                                 QStackedWidget, QLineEdit, QComboBox, QFileDialog,
                                 QMessageBox, QFrame, QSplitter, QCheckBox, QSlider,
                                 QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
                                 QDialog, QFormLayout, QSpinBox, QGroupBox, QTextEdit)
    from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont, QPalette, QColor, QPainter
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QDateTime
except Exception as e:
    print("PyQt Import Failed in ui_components:", e)
    import traceback
    traceback.print_exc()

try:
    from enhanced_camera_manager import EnhancedCameraManager
except:
    print("EnhancedCameraManager failed to import in ui_components")

class StorageChoiceDialog(QDialog):
    """Dialog to choose storage location for recordings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Storage Location")
        self.setFixedSize(400, 250)
        self.setModal(True)
        self.storage_choice = None
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #505050;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00aaff;
            }
            QPushButton#localBtn {
                border-color: #00aaff;
            }
            QPushButton#localBtn:hover {
                background-color: #3d3d3d;
                border-color: #00ccff;
            }
            QPushButton#driveBtn {
                border-color: #ff3333;
            }
            QPushButton#driveBtn:hover {
                background-color: #3d3d3d;
                border-color: #ff5555;
            }
            QPushButton#cancelBtn {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton#cancelBtn:hover {
                background-color: #606060;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # Title
        title = QLabel("Where would you like to save the recording?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                padding: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Choose your preferred storage location for this recording session.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #cccccc;
                padding: 5px;
            }
        """)
        layout.addWidget(desc)
        
        # Buttons container
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        
        # Local storage button
        local_btn = QPushButton("💾 Local Storage")
        local_btn.setObjectName("localBtn")
        local_btn.setToolTip("Save recording to your computer's local storage")
        local_btn.clicked.connect(lambda: self.set_choice("local"))
        
        # Google Drive button
        drive_btn = QPushButton("☁️ Google Drive")
        drive_btn.setObjectName("driveBtn")
        drive_btn.setToolTip("Save recording to Google Drive (requires authentication)")
        drive_btn.clicked.connect(lambda: self.set_choice("drive"))
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setToolTip("Cancel recording")
        cancel_btn.clicked.connect(lambda: self.set_choice(None))
        
        buttons_layout.addWidget(local_btn)
        buttons_layout.addWidget(drive_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(buttons_widget)
    
    def set_choice(self, choice):
        """Set the storage choice and close dialog"""
        self.storage_choice = choice
        if choice is None:
            self.reject()
        else:
            self.accept()
    
    def get_choice(self):
        """Get the selected storage choice"""
        return self.storage_choice

class EnhancedCameraWidget(QLabel):
    """Professional CCTV camera widget matching the reference interface"""
    
    clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)  # Add delete signal
    
    def __init__(self, camera_id, camera_name):
        super().__init__()
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.current_frame = None
        self.people_detection_enabled = False
        self.fire_smoke_detection_enabled = False
        self.people_count = 0
        self.fire_smoke_alert_active = False
        
        # Camera technical info
        self.iso_value = "ISO 800"
        self.shutter_speed = "1/60"
        self.aperture = "F5.6"
        self.white_balance = "5600K"
        self.resolution = "1080p"
        self.fps = "30fps"
        
        self.setFixedSize(380, 280)  # Slightly larger for professional look
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #232323;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setText(f"\U0001f4f9 {camera_name}\nConnecting...")
        
        # Create overlay widgets
        self.setup_professional_overlay()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def setup_professional_overlay(self):
        """Setup professional overlay elements matching the reference UI"""
        
        # Top header with camera info
        self.header_widget = QWidget(self)
        self.header_widget.setGeometry(0, 0, 380, 35)
        self.header_widget.setStyleSheet("""
            QWidget {
                background-color: #1f1f1f;
                border-bottom: 1px solid #2a4a7a;
            }
        """)
        
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(5)
        
        # Camera ID
        self.camera_id_label = QLabel(f"CAMERA {self.camera_id.upper()}")
        self.camera_id_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        # Live indicator
        self.live_indicator = QLabel("LIVE")
        self.live_indicator.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 10px;
                font-weight: bold;
                background: rgba(255, 68, 68, 30);
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid #ff4444;
            }
        """)
        
        header_layout.addWidget(self.camera_id_label)
        header_layout.addStretch()
        header_layout.addWidget(self.live_indicator)
        
        # Technical info overlay (top right)
        self.tech_info_widget = QWidget(self)
        self.tech_info_widget.setGeometry(280, 40, 95, 60)
        self.tech_info_widget.setStyleSheet("""
            QWidget {
                background: rgba(10, 15, 26, 180);
                border: 1px solid rgba(30, 58, 95, 100);
                border-radius: 4px;
            }
        """)
        
        tech_layout = QVBoxLayout(self.tech_info_widget)
        tech_layout.setContentsMargins(6, 4, 6, 4)
        tech_layout.setSpacing(1)
        
        # Technical specifications
        self.iso_label = QLabel(self.iso_value)
        self.shutter_label = QLabel(f"S: {self.shutter_speed}")
        self.aperture_label = QLabel(self.aperture)
        
        for label in [self.iso_label, self.shutter_label, self.aperture_label]:
            label.setStyleSheet("""
                QLabel {
                    color: #cccccc;
                    font-size: 9px;
                    font-weight: normal;
                    background: transparent;
                    border: none;
                }
            """)
            tech_layout.addWidget(label)
        
        # Bottom status bar
        self.status_bar_widget = QWidget(self)
        self.status_bar_widget.setGeometry(0, 245, 380, 35)
        self.status_bar_widget.setStyleSheet("""
            QWidget {
                background-color: #1f1f1f;
                border-top: 1px solid #2a4a7a;
            }
        """)
        
        status_layout = QHBoxLayout(self.status_bar_widget)
        status_layout.setContentsMargins(8, 4, 8, 4)
        status_layout.setSpacing(10)
        
        # Timestamp
        self.timestamp_label = QLabel()
        self.timestamp_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10px;
                font-weight: normal;
                background: transparent;
                border: none;
            }
        """)
        self.update_timestamp()
        
        # Resolution and FPS info
        self.resolution_label = QLabel(f"HD | {self.aperture} | {self.resolution}")
        self.resolution_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10px;
                font-weight: normal;
                background: transparent;
                border: none;
            }
        """)
        
        # Quality indicator
        self.quality_label = QLabel("1080p")
        self.quality_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        # Frame rate
        self.fps_label = QLabel(self.fps)
        self.fps_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        
        status_layout.addWidget(self.timestamp_label)
        status_layout.addWidget(self.resolution_label)
        status_layout.addStretch()
        status_layout.addWidget(self.quality_label)
        status_layout.addWidget(self.fps_label)
        
        # People detection indicator (left side)
        self.people_indicator = QLabel(self)
        self.people_indicator.setGeometry(8, 45, 80, 25)
        self.people_indicator.setStyleSheet("""
            QLabel {
                background: rgba(76, 175, 80, 180);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                border: 1px solid #4CAF50;
            }
        """)
        self.people_indicator.hide()
        
        # Fire/Smoke alert indicator (center)
        self.fire_smoke_indicator = QLabel(self)
        self.fire_smoke_indicator.setGeometry(140, 100, 100, 35)
        self.fire_smoke_indicator.setStyleSheet("""
            QLabel {
                background: rgba(255, 0, 0, 220);
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #ff0000;
                text-align: center;
            }
        """)
        self.fire_smoke_indicator.hide()
        
        # Start timestamp update timer
        self.timestamp_timer = QTimer()
        self.timestamp_timer.timeout.connect(self.update_timestamp)
        self.timestamp_timer.start(1000)  # Update every second

    def set_status(self, status):
        """Update the status text on the widget"""
        self.setText(f"📹 {self.camera_name}\n{status}")
        # Also update the quality label with the status if it's brief
        if len(status) < 15:
            self.quality_label.setText(status)
        self.quality_label.show()

    def update_timestamp(self):
        """Update the timestamp display"""
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("Time: %H:%M:%S")
        self.timestamp_label.setText(time_str)
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.camera_id)
    
    def enterEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #ff0000;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 1px solid #232323;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        super().leaveEvent(event)
    
    def update_frame(self, frame):
        """Update with original frame"""
        try:
            self.current_frame = frame.copy()
            self.display_frame(frame)
        except Exception as e:
            print(f"Error updating frame for camera {self.camera_id}: {e}")
    
    def update_detection_frame(self, frame, detections, people_count):
        """Update with people detection results - but show clean frame in grid"""
        try:
            # Store the original frame (not the annotated detection frame)
            # The 'frame' parameter here is the annotated frame, but we need the original
            # We'll use the current_frame if it exists, otherwise use the frame
            if self.current_frame is not None:
                # Keep the original frame for display
                display_frame = self.current_frame.copy()
            else:
                # If no original frame exists, use the provided frame but remove annotations
                display_frame = frame.copy()
            
            self.people_count = people_count
            self.people_detection_enabled = True
            
            # Update people indicator
            if people_count > 0:
                self.people_indicator.setText(f"👥 People: {people_count}")
                self.people_indicator.show()
            else:
                self.people_indicator.hide()
            
            # IMPORTANT: Show clean frame without detection overlays in main grid
            # Use the original frame, not the annotated detection frame
            self.display_frame(display_frame)
                
        except Exception as e:
            print(f"Error updating detection frame for camera {self.camera_id}: {e}")
    
    def update_fire_smoke_frame(self, frame, detections, alert_info):
        """Update with fire/smoke detection results - but show clean frame in grid"""
        try:
            # Store the original frame (not the annotated detection frame)
            # The 'frame' parameter here is the annotated frame, but we need the original
            # We'll use the current_frame if it exists, otherwise use the frame
            if self.current_frame is not None:
                # Keep the original frame for display
                display_frame = self.current_frame.copy()
            else:
                # If no original frame exists, use the provided frame but remove annotations
                display_frame = frame.copy()
            
            self.fire_smoke_detection_enabled = True
            
            # Check if there are fire/smoke detections
            fire_count = alert_info.get('fire_count', 0)
            smoke_count = alert_info.get('smoke_count', 0)
            
            if fire_count > 0 or smoke_count > 0:
                self.fire_smoke_alert_active = True
                
                # Update fire/smoke indicator
                if fire_count > 0:
                    self.fire_smoke_indicator.setText("🔥 FIRE ALERT!")
                    self.fire_smoke_indicator.setStyleSheet("""
                        QLabel {
                            background: rgba(255, 0, 0, 240);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid #ff0000;
                            text-align: center;
                        }
                    """)
                elif smoke_count > 0:
                    self.fire_smoke_indicator.setText("💨 SMOKE ALERT!")
                    self.fire_smoke_indicator.setStyleSheet("""
                        QLabel {
                            background: rgba(128, 128, 128, 240);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid #808080;
                            text-align: center;
                        }
                    """)
                
                self.fire_smoke_indicator.show()
                
                # Update widget border to indicate alert
                self.setStyleSheet("""
                    QLabel {
                        background-color: #000000;
                        border: 2px solid #ff0000;
                        color: white;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                """)
                
                # Update live indicator to show alert
                self.live_indicator.setText("ALERT")
                self.live_indicator.setStyleSheet("""
                    QLabel {
                        color: #ffffff;
                        font-size: 10px;
                        font-weight: bold;
                        background: #ff0000;
                        padding: 2px 6px;
                        border-radius: 3px;
                        border: 1px solid #ff0000;
                    }
                """)
            else:
                self.fire_smoke_alert_active = False
                self.fire_smoke_indicator.hide()
                
                # Reset border and live indicator
                self.setStyleSheet("""
                    QLabel {
                        background-color: #000000;
                        border: 1px solid #232323;
                        color: white;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                """)
                
                self.live_indicator.setText("LIVE")
                self.live_indicator.setStyleSheet("""
                    QLabel {
                        color: #ff4444;
                        font-size: 10px;
                        font-weight: bold;
                        background: rgba(255, 68, 68, 30);
                        padding: 2px 6px;
                        border-radius: 3px;
                        border: 1px solid #ff4444;
                    }
                """)
            
            # IMPORTANT: Show clean frame without detection overlays in main grid
            # Use the original frame, not the annotated detection frame
            self.display_frame(display_frame)
                
        except Exception as e:
            print(f"Error updating fire/smoke frame for camera {self.camera_id}: {e}")
    
    def display_frame(self, frame):
        """Display frame in the widget with professional overlay"""
        try:
            if frame is None:
                return
                
            # Ensure frame is in BGR format (OpenCV default)
            if len(frame.shape) == 3:
                # Convert BGR to RGB for Qt display
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            else:
                # Handle grayscale
                h, w = frame.shape
                qt_image = QImage(frame.data, w, h, w, QImage.Format_Grayscale8)
            
            # Scale to widget size (accounting for overlays)
            display_size = QSize(380, 280)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                display_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
            # Ensure overlays stay on top
            self.header_widget.raise_()
            self.tech_info_widget.raise_()
            self.status_bar_widget.raise_()
            self.people_indicator.raise_()
            self.fire_smoke_indicator.raise_()
            
        except Exception as e:
            print(f"Error displaying frame for camera {self.camera_id}: {e}")
            self.setText(f"📹 {self.camera_name}\nDisplay Error")
    
    def set_detection_enabled(self, enabled):
        """Set detection enabled status"""
        self.people_detection_enabled = enabled
        if not enabled:
            self.people_indicator.hide()
    
    def set_fire_smoke_detection_enabled(self, enabled):
        """Set fire/smoke detection enabled status"""
        self.fire_smoke_detection_enabled = enabled
        if not enabled:
            self.fire_smoke_indicator.hide()
            self.fire_smoke_alert_active = False
    
    def update_camera_settings(self, iso=None, shutter=None, aperture=None, wb=None):
        """Update camera technical settings"""
        if iso:
            self.iso_value = f"ISO {iso}"
            self.iso_label.setText(self.iso_value)
        if shutter:
            self.shutter_speed = shutter
            self.shutter_label.setText(f"S: {self.shutter_speed}")
        if aperture:
            self.aperture = aperture
            self.aperture_label.setText(self.aperture)
        if wb:
            self.white_balance = f"{wb}K"

class EnhancedFullScreenCameraWidget(QWidget):
    back_clicked = pyqtSignal()
    
    def __init__(self, camera_id, camera_name):
        super().__init__()
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.is_playing = True
        self.is_recording = False
        self.zoom_level = 1.0
        self.current_frame = None
        self.current_detection_frame = None
        self.current_fire_smoke_frame = None
        self.playback_speed = 1.0
        self.frame_history = []
        self.max_history = 300
        self.current_frame_index = -1
        self.people_count = 0
        self.people_detection_enabled = False
        self.fire_smoke_detection_enabled = False
        self.detections = []
        self.fire_smoke_detections = []
        self.fire_smoke_alert_info = {}
        
        # Recording variables
        self.video_writer = None
        self.recording_start_time = None
        self.recording_filename = None
        self.use_drive_upload = False
        
        self.setup_ui()
        
        # Timer for auto-hide controls
        self.controls_timer = QTimer()
        self.controls_timer.timeout.connect(self.hide_controls)
        self.controls_visible = True
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top control bar
        self.create_top_controls(layout)
        
        # Main video display
        self.video_label = QLabel()
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: none;
            }
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(False)
        self.video_label.mousePressEvent = self.toggle_controls_visibility
        layout.addWidget(self.video_label, 1)
        
        # Bottom control bar
        self.create_bottom_controls(layout)
        
    def create_top_controls(self, layout):
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(100)  # Increased height for fire/smoke detection info
        self.top_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
                border-bottom: 1px solid #505050;
            }
        """)
        
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        
        # Back button
        back_btn = QPushButton("← Back to Grid")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        
        # Camera title and info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        title_label = QLabel(f"📹 {self.camera_name}")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # Detection info
        self.people_info_label = QLabel("👥 People Detection: OFF")
        self.people_info_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        self.fire_smoke_info_label = QLabel("🔥 Fire/Smoke Detection: OFF")
        self.fire_smoke_info_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(self.people_info_label)
        info_layout.addWidget(self.fire_smoke_info_label)
        
        # Status container
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)
        
        # Top status row
        top_status_widget = QWidget()
        top_status_layout = QHBoxLayout(top_status_widget)
        top_status_layout.setContentsMargins(0, 0, 0, 0)
        top_status_layout.setSpacing(15)
        
        # Recording indicator
        self.recording_indicator = QLabel("⏺ REC")
        self.recording_indicator.setStyleSheet("""
            QLabel {
                color: #ff3333;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border: 1px solid #ff3333;
                border-radius: 4px;
            }
        """)
        self.recording_indicator.hide()
        
        # Recording time
        self.recording_time_label = QLabel("00:00:00")
        self.recording_time_label.setStyleSheet("""
            QLabel {
                color: #ff3333;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.recording_time_label.hide()
        
        # Status
        self.status_label = QLabel("● LIVE")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border: 1px solid #00ff00;
                border-radius: 4px;
            }
        """)
        
        top_status_layout.addWidget(self.recording_indicator)
        top_status_layout.addWidget(self.recording_time_label)
        top_status_layout.addWidget(self.status_label)
        
        # Detection displays
        detection_displays_widget = QWidget()
        detection_displays_layout = QHBoxLayout(detection_displays_widget)
        detection_displays_layout.setContentsMargins(0, 0, 0, 0)
        detection_displays_layout.setSpacing(15)
        
        # People count display
        self.people_count_display = QLabel("👥 People: 0")
        self.people_count_display.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 14px;
                font-weight: bold;
                background: rgba(0, 0, 0, 150);
                padding: 5px 12px;
                border: 2px solid #00ff00;
                border-radius: 6px;
            }
        """)
        self.people_count_display.hide()
        
        # Fire/Smoke alert display
        self.fire_smoke_alert_display = QLabel("🔥 FIRE DETECTED!")
        self.fire_smoke_alert_display.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                background: rgba(255, 0, 0, 200);
                padding: 8px 15px;
                border: 3px solid #ff0000;
                border-radius: 8px;
            }
        """)
        self.fire_smoke_alert_display.hide()
        
        detection_displays_layout.addWidget(self.people_count_display)
        detection_displays_layout.addWidget(self.fire_smoke_alert_display)
        
        status_layout.addWidget(top_status_widget)
        status_layout.addWidget(detection_displays_widget)
        
        top_layout.addWidget(back_btn)
        top_layout.addWidget(info_widget)
        top_layout.addStretch()
        top_layout.addWidget(status_container)
        
        layout.addWidget(self.top_bar)
        
    def create_bottom_controls(self, layout):
        self.bottom_bar = QWidget()
        self.bottom_bar.setFixedHeight(140)  # Increased height for fire/smoke detection controls
        self.bottom_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
                border-top: 1px solid #505050;
            }
        """)
        
        main_layout = QVBoxLayout(self.bottom_bar)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(10)
        
        # Main controls row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        # ---- PLAYBACK CONTROLS ----
        playback_widget = QWidget()
        playback_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 120);
                border-radius: 8px;
            }
        """)
        playback_layout = QHBoxLayout(playback_widget)
        playback_layout.setContentsMargins(15, 8, 15, 8)
        playback_layout.setSpacing(15)
        
        # Backward button
        self.backward_btn = QPushButton("⏪")
        self.backward_btn.setFixedSize(40, 40)
        self.backward_btn.setStyleSheet(self.get_control_button_style())
        self.backward_btn.clicked.connect(self.backward_frame)
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("⏸️")
        self.play_pause_btn.setFixedSize(50, 50)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #00aaff;
                border-radius: 25px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00ccff;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        
        # Forward button
        self.forward_btn = QPushButton("⏩")
        self.forward_btn.setFixedSize(40, 40)
        self.forward_btn.setStyleSheet(self.get_control_button_style())
        self.forward_btn.clicked.connect(self.forward_frame)
        
        # Live button
        self.live_btn = QPushButton("🔴 LIVE")
        self.live_btn.setFixedHeight(30)
        self.live_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        self.live_btn.clicked.connect(self.go_to_live)
        
        playback_layout.addWidget(self.backward_btn)
        playback_layout.addWidget(self.play_pause_btn)
        playback_layout.addWidget(self.forward_btn)
        playback_layout.addWidget(self.live_btn)
        
        # ---- DETECTION CONTROLS ----
        detection_widget = QWidget()
        detection_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 120);
                border-radius: 8px;
            }
        """)
        detection_layout = QVBoxLayout(detection_widget)
        detection_layout.setContentsMargins(15, 8, 15, 8)
        detection_layout.setSpacing(5)
        
        # People detection toggle
        self.people_detection_toggle_btn = QPushButton("👥 People Detection")
        self.people_detection_toggle_btn.setFixedSize(140, 30)
        self.people_detection_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #ffcc00;
            }
        """)
        self.people_detection_toggle_btn.clicked.connect(self.toggle_people_detection)
        
        # Fire/Smoke detection toggle
        self.fire_smoke_detection_toggle_btn = QPushButton("🔥 Fire/Smoke Detection")
        self.fire_smoke_detection_toggle_btn.setFixedSize(140, 30)
        self.fire_smoke_detection_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #ff3333;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #ff5555;
            }
        """)
        self.fire_smoke_detection_toggle_btn.clicked.connect(self.toggle_fire_smoke_detection)
        
        detection_layout.addWidget(self.people_detection_toggle_btn)
        detection_layout.addWidget(self.fire_smoke_detection_toggle_btn)
        
        # ---- RECORDING CONTROLS ----
        recording_widget = QWidget()
        recording_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 120);
                border-radius: 8px;
            }
        """)
        recording_layout = QHBoxLayout(recording_widget)
        recording_layout.setContentsMargins(15, 8, 15, 8)
        
        # Record button
        self.record_btn = QPushButton("⏺️ Record")
        self.record_btn.setFixedSize(90, 40)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #ff3333;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #ff5555;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        
        # Screenshot button
        screenshot_btn = QPushButton("📷 Screenshot")
        screenshot_btn.setFixedSize(100, 40)
        screenshot_btn.setStyleSheet(self.get_control_button_style())
        screenshot_btn.clicked.connect(self.take_screenshot)
        
        recording_layout.addWidget(self.record_btn)
        recording_layout.addWidget(screenshot_btn)
        
        # ---- ZOOM CONTROLS ----
        zoom_widget = QWidget()
        zoom_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 120);
                border-radius: 8px;
            }
        """)
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(15, 8, 15, 8)
        
        zoom_label = QLabel("🔍")
        zoom_label.setStyleSheet("color: white; font-size: 16px;")
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #505050;
                height: 6px;
                background: #2d2d2d;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff3333;
                border: 1px solid #ff3333;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #ff5555;
            }
        """)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        self.zoom_value_label = QLabel("1.0x")
        self.zoom_value_label.setStyleSheet("color: white; font-size: 12px;")
        self.zoom_value_label.setFixedWidth(40)
        
        reset_zoom_btn = QPushButton("Reset")
        reset_zoom_btn.setFixedSize(60, 30)
        reset_zoom_btn.setStyleSheet(self.get_control_button_style())
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value_label)
        zoom_layout.addWidget(reset_zoom_btn)
        
        # ---- FULLSCREEN BUTTON ----
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(50, 50)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #505050;
                border-radius: 25px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00aaff;
            }
        """)
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        # Add all widgets to main controls layout
        controls_layout.addWidget(playback_widget)
        controls_layout.addWidget(detection_widget)
        controls_layout.addWidget(recording_widget)
        controls_layout.addWidget(zoom_widget)
        controls_layout.addStretch()
        controls_layout.addWidget(fullscreen_btn)
        
        main_layout.addLayout(controls_layout)
        
        # Speed control row
        speed_widget = QWidget()
        speed_widget.setFixedHeight(30)
        speed_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 80);
                border-radius: 4px;
            }
        """)
        speed_layout = QHBoxLayout(speed_widget)
        speed_layout.setContentsMargins(10, 0, 10, 0)
        
        speed_label = QLabel("Playback Speed:")
        speed_label.setStyleSheet("color: white; font-size: 12px;")
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(25, 400)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(200)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #505050;
                height: 4px;
                background: #2d2d2d;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00ff00;
                border: 1px solid #00ff00;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
        """)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setStyleSheet("color: white; font-size: 12px;")
        self.speed_label.setFixedWidth(40)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        speed_layout.addStretch()
        
        main_layout.addWidget(speed_widget)
        layout.addWidget(self.bottom_bar)

    def get_control_button_style(self):
        return """
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00aaff;
            }
        """

    def toggle_people_detection(self):
        """Toggle people detection for this camera"""
        main_window = self.window()
        if hasattr(main_window, 'camera_manager'):
            current_state = main_window.camera_manager.is_people_detection_enabled(self.camera_id)
            new_state = not current_state
            
            main_window.camera_manager.enable_people_detection(self.camera_id, new_state)
            self.people_detection_enabled = new_state
            
            if new_state:
                self.people_detection_toggle_btn.setText("👥 Disable People")
                self.people_detection_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00aa00;
                        color: white;
                        border: 2px solid #00cc00;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #00cc00;
                        border-color: #00ff00;
                    }
                """)
                self.people_info_label.setText("👥 People Detection: ON")
                self.people_info_label.setStyleSheet("""
                    QLabel {
                        color: #00ff00;
                        font-size: 12px;
                        background: transparent;
                        font-weight: bold;
                    }
                """)
            else:
                self.people_detection_toggle_btn.setText("👥 People Detection")
                self.people_detection_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: white;
                        border: 2px solid #ffaa00;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        border-color: #ffcc00;
                    }
                """)
                self.people_info_label.setText("👥 People Detection: OFF")
                self.people_info_label.setStyleSheet("""
                    QLabel {
                        color: #cccccc;
                        font-size: 12px;
                        background: transparent;
                    }
                """)
                self.people_count_display.hide()

    def toggle_fire_smoke_detection(self):
        """Toggle fire/smoke detection for this camera"""
        main_window = self.window()
        if hasattr(main_window, 'camera_manager'):
            current_state = main_window.camera_manager.is_fire_smoke_detection_enabled(self.camera_id)
            new_state = not current_state
            
            main_window.camera_manager.enable_fire_smoke_detection(self.camera_id, new_state)
            self.fire_smoke_detection_enabled = new_state
            
            if new_state:
                self.fire_smoke_detection_toggle_btn.setText("🔥 Disable Fire/Smoke")
                self.fire_smoke_detection_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #aa0000;
                        color: white;
                        border: 2px solid #cc0000;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #cc0000;
                        border-color: #ff0000;
                    }
                """)
                self.fire_smoke_info_label.setText("🔥 Fire/Smoke Detection: ON")
                self.fire_smoke_info_label.setStyleSheet("""
                    QLabel {
                        color: #ff3333;
                        font-size: 12px;
                        background: transparent;
                        font-weight: bold;
                    }
                """)
            else:
                self.fire_smoke_detection_toggle_btn.setText("🔥 Fire/Smoke Detection")
                self.fire_smoke_detection_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: white;
                        border: 2px solid #ff3333;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        border-color: #ff5555;
                    }
                """)
                self.fire_smoke_info_label.setText("🔥 Fire/Smoke Detection: OFF")
                self.fire_smoke_info_label.setStyleSheet("""
                    QLabel {
                        color: #cccccc;
                        font-size: 12px;
                        background: transparent;
                    }
                """)
                self.fire_smoke_alert_display.hide()

    def update_people_detection_info(self, people_count, detections):
        """Update people detection information"""
        self.people_count = people_count
        self.detections = detections
        
        if self.people_detection_enabled and people_count > 0:
            self.people_count_display.setText(f"👥 People: {people_count}")
            self.people_count_display.show()
        else:
            self.people_count_display.hide()

    def update_fire_smoke_detection_info(self, detections, alert_info):
        """Update fire/smoke detection information"""
        self.fire_smoke_detections = detections
        self.fire_smoke_alert_info = alert_info
        
        if self.fire_smoke_detection_enabled and (alert_info.get('fire_count', 0) > 0 or alert_info.get('smoke_count', 0) > 0):
            if alert_info.get('alert_type') == 'fire':
                self.fire_smoke_alert_display.setText("🔥 FIRE DETECTED!")
                self.fire_smoke_alert_display.setStyleSheet("""
                    QLabel {
                        color: #ffffff;
                        font-size: 16px;
                        font-weight: bold;
                        background: rgba(255, 0, 0, 200);
                        padding: 8px 15px;
                        border: 3px solid #ff0000;
                        border-radius: 8px;
                    }
                """)
            elif alert_info.get('alert_type') == 'smoke':
                self.fire_smoke_alert_display.setText("💨 SMOKE DETECTED!")
                self.fire_smoke_alert_display.setStyleSheet("""
                    QLabel {
                        color: #ffffff;
                        font-size: 16px;
                        font-weight: bold;
                        background: rgba(128, 128, 128, 200);
                        padding: 8px 15px;
                        border: 3px solid #808080;
                        border-radius: 8px;
                    }
                """)
            self.fire_smoke_alert_display.show()
        else:
            self.fire_smoke_alert_display.hide()

    def show_storage_choice_dialog(self):
        """Show dialog to choose storage location and return choice"""
        dialog = StorageChoiceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_choice()
        return None

    def toggle_recording(self):
        """Toggle video recording with storage choice"""
        if not self.is_recording:
            # Show storage choice dialog
            storage_choice = self.show_storage_choice_dialog()
            
            if storage_choice == "local":
                self.start_recording(use_drive=False)
            elif storage_choice == "drive":
                # Check if Google Drive is authenticated
                main_window = self.window()
                if hasattr(main_window, 'google_drive_manager') and main_window.google_drive_manager.is_authenticated():
                    self.start_recording(use_drive=True)
                else:
                    # Authenticate Google Drive
                    reply = QMessageBox.question(
                        self, "Google Drive Authentication",
                        "You need to authenticate with Google Drive first. Proceed?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        if main_window.google_drive_manager.authenticate():
                            self.start_recording(use_drive=True)
                        else:
                            QMessageBox.warning(self, "Authentication Failed", 
                                              "Failed to authenticate with Google Drive")
            # If storage_choice is None (cancelled), do nothing
        else:
            self.stop_recording()

    def start_recording(self, use_drive=False):
        """Start video recording with optional Google Drive upload"""
        try:
            # Create recordings directory if it doesn't exist
            recordings_dir = "recordings"
            if not os.path.exists(recordings_dir):
                os.makedirs(recordings_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_filename = os.path.join(recordings_dir, f"{self.camera_name}_{timestamp}.mp4")
            
            # Store the Google Drive upload preference
            self.use_drive_upload = use_drive
            
            # Initialize video writer
            if self.current_frame is not None:
                h, w = self.current_frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(self.recording_filename, fourcc, 30.0, (w, h))
                
                self.is_recording = True
                self.recording_start_time = time.time()
                
                # Update UI
                self.record_btn.setText("⏹️ Stop")
                self.record_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff3333;
                        color: white;
                        border: 2px solid #ff5555;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff5555;
                    }
                """)
                self.recording_indicator.show()
                self.recording_time_label.show()
                
                # Start recording timer
                self.recording_timer = QTimer()
                self.recording_timer.timeout.connect(self.update_recording_time)
                self.recording_timer.start(1000)  # Update every second
                
                # Show different message based on storage choice
                if use_drive:
                    storage_msg = "Google Drive (after completion)"
                else:
                    storage_msg = "Local Storage"
                    
                print(f"Started recording: {self.recording_filename} - Saving to: {storage_msg}")
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            QMessageBox.warning(self, "Recording Error", f"Failed to start recording: {str(e)}")

    def stop_recording(self):
        """Stop video recording and upload to Google Drive if selected"""
        try:
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            self.is_recording = False
            
            # Update UI
            self.record_btn.setText("⏺️ Record")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: white;
                    border: 2px solid #ff3333;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border-color: #ff5555;
                }
            """)
            self.recording_indicator.hide()
            self.recording_time_label.hide()
            
            if hasattr(self, 'recording_timer'):
                self.recording_timer.stop()
            
            if self.recording_filename:
                print(f"Recording saved: {self.recording_filename}")
                
                # Handle Google Drive upload if selected
                if self.use_drive_upload:
                    main_window = self.window()
                    if hasattr(main_window, 'google_drive_manager') and main_window.google_drive_manager.is_authenticated():
                        success = main_window.google_drive_manager.upload_recording(
                            self.recording_filename, self.camera_name
                        )
                        if success:
                            QMessageBox.information(self, "Upload Started", 
                                                  "Recording upload to Google Drive started. You can view it in the Recordings page when complete.")
                        else:
                            QMessageBox.warning(self, "Upload Failed", 
                                              "Failed to start upload to Google Drive. Recording saved locally.")
                else:
                    QMessageBox.information(self, "Recording Saved", 
                                          f"Recording saved locally:\n{self.recording_filename}")
            
        except Exception as e:
            print(f"Error stopping recording: {e}")

    # Include all the other methods from the original FullScreenCameraWidget
    def toggle_controls_visibility(self, event=None):
        if self.controls_visible:
            self.hide_controls()
        else:
            self.show_controls()
            
    def show_controls(self):
        self.top_bar.show()
        self.bottom_bar.show()
        self.controls_visible = True
        self.controls_timer.start(3000)
        
    def hide_controls(self):
        self.top_bar.hide()
        self.bottom_bar.hide()
        self.controls_visible = False
        self.controls_timer.stop()
        
    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_btn.setText("⏸️")
            if self.current_frame_index == -1:
                self.status_label.setText("● LIVE")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #00ff00;
                        font-size: 14px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
            else:
                self.status_label.setText("▶ PLAYING")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #00aaff;
                        font-size: 14px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
        else:
            self.play_pause_btn.setText("▶️")
            self.status_label.setText("⏸ PAUSED")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ffaa00;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
    
    def backward_frame(self):
        if len(self.frame_history) > 0:
            if self.current_frame_index == -1:
                self.current_frame_index = len(self.frame_history) - 1
            else:
                self.current_frame_index = max(0, self.current_frame_index - 1)
            
            if self.current_frame_index < len(self.frame_history):
                frame = self.frame_history[self.current_frame_index]
                self.display_frame(frame)
                self.status_label.setText(f"◀ FRAME {self.current_frame_index + 1}/{len(self.frame_history)}")
    
    def forward_frame(self):
        if len(self.frame_history) > 0 and self.current_frame_index != -1:
            self.current_frame_index = min(len(self.frame_history) - 1, self.current_frame_index + 1)
            
            if self.current_frame_index == len(self.frame_history) - 1:
                self.go_to_live()
            else:
                frame = self.frame_history[self.current_frame_index]
                self.display_frame(frame)
                self.status_label.setText(f"▶ FRAME {self.current_frame_index + 1}/{len(self.frame_history)}")
    
    def go_to_live(self):
        self.current_frame_index = -1
        self.is_playing = True
        self.play_pause_btn.setText("⏸️")
        self.status_label.setText("● LIVE")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
    
    def on_speed_changed(self, value):
        self.playback_speed = value / 100.0
        self.speed_label.setText(f"{self.playback_speed:.1f}x")
    
    def on_zoom_changed(self, value):
        self.zoom_level = value / 100.0
        self.zoom_value_label.setText(f"{self.zoom_level:.1f}x")
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def reset_zoom(self):
        self.zoom_slider.setValue(100)
        self.zoom_level = 1.0
        self.zoom_value_label.setText("1.0x")
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def update_recording_time(self):
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.recording_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def take_screenshot(self):
        try:
            if self.current_frame is not None:
                screenshots_dir = "screenshots"
                if not os.path.exists(screenshots_dir):
                    os.makedirs(screenshots_dir)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(screenshots_dir, f"{self.camera_name}_{timestamp}.jpg")
                
                # Use the most appropriate frame for screenshot
                frame_to_save = self.current_frame
                if self.fire_smoke_detection_enabled and self.current_fire_smoke_frame is not None:
                    frame_to_save = self.current_fire_smoke_frame
                elif self.people_detection_enabled and self.current_detection_frame is not None:
                    frame_to_save = self.current_detection_frame
                
                cv2.imwrite(filename, frame_to_save)
                print(f"Screenshot saved: {filename}")
                QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved to:\n{filename}")
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            QMessageBox.warning(self, "Screenshot Error", f"Failed to take screenshot: {str(e)}")
    
    def display_frame(self, frame):
        try:
            display_frame = frame.copy()
            if self.zoom_level > 1.0:
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                
                crop_w = int(w / self.zoom_level)
                crop_h = int(h / self.zoom_level)
                
                x1 = max(0, center_x - crop_w // 2)
                y1 = max(0, center_y - crop_h // 2)
                x2 = min(w, x1 + crop_w)
                y2 = min(h, y1 + crop_h)
                
                cropped = frame[y1:y2, x1:x2]
                display_frame = cv2.resize(cropped, (w, h))
            
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
    
    def update_frame(self, frame):
        """Update with original frame"""
        try:
            self.current_frame = frame.copy()
            
            if self.current_frame_index == -1:
                self.frame_history.append(frame.copy())
                if len(self.frame_history) > self.max_history:
                    self.frame_history.pop(0)
            
            # Display frame if we're in live mode and no detection frames are available
            if (self.is_playing and self.current_frame_index == -1 and 
                not self.fire_smoke_detection_enabled and not self.people_detection_enabled):
                self.display_frame(frame)
            
            if self.is_recording and self.video_writer:
                # Record the most appropriate frame
                frame_to_record = frame
                if self.fire_smoke_detection_enabled and self.current_fire_smoke_frame is not None:
                    frame_to_record = self.current_fire_smoke_frame
                elif self.people_detection_enabled and self.current_detection_frame is not None:
                    frame_to_record = self.current_detection_frame
                
                self.video_writer.write(frame_to_record)
            
        except Exception as e:
            print(f"Error updating frame for camera {self.camera_id}: {e}")

    def update_detection_frame(self, frame, detections, people_count):
        """Update with people detection results - but show clean frame in grid"""
        try:
            # Store the original frame (not the annotated detection frame)
            # The 'frame' parameter here is the annotated frame, but we need the original
            # We'll use the current_frame if it exists, otherwise use the frame
            if self.current_frame is not None:
                # Keep the original frame for display
                display_frame = self.current_frame.copy()
            else:
                # If no original frame exists, use the provided frame but remove annotations
                display_frame = frame.copy()
            
            self.people_count = people_count
            self.people_detection_enabled = True
            
            # Update people indicator
            if people_count > 0:
                self.people_indicator.setText(f"👥 People: {people_count}")
                self.people_indicator.show()
            else:
                self.people_indicator.hide()
            
            # IMPORTANT: Show clean frame without detection overlays in main grid
            # Use the original frame, not the annotated detection frame
            self.display_frame(display_frame)
                
        except Exception as e:
            print(f"Error updating detection frame for camera {self.camera_id}: {e}")
    
    def update_fire_smoke_frame(self, frame, detections, alert_info):
        """Update with fire/smoke detection results - but show clean frame in grid"""
        try:
            # Store the original frame (not the annotated detection frame)
            # The 'frame' parameter here is the annotated frame, but we need the original
            # We'll use the current_frame if it exists, otherwise use the frame
            if self.current_frame is not None:
                # Keep the original frame for display
                display_frame = self.current_frame.copy()
            else:
                # If no original frame exists, use the provided frame but remove annotations
                display_frame = frame.copy()
            
            self.fire_smoke_detection_enabled = True
            
            # Check if there are fire/smoke detections
            fire_count = alert_info.get('fire_count', 0)
            smoke_count = alert_info.get('smoke_count', 0)
            
            if fire_count > 0 or smoke_count > 0:
                self.fire_smoke_alert_active = True
                
                # Update fire/smoke indicator
                if fire_count > 0:
                    self.fire_smoke_indicator.setText("🔥 FIRE ALERT!")
                    self.fire_smoke_indicator.setStyleSheet("""
                        QLabel {
                            background: rgba(255, 0, 0, 240);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid #ff0000;
                            text-align: center;
                        }
                    """)
                elif smoke_count > 0:
                    self.fire_smoke_indicator.setText("💨 SMOKE ALERT!")
                    self.fire_smoke_indicator.setStyleSheet("""
                        QLabel {
                            background: rgba(128, 128, 128, 240);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 2px solid #808080;
                            text-align: center;
                        }
                    """)
                
                self.fire_smoke_indicator.show()
                
                # Update widget border to indicate alert
                self.setStyleSheet("""
                    QLabel {
                        background-color: #000000;
                        border: 2px solid #ff0000;
                        color: white;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                """)
                
                # Update live indicator to show alert
                self.live_indicator.setText("ALERT")
                self.live_indicator.setStyleSheet("""
                    QLabel {
                        color: #ffffff;
                        font-size: 10px;
                        font-weight: bold;
                        background: #ff0000;
                        padding: 2px 6px;
                        border-radius: 3px;
                        border: 1px solid #ff0000;
                    }
                """)
            else:
                self.fire_smoke_alert_active = False
                self.fire_smoke_indicator.hide()
                
                # Reset border and live indicator
                self.setStyleSheet("""
                    QLabel {
                        background-color: #000000;
                        border: 1px solid #232323;
                        color: white;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                """)
                
                self.live_indicator.setText("LIVE")
                self.live_indicator.setStyleSheet("""
                    QLabel {
                        color: #ff4444;
                        font-size: 10px;
                        font-weight: bold;
                        background: rgba(255, 68, 68, 30);
                        padding: 2px 6px;
                        border-radius: 3px;
                        border: 1px solid #ff4444;
                    }
                """)
            
            # IMPORTANT: Show clean frame without detection overlays in main grid
            # Use the original frame, not the annotated detection frame
            self.display_frame(display_frame)
                
        except Exception as e:
            print(f"Error updating fire/smoke frame for camera {self.camera_id}: {e}")

class AddCameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Camera")
        self.setFixedSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Add New Camera")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px 0px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)

        # Camera name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Front Door Camera")

        # Camera type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Webcam", "IP Camera", "Analog Camera", "Video File"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        # Source input
        self.source_input = QLineEdit()
        self.source_input.setText("0")
        self.source_input.setPlaceholderText("Camera source (0 for default webcam)")
        
        # Browse button for video files
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        self.browse_btn.hide()
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(self.browse_btn)

        form_layout.addRow("Camera Name:", self.name_input)
        form_layout.addRow("Camera Type:", self.type_combo)
        form_layout.addRow("Source:", source_layout)

        layout.addWidget(form_widget)

        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        add_btn = QPushButton("Add Camera")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_camera)

        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)

        layout.addWidget(buttons_widget)

    def on_type_changed(self, camera_type):
        """Handle camera type change"""
        self.browse_btn.hide()
        
        if camera_type == "Webcam":
            self.source_input.setText("0")
            self.source_input.setPlaceholderText("Camera index (0, 1, 2...)")
        elif camera_type == "IP Camera":
            self.source_input.setText("rtsp://192.168.1.100:554/stream")
            self.source_input.setPlaceholderText("RTSP URL")
        elif camera_type == "Analog Camera":
            self.source_input.setText("/dev/video0")
            self.source_input.setPlaceholderText("Device path")
        elif camera_type == "Video File":
            self.source_input.setText("")
            self.source_input.setPlaceholderText("Select video file path...")
            self.browse_btn.show()

    def browse_file(self):
        """Browse for video file"""
        file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov)")
        if file:
            self.source_input.setText(file)

    def add_camera(self):
        """Add the camera"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a camera name.")
            return

        source = self.source_input.text().strip()
        if not source:
            QMessageBox.warning(self, "Error", "Please enter a camera source.")
            return

        camera_type = self.type_combo.currentText()

        # Generate unique ID
        import uuid
        camera_id = str(uuid.uuid4())[:8]

        # Convert source for webcam
        if camera_type == "Webcam":
            try:
                source = int(source)
            except ValueError:
                QMessageBox.warning(self, "Error", "Webcam source must be a number.")
                return

        self.camera_data = {
            'id': camera_id,
            'name': name,
            'source': source,
            'type': camera_type.lower().replace(" ", "_")
        }

        self.accept()

    def get_camera_data(self):
        """Get the camera data"""
        return getattr(self, 'camera_data', None)
