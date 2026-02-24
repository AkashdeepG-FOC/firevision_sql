import cv2
import numpy as np
import time
import datetime
import threading
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

import urllib.request
import urllib.error
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QSlider, QFrame, QSplitter,
                           QScrollArea, QListWidget, QListWidgetItem,
                           QComboBox, QCheckBox, QSpinBox, QGroupBox,
                           QTabWidget, QTextEdit, QProgressBar, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtCore import QSize, QUrl, QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from enhanced_review_system import (PanicBehaviorDetector, EventClipManager, 
                                 EventReviewWidget, PanicBehavior, EventClip)
from notification_manager import NotificationManager

# --- SAFE MODE FLAGS FOR DEBUGGING CRASH ---
# Set these to True to DISABLE the feature and prevent crashes
DISABLE_AUDIO_ALARM = True      # Disable QMediaPlayer alarm
DISABLE_SIDE_PANEL_UPDATE = False # Disable side panel widget creation/update
DISABLE_AUTO_RECORDING = True     # Disable cv2.VideoWriter recording
DISABLE_ESP32_COMMANDS = True     # Disable Pump/Fan commands
# -------------------------------------------

class ESP32CommandThread(QThread):
    """Thread to send ESP32 commands without blocking UI"""
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            with urllib.request.urlopen(self.url, timeout=3) as _:
                pass
            print(f"📡 Sent ESP32 command: {self.url}")
        except Exception as e:
            print(f"❌ ESP32 command failed: {e}")

class ThumbnailTimelineWidget(QWidget):
    """Dedicated thumbnail timeline player for side panel"""
    
    thumbnail_clicked = pyqtSignal(str)  # clip_id
    
    def __init__(self, clip_manager, camera_id):
        super().__init__()
        self.clip_manager = clip_manager
        self.camera_id = camera_id
        self.thumbnails = []
        self.current_playing_clip = None
        self.playback_cap = None
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_frame)
        self.is_playing = False
        self.current_frame_pos = 0
        self.total_frames = 0
        self.playback_fps = 25
        
        self.setup_ui()
        self.load_thumbnails()
        
    def setup_ui(self):
        """Setup the thumbnail timeline UI for side panel"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QWidget()
        header.setFixedHeight(25)
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 3, 8, 3)
        
        title_label = QLabel("📹 Timeline")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(20, 20)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 8px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_thumbnails)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        
        # Thumbnail scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(80)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: 1px solid #505050;
                border-radius: 4px;
            }
        """)
        
        # Thumbnail container
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QHBoxLayout(self.thumbnail_container)
        self.thumbnail_layout.setContentsMargins(3, 3, 3, 3)
        self.thumbnail_layout.setSpacing(3)
        self.thumbnail_layout.setAlignment(Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.thumbnail_container)
        
        # Playback controls
        controls = QWidget()
        controls.setFixedHeight(30)
        controls.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(8, 3, 8, 3)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶️")
        self.play_btn.setFixedSize(25, 25)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #505050;
                height: 4px;
                background: #2d2d2d;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ff3333;
                border: 1px solid #ff5555;
                width: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #ff3333;
                border-radius: 2px;
            }
        """)
        self.progress_slider.valueChanged.connect(self.seek_to_position)
        
        # Time label
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 8px;
                background: transparent;
            }
        """)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.progress_slider)
        controls_layout.addWidget(self.time_label)
        
        layout.addWidget(header)
        layout.addWidget(self.scroll_area)
        layout.addWidget(controls)
        
    def load_thumbnails(self):
        """Load event clip thumbnails"""
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())):
            child = self.thumbnail_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get clips for this camera
        clips = self.clip_manager.get_clips_by_filter(camera_id=self.camera_id)
        
        for clip in clips[:15]:  # Show last 15 clips
            thumbnail_widget = self.create_thumbnail_widget(clip)
            self.thumbnail_layout.addWidget(thumbnail_widget)
        
        # Add stretch to push thumbnails to the left
        self.thumbnail_layout.addStretch()
        
    def create_thumbnail_widget(self, clip):
        """Create a thumbnail widget for a clip"""
        widget = QWidget()
        widget.setFixedSize(60, 45)
        widget.setStyleSheet("""
            QWidget {
                background-color: #3d3d3d;
                border: 1px solid #505050;
                border-radius: 3px;
            }
            QWidget:hover {
                border-color: #ff3333;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # Thumbnail image
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(56, 35)
        thumbnail_label.setAlignment(Qt.AlignCenter)
        thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #505050;
                border-radius: 2px;
            }
        """)
        
        # Load thumbnail image if exists
        # Load thumbnail image if exists
        loaded_thumbnail = False
        try:
            if os.path.exists(clip.thumbnail_path):
                pixmap = QPixmap(clip.thumbnail_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(56, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumbnail_label.setPixmap(scaled_pixmap)
                    loaded_thumbnail = True
        except Exception:
            pass

        if not loaded_thumbnail:
            # Event type emoji as fallback
            type_emoji = {
                'fire': '🔥',
                'smoke': '💨',
                'panic': '😰',
                'combined': '🚨'
            }.get(clip.event_type, '📹')
            thumbnail_label.setText(type_emoji)
            thumbnail_label.setStyleSheet(thumbnail_label.styleSheet() + "font-size: 12px;")
        
        # Info label
        timestamp = datetime.datetime.fromtimestamp(clip.start_time)
        time_str = timestamp.strftime("%H:%M")
        
        info_label = QLabel(time_str)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 7px;
                background: transparent;
            }
        """)
        
        layout.addWidget(thumbnail_label)
        layout.addWidget(info_label)
        
        # Store clip ID for click handling
        widget.clip_id = clip.clip_id
        widget.clip_path = clip.file_path
        widget.mousePressEvent = lambda event, cid=clip.clip_id, cpath=clip.file_path: self.play_clip(cid, cpath)
        
        return widget
        
    def play_clip(self, clip_id, clip_path):
        """Play selected clip in the thumbnail player"""
        if not os.path.exists(clip_path):
            print(f"Clip file not found: {clip_path}")
            return
            
        # Stop current playback if any
        if self.playback_cap:
            self.playback_timer.stop()
            self.playback_cap.release()
            
        # Open new clip
        self.playback_cap = cv2.VideoCapture(clip_path)
        if not self.playback_cap.isOpened():
            print(f"Failed to open clip: {clip_path}")
            return
            
        self.current_playing_clip = clip_id
        self.current_frame_pos = 0
        self.total_frames = int(self.playback_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.playback_fps = self.playback_cap.get(cv2.CAP_PROP_FPS) or 25
        
        # Setup progress slider
        self.progress_slider.setEnabled(True)
        self.progress_slider.setRange(0, self.total_frames - 1)
        self.progress_slider.setValue(0)
        
        # Start playback
        self.is_playing = True
        self.play_btn.setText("⏸️")
        interval = int(1000 / self.playback_fps)
        self.playback_timer.start(interval)
        
        # Emit signal to main widget
        self.thumbnail_clicked.emit(clip_id)
        
        print(f"Playing clip in thumbnail player: {clip_id}")
        
    def toggle_playback(self):
        """Toggle playback state"""
        if not self.playback_cap:
            return
            
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.play_btn.setText("⏸️")
            interval = int(1000 / self.playback_fps)
            self.playback_timer.start(interval)
        else:
            self.play_btn.setText("▶️")
            self.playback_timer.stop()
            
    def update_playback_frame(self):
        """Update playback frame"""
        if not self.playback_cap or not self.is_playing:
            return
            
        ret, frame = self.playback_cap.read()
        if not ret:
            # End of clip
            self.playback_timer.stop()
            self.is_playing = False
            self.play_btn.setText("▶️")
            return
            
        self.current_frame_pos = int(self.playback_cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        # Update progress slider
        self.progress_slider.setValue(self.current_frame_pos)
        
        # Update time label
        current_time = self.current_frame_pos / self.playback_fps
        time_str = f"{int(current_time//60):02d}:{int(current_time%60):02d}"
        self.time_label.setText(time_str)
        
    def seek_to_position(self, position):
        """Seek to specific position in clip"""
        if self.playback_cap and not self.is_playing:  # Only allow seeking when paused
            self.playback_cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            self.current_frame_pos = position
            
            # Update time label
            current_time = position / self.playback_fps
            time_str = f"{int(current_time//60):02d}:{int(current_time%60):02d}"
            self.time_label.setText(time_str)


class FireDetectionSidePanelWidget(QWidget):
    """Fire detection frame-by-frame processor for side panel"""
    
    dispatch_clicked = pyqtSignal(str, str)  # camera_id, clip_id
    false_alert_clicked = pyqtSignal(str, str)  # camera_id, clip_id
    
    def __init__(self, camera_id, camera_name, fire_detection_backend=None, notification_manager=None):
        super().__init__()
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.fire_detection_backend = fire_detection_backend
        self.notification_manager = notification_manager
        self.fire_detected_frames = []
        self.current_frame_index = 0
        self.detection_active = False
        self.current_alert_id = None  # Store the current alert ID for backend communication
        
        # Initialize audio player for alarm sound
        try:
            self.alarm_player = QMediaPlayer()
            self.alarm_player.setVolume(80)  # Set volume to 80%
            
            # Load alarm audio file
            self.alarm_audio_path = resource_path(os.path.join("assests", "audio", "fire_alarm.mp3"))
            self.load_alarm_audio()
        except Exception as e:
            print(f"❌ Error initializing alarm audio: {e}")
            if not hasattr(self, 'alarm_player'):
                self.alarm_player = None
        
        self.setup_ui()
        
    def load_alarm_audio(self):
        """Load the alarm audio file with robust error handling"""
        try:
            if not hasattr(self, 'alarm_player') or self.alarm_player is None:
                return

            if os.path.exists(self.alarm_audio_path):
                self.alarm_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(self.alarm_audio_path))))
                print(f"✅ Alarm audio loaded: {self.alarm_audio_path}")
            else:
                print(f"⚠️ Alarm audio file not found: {self.alarm_audio_path}")
                # Try alternative paths
                alternative_paths = [
                    os.path.join("assets", "audio", "fire_alarm.mp3"),
                    os.path.join("audio", "fire_alarm.mp3"),
                    "fire_alarm.mp3"
                ]
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        self.alarm_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(alt_path))))
                        print(f"✅ Alarm audio loaded from alternative path: {alt_path}")
                        self.alarm_audio_path = alt_path
                        break
                else:
                    print("❌ No alarm audio file found in any expected location")
        except Exception as e:
            print(f"❌ Error loading alarm audio: {e}")

    def setup_ui(self):
        """Setup fire detection frame processor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Alert header
        self.alert_header = QWidget()
        self.alert_header.setFixedHeight(35)
        self.alert_header.setStyleSheet("""
            QWidget {
                background-color: #ff0000;
                border-radius: 4px;
            }
        """)
        self.alert_header.hide()
        
        alert_layout = QHBoxLayout(self.alert_header)
        alert_layout.setContentsMargins(8, 5, 8, 5)
        
        self.alert_label = QLabel("🚨 FIRE DETECTED - FRAME ANALYSIS")
        self.alert_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        # Auto alarm countdown label (right side)
        self.countdown_label = QLabel("Auto alarm in: --")
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.countdown_label.hide()

        alert_layout.addWidget(self.alert_label)
        alert_layout.addStretch()
        alert_layout.addWidget(self.countdown_label)
        
        # Frame display
        self.frame_label = QLabel()
        self.frame_label.setFixedSize(350, 200)
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 4px;
            }
        """)
        self.frame_label.hide()
        
        # Controls
        controls = QWidget()
        controls.setFixedHeight(80)
        controls.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
        """)
        controls.hide()
        self.controls_widget = controls
        
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(8, 5, 8, 5)
        
        # Frame navigation
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⏮️")
        self.prev_btn.setFixedSize(30, 25)
        self.prev_btn.clicked.connect(self.previous_frame)
        
        self.next_btn = QPushButton("⏭️")
        self.next_btn.setFixedSize(30, 25)
        self.next_btn.clicked.connect(self.next_frame)
        
        self.frame_info = QLabel("Frame 1 of 1")
        self.frame_info.setAlignment(Qt.AlignCenter)
        self.frame_info.setStyleSheet("color: white; font-size: 10px;")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.frame_info)
        nav_layout.addWidget(self.next_btn)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.dispatch_btn = QPushButton("🚨 DISPATCH")
        self.dispatch_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        self.dispatch_btn.clicked.connect(self.dispatch_alert)
        
        self.false_alert_btn = QPushButton("❌ FALSE ALERT")
        self.false_alert_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        self.false_alert_btn.clicked.connect(self.mark_false_alert)
        
        # Test alarm button
        self.test_alarm_btn = QPushButton("🔊 TEST")
        self.test_alarm_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8800;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6600;
            }
        """)
        self.test_alarm_btn.clicked.connect(self.test_alarm_audio)
        self.test_alarm_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.test_alarm_btn.customContextMenuRequested.connect(self.show_audio_context_menu)
        
        self.close_btn = QPushButton("✖️ CLOSE")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
        """)
        self.close_btn.clicked.connect(self.close_detection_mode)
        
        action_layout.addWidget(self.dispatch_btn)
        action_layout.addWidget(self.false_alert_btn)
        action_layout.addWidget(self.test_alarm_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.close_btn)
        
        controls_layout.addLayout(nav_layout)
        controls_layout.addLayout(action_layout)
        
        layout.addWidget(self.alert_header)
        layout.addWidget(self.frame_label)
        layout.addWidget(controls)
        
    def activate_fire_detection_mode(self, frames_with_detections, alert_id=None):
        """Activate frame-by-frame fire detection mode"""
        self.fire_detected_frames = frames_with_detections
        self.current_frame_index = 0
        self.detection_active = True
        self.current_alert_id = alert_id  # Store the alert ID for backend communication
        
        # Show UI elements
        self.alert_header.show()
        self.frame_label.show()
        self.controls_widget.show()
        
        # Display first frame
        self.update_frame_display()
        
        print(f"🔥 Fire detection mode activated with {len(frames_with_detections)} frames")
        if alert_id:
            print(f"📋 Alert ID: {alert_id}")

    def update_frames(self, frames_with_detections):
        """Update frames in existing fire detection mode"""
        if self.detection_active:
            self.fire_detected_frames = frames_with_detections
            # Keep current frame index if valid, otherwise go to latest
            if self.current_frame_index >= len(self.fire_detected_frames):
                self.current_frame_index = len(self.fire_detected_frames) - 1
            self.update_frame_display()
        
    def update_frame_display(self):
        """Update the current frame display with detection information"""
        if not self.fire_detected_frames or self.current_frame_index >= len(self.fire_detected_frames):
            return
        
        frame_data = self.fire_detected_frames[self.current_frame_index]
        frame = frame_data['frame']
        detections = frame_data.get('detections', [])
        alert_info = frame_data.get('alert_info', {})
        
        # Display frame with bounding boxes in side panel
        if frame is not None:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.frame_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.frame_label.setPixmap(scaled_pixmap)
        
        # Update frame info with detection details
        detection_count = len(detections)
        fire_count = alert_info.get('fire_count', 0)
        smoke_count = alert_info.get('smoke_count', 0)
        max_confidence = alert_info.get('max_confidence', 0)
        
        info_text = f"Frame {self.current_frame_index + 1}/{len(self.fire_detected_frames)}"
        info_text += f"\n🔥 Fire: {fire_count} | 💨 Smoke: {smoke_count}"
        info_text += f"\n📊 Confidence: {max_confidence:.2f}"
        
        self.frame_info.setText(info_text)
        
        # Update button states
        self.prev_btn.setEnabled(self.current_frame_index > 0)
        self.next_btn.setEnabled(self.current_frame_index < len(self.fire_detected_frames) - 1)
        
    def previous_frame(self):
        """Go to previous frame"""
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.update_frame_display()
            
    def next_frame(self):
        """Go to next frame"""
        if self.current_frame_index < len(self.fire_detected_frames) - 1:
            self.current_frame_index += 1
            self.update_frame_display()
            
    def dispatch_alert(self):
        """Handle dispatch button click"""
        current_frame_data = self.fire_detected_frames[self.current_frame_index]
        clip_id = current_frame_data.get('clip_id', 'unknown')
        
        # Play alarm audio when dispatch is clicked
        try:
            if self.alarm_player.mediaStatus() == QMediaPlayer.LoadedMedia:
                self.alarm_player.play()
                print("🔊 Playing alarm audio for dispatch")
            else:
                print("⚠️ Alarm audio not loaded properly")
        except Exception as e:
            print(f"❌ Error playing alarm audio: {e}")
        
        # Send comprehensive notification to both backend and mobile app
        if self.notification_manager and self.current_alert_id:
            try:
                # Get current frame and detection data
                frame = current_frame_data.get('frame')
                detections = current_frame_data.get('detections', [])
                alert_info = current_frame_data.get('alert_info', {})
                
                if frame is not None:
                    # Send to both backend and mobile app
                    results = self.notification_manager.send_comprehensive_fire_alert(
                        camera_id=self.camera_id,
                        camera_name=self.camera_name,
                        frame=frame,
                        detections=detections,
                        alert_info=alert_info
                    )
                    
                    # Log results
                    backend_status = "✅" if results['backend'] else "❌"
                    mobile_status = "✅" if results['mobile'] else "❌"
                    print(f"🚨 Emergency dispatch notification results:")
                    print(f"   Backend: {backend_status}")
                    print(f"   Mobile App: {mobile_status}")
                    
                    # Show success message
                    QMessageBox.information(self, "Dispatch Successful", 
                                          f"Emergency services have been dispatched successfully!\n\n"
                                          f"Backend: {backend_status}\n"
                                          f"Mobile App: {mobile_status}")
                else:
                    print("⚠️ No frame data available for notification")
                    QMessageBox.warning(self, "Dispatch Warning", 
                                      "Emergency services dispatched but notification data incomplete.")
                    
            except Exception as e:
                print(f"❌ Error sending dispatch notification: {e}")
                QMessageBox.critical(self, "Notification Error", 
                                   f"Error sending dispatch notification: {e}")
        
        # If we have a backend connection and alert ID, dispatch emergency services
        if self.fire_detection_backend and self.current_alert_id:
            try:
                success = self.fire_detection_backend.dispatch_emergency_services(
                    alert_id=self.current_alert_id,
                    dispatched_by="user",
                    dispatch_notes=f"Emergency services dispatched from camera {self.camera_id}"
                )
                
                if success:
                    print(f"🚨 Emergency services dispatched for alert {self.current_alert_id}")
                else:
                    print(f"❌ Failed to dispatch emergency services for alert {self.current_alert_id}")
                    
            except Exception as e:
                print(f"❌ Error dispatching emergency services: {e}")
        else:
            print(f"⚠️ No backend connection or alert ID available for dispatch")
        
        # Emit signal to parent widget
        self.dispatch_clicked.emit(self.camera_id, clip_id)
        
        # Close detection mode after dispatch
        self.close_detection_mode()
        
    def mark_false_alert(self):
        """Handle false alert button click"""
        current_frame_data = self.fire_detected_frames[self.current_frame_index]
        clip_id = current_frame_data.get('clip_id', 'unknown')
        
        # If we have a backend connection and alert ID, mark as false alarm
        if self.fire_detection_backend and self.current_alert_id:
            try:
                success = self.fire_detection_backend.mark_false_alarm(
                    alert_id=self.current_alert_id,
                    resolved_by="user",
                    resolution_notes=f"Marked as false alarm from camera {self.camera_id}"
                )
                
                if success:
                    print(f"✅ Fire alert {self.current_alert_id} marked as false alarm")
                    # Show success message
                    QMessageBox.information(self, "False Alarm Marked", 
                                          "Alert has been marked as false alarm successfully!")
                else:
                    print(f"❌ Failed to mark alert {self.current_alert_id} as false alarm")
                    QMessageBox.warning(self, "False Alarm Failed", 
                                      "Failed to mark as false alarm. Please try again.")
                    
            except Exception as e:
                print(f"❌ Error marking false alarm: {e}")
                QMessageBox.critical(self, "False Alarm Error", 
                                   f"Error marking false alarm: {e}")
        else:
            print(f"⚠️ No backend connection or alert ID available for false alarm")
            QMessageBox.warning(self, "False Alarm Unavailable", 
                              "Backend connection not available. Cannot mark as false alarm.")
        
        # Emit signal to parent widget
        self.false_alert_clicked.emit(self.camera_id, clip_id)
        
        # Close detection mode after marking false alert
        self.close_detection_mode()
        
    def close_detection_mode(self):
        """Close fire detection mode and reset state"""
        self.detection_active = False
        self.fire_detected_frames = []
        self.current_frame_index = 0
        self.current_alert_id = None  # Reset alert ID
        
        # Stop alarm audio if playing
        try:
            if self.alarm_player.state() == QMediaPlayer.PlayingState:
                self.alarm_player.stop()
                print("🔇 Stopped alarm audio")
        except Exception as e:
            print(f"❌ Error stopping alarm audio: {e}")
        
        # Hide UI elements
        self.alert_header.hide()
        self.frame_label.hide()
        self.controls_widget.hide()
        
        # Reset parent widget fire detection state
        parent_widget = self.parent()
        while parent_widget and not hasattr(parent_widget, 'fire_detection_active'):
            parent_widget = parent_widget.parent()
        
        if parent_widget and hasattr(parent_widget, 'fire_detection_active'):
            parent_widget.fire_detection_active = False
            parent_widget.fire_detection_frames = []
            parent_widget.current_alert_id = None  # Reset alert ID in parent widget
        
        print("🔥 Fire detection mode closed")

    def update_auto_countdown(self, seconds_remaining: float, active: bool = True):
        """Update or hide the auto-alarm countdown label in the header."""
        try:
            if active and seconds_remaining is not None:
                secs = max(0.0, float(seconds_remaining))
                self.countdown_label.setText(f"Auto alarm in: {secs:.1f}s")
                # Emphasize when < 2s
                if secs <= 2.0:
                    self.countdown_label.setStyleSheet("color: #ffff00; font-size: 11px; font-weight: bold; background: transparent;")
                else:
                    self.countdown_label.setStyleSheet("color: white; font-size: 11px; font-weight: bold; background: transparent;")
                self.countdown_label.show()
            else:
                self.countdown_label.hide()
        except Exception:
            pass

    def start_auto_alarm(self):
        """Start playing the alarm audio without dialogs (auto mode)."""
        try:
            if self.alarm_player.mediaStatus() == QMediaPlayer.LoadedMedia:
                if self.alarm_player.state() != QMediaPlayer.PlayingState:
                    self.alarm_player.play()
                    print("🔊 Auto alarm started")
            else:
                print("⚠️ Auto alarm could not start, audio not loaded")
        except Exception as e:
            print(f"❌ Error starting auto alarm: {e}")

    def set_alert_id(self, alert_id):
        """Set the current alert ID for backend communication"""
        self.current_alert_id = alert_id
        print(f"📋 Alert ID set: {alert_id}")
    
    def stop_alarm_audio(self):
        """Manually stop the alarm audio"""
        try:
            if self.alarm_player.state() == QMediaPlayer.PlayingState:
                self.alarm_player.stop()
                print("🔇 Alarm audio stopped manually")
        except Exception as e:
            print(f"❌ Error stopping alarm audio: {e}")
    
    def set_alarm_volume(self, volume):
        """Set the alarm audio volume (0-100)"""
        try:
            self.alarm_player.setVolume(volume)
            print(f"🔊 Alarm volume set to: {volume}%")
        except Exception as e:
            print(f"❌ Error setting alarm volume: {e}")
    
    def test_alarm_audio(self):
        """Test the alarm audio playback"""
        try:
            # Check if audio is loaded, if not try to reload
            if self.alarm_player.mediaStatus() != QMediaPlayer.LoadedMedia:
                print("🔄 Reloading alarm audio...")
                self.load_alarm_audio()
            
            if self.alarm_player.mediaStatus() == QMediaPlayer.LoadedMedia:
                # Stop any currently playing audio first
                if self.alarm_player.state() == QMediaPlayer.PlayingState:
                    self.alarm_player.stop()
                
                # Play the alarm audio
                self.alarm_player.play()
                print("🔊 Testing alarm audio")
                
                # Show a brief message
                QMessageBox.information(self, "Alarm Test", 
                                      "Alarm audio is playing. Click OK to stop.")
                
                # Stop the audio when dialog is closed
                self.alarm_player.stop()
                
            else:
                QMessageBox.warning(self, "Audio Not Loaded", 
                                  "Alarm audio file is not loaded properly.\n\n"
                                  f"Expected path: {self.alarm_audio_path}\n"
                                  "Please ensure the fire_alarm.mp3 file exists in the assets/audio folder.")
        except Exception as e:
            print(f"❌ Error testing alarm audio: {e}")
            QMessageBox.critical(self, "Audio Error", 
                               f"Error testing alarm audio: {e}")
    
    def reload_alarm_audio(self):
        """Reload the alarm audio file"""
        try:
            self.load_alarm_audio()
            if self.alarm_player.mediaStatus() == QMediaPlayer.LoadedMedia:
                QMessageBox.information(self, "Audio Reloaded", 
                                      "Alarm audio has been reloaded successfully!")
            else:
                QMessageBox.warning(self, "Reload Failed", 
                                  "Failed to reload alarm audio file.")
        except Exception as e:
            print(f"❌ Error reloading alarm audio: {e}")
            QMessageBox.critical(self, "Reload Error", 
                               f"Error reloading alarm audio: {e}")
    
    def show_audio_context_menu(self, position):
        """Show context menu for audio controls"""
        from PyQt5.QtWidgets import QMenu
        
        context_menu = QMenu(self)
        
        # Test audio action
        test_action = context_menu.addAction("🔊 Test Alarm Audio")
        test_action.triggered.connect(self.test_alarm_audio)
        
        # Reload audio action
        reload_action = context_menu.addAction("🔄 Reload Audio File")
        reload_action.triggered.connect(self.reload_alarm_audio)
        
        context_menu.addSeparator()
        
        # Volume control submenu
        volume_menu = context_menu.addMenu("🔊 Volume Control")
        
        volume_levels = [("Mute", 0), ("Low (25%)", 25), ("Medium (50%)", 50), 
                        ("High (75%)", 75), ("Full (100%)", 100)]
        
        for label, volume in volume_levels:
            action = volume_menu.addAction(label)
            action.triggered.connect(lambda checked, vol=volume: self.set_alarm_volume(vol))
        
        context_menu.addSeparator()
        
        # Audio info action
        info_action = context_menu.addAction("ℹ️ Audio Info")
        info_action.triggered.connect(self.show_audio_info)
        
        # Show the context menu
        context_menu.exec_(self.test_alarm_btn.mapToGlobal(position))
    
    def show_audio_info(self):
        """Show information about the loaded audio file"""
        try:
            status = self.alarm_player.mediaStatus()
            state = self.alarm_player.state()
            volume = self.alarm_player.volume()
            
            status_text = {
                QMediaPlayer.UnknownMediaStatus: "Unknown",
                QMediaPlayer.NoMedia: "No Media",
                QMediaPlayer.LoadingMedia: "Loading",
                QMediaPlayer.LoadedMedia: "Loaded",
                QMediaPlayer.StalledMedia: "Stalled",
                QMediaPlayer.BufferingMedia: "Buffering",
                QMediaPlayer.BufferedMedia: "Buffered",
                QMediaPlayer.EndOfMedia: "End of Media",
                QMediaPlayer.InvalidMedia: "Invalid Media"
            }.get(status, "Unknown")
            
            state_text = {
                QMediaPlayer.StoppedState: "Stopped",
                QMediaPlayer.PlayingState: "Playing",
                QMediaPlayer.PausedState: "Paused"
            }.get(state, "Unknown")
            
            info_text = f"""
Audio File Information:
• File Path: {self.alarm_audio_path}
• File Exists: {'Yes' if os.path.exists(self.alarm_audio_path) else 'No'}
• Media Status: {status_text}
• Player State: {state_text}
• Volume: {volume}%
• File Size: {self.get_file_size()}
            """
            
            QMessageBox.information(self, "Audio Information", info_text.strip())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error getting audio info: {e}")
    
    def get_file_size(self):
        """Get the size of the audio file"""
        try:
            if os.path.exists(self.alarm_audio_path):
                size_bytes = os.path.getsize(self.alarm_audio_path)
                if size_bytes < 1024:
                    return f"{size_bytes} bytes"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return "File not found"
        except Exception:
            return "Unknown"


class EnhancedFullScreenCameraWidget(QWidget):
    def on_auto_fire_alarm(self):
        """Auto fire alarm: 5s countdown, then buzzer and pump ON."""
        if hasattr(self, 'fire_detection_widget') and self.fire_detection_widget:
            self.fire_detection_widget.update_auto_countdown(3.0, active=True)
            QTimer.singleShot(3000, self._auto_alarm_and_pump)

    def _auto_alarm_and_pump(self):
        if hasattr(self, 'fire_detection_widget') and self.fire_detection_widget:
            self.fire_detection_widget.start_auto_alarm()
        self._trigger_pump_on_if_configured()
        self._trigger_fan_on_if_configured()
    """Enhanced full-screen camera widget with side panel design and complete functionality"""
    
    back_clicked = pyqtSignal()
    
    def __init__(self, camera_id, camera_name, clip_manager, fire_detection_backend=None, notification_manager=None):

        super().__init__()
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.clip_manager = clip_manager
        self.fire_detection_backend = fire_detection_backend
        self.notification_manager = notification_manager

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
        
        # Fire detection optimization
        self.fire_detection_frames = []  # Store frames with fire detections
        self.fire_detection_active = False
        self.fire_detection_threshold = 0.7  # Higher threshold for frame-by-frame mode
        self.current_alert_id = None  # Store the current alert ID
        
        # Initialize detection states
        self.people_detection_enabled = False
        self.fire_smoke_detection_enabled = False
        
        self.detections = []
        self.fire_smoke_detections = []
        self.fire_smoke_alert_info = {}
        self.fire_smoke_last_update = 0.0  # timestamp of last fire/smoke detections update
        self.auto_alarm_threshold_seconds = 3.0
        self.fire_continuous_start_time = None
        self.auto_alarm_triggered = False
        self.fire_overlay_info = None
        # ESP32 pump and fan control
        self.esp32_base_url = None
        self._pump_on_sent = False
        self._fan_on_sent = False
        
        # Force display to grayscale (user Night Mode toggle)
        self.force_grayscale = False
        
        # Recording variables
        self.video_writer = None
        self.recording_start_time = None
        self.recording_filename = None
        
        # AI Review System components
        self.panic_detector = PanicBehaviorDetector()
        self.review_widget = None
        self.panic_behaviors = []
        self.active_event_recording = None
        
        # Detection system references
        self.people_detector = None
        self.fire_smoke_detector = None
        self.camera_manager = None
        
        # Connect signals
        self.panic_detector.panic_detected.connect(self.on_panic_detected)
        self.clip_manager.clip_created.connect(self.on_clip_created)
        
        if self.camera_manager:
            self.people_detection_enabled = self.camera_manager.is_people_detection_enabled(self.camera_id)
            self.fire_smoke_detection_enabled = self.camera_manager.is_fire_smoke_detection_enabled(self.camera_id)
        
        self.setup_ui()
        self._update_detection_button_states()

        
        # Timer for auto-recording duration
        self.auto_record_timer = QTimer(self)
        self.auto_record_timer.setSingleShot(True)
        self.auto_record_timer.timeout.connect(self.on_auto_record_timeout)
        self.current_auto_recording_clip_id = None
        
        # Enable panic detection by default
        self.panic_detector.enable_detection(self.camera_id, True)
        
        # Clip playback variables
        self.clip_playback_cap = None
        self.clip_playback_timer = QTimer()
        self.clip_playback_timer.timeout.connect(self._playback_next_clip_frame)
        self.is_clip_playing = False
        self.clip_playback_fps = 25  # Default fallback FPS
        self.clip_is_paused = False
        self.clip_current_frame_pos = 0
        self.clip_total_frames = 0
        
    def set_detection_systems(self, people_detector=None, fire_smoke_detector=None, camera_manager=None):
        """Set references to the detection systems and update initial states"""
        self.people_detector = people_detector
        self.fire_smoke_detector = fire_smoke_detector
        self.camera_manager = camera_manager
        
        # Update initial state of detection buttons based on camera_manager
        if self.camera_manager:
            self.people_detection_enabled = self.camera_manager.is_people_detection_enabled(self.camera_id)
            self.fire_smoke_detection_enabled = self.camera_manager.is_fire_smoke_detection_enabled(self.camera_id)
        
        self._update_detection_button_states() # Update UI elements
        
    def set_button_icon(self, button, icon_path, fallback_text):
        """Set icon for button with fallback to text"""
        try:
            if os.path.exists(icon_path):
                # Try to load the icon
                icon = QIcon(icon_path)
                
                # Check if icon loaded successfully
                if not icon.isNull() and len(icon.availableSizes()) > 0:
                    button.setIcon(icon)
                    button.setIconSize(QSize(32, 32))  # Increased to 32x32 for better visibility
                    button.setText("")
                    print(f"✅ Icon set successfully: {icon_path} (sizes: {icon.availableSizes()})")
                else:
                    # Icon failed to load, use fallback
                    button.setText(fallback_text)
                    button.setIcon(QIcon())
                    print(f"⚠️ Icon loaded but empty, using fallback: {icon_path}")
            else:
                button.setText(fallback_text)
                button.setIcon(QIcon())
                print(f"❌ Icon file not found, using fallback: {icon_path}")
        except Exception as e:
            print(f"❌ Error setting button icon {icon_path}: {e}")
            button.setText(fallback_text)
            button.setIcon(QIcon())
        
    def setup_ui(self):
        """Setup the enhanced UI with side panel only"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left side - Video display and controls
        self.video_widget = self.create_video_widget()
        layout.addWidget(self.video_widget, 3)  # 75% of width
        
        # Right side - Side panel (always visible)
        self.side_panel = self.create_side_panel()
        layout.addWidget(self.side_panel, 1)  # 25% of width
        
    def create_video_widget(self):
        """Create the main video display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
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
        # Removed mousePressEvent connection - no more click to hide
        layout.addWidget(self.video_label, 1)
        
        # Bottom control bar
        self.create_bottom_controls(layout)
        
        return widget
        
    def create_side_panel(self):
        """Create the side panel with all detection and clip features"""
        panel = QWidget()
        panel.setFixedWidth(400)
        panel.setStyleSheet("""
            QWidget {
                background-color: #141414;
                border-left: 1px solid #333333;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Panel header
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border-bottom: 2px solid #1a1a1a;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(5)
        
        # Top row: FV logo and title
        top_row = QWidget()
        top_row_layout = QHBoxLayout(top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(10)
        
        # FV logo
        fv_logo = QLabel()
        logo_pixmap = QPixmap(resource_path("assests/logo/fv_logo-removebg-preview.png"))
        if not logo_pixmap.isNull():
            fv_logo.setPixmap(logo_pixmap.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        fv_logo.setStyleSheet("background: transparent;")
        
        # AI ANALYSIS MONITOR title
        title_label = QLabel("AI ANALYSIS MONITOR")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        
        top_row_layout.addWidget(fv_logo)
        top_row_layout.addWidget(title_label)
        top_row_layout.addStretch()
        
        # Bottom row: Live Analysis status
        bottom_row = QWidget()
        bottom_row_layout = QHBoxLayout(bottom_row)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        
        live_label = QLabel("Live Analysis:")
        live_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                background: transparent;
            }
        """)
        
        # Status indicators
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(15)
        
        # Play/Pause indicator
        play_indicator = QLabel("▶")
        play_indicator.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        # Forward indicator
        forward_indicator = QLabel("▶")
        forward_indicator.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 12px;
                background: transparent;
            }
        """)
        
        status_layout.addWidget(play_indicator)
        status_layout.addWidget(forward_indicator)
        
        bottom_row_layout.addWidget(live_label)
        bottom_row_layout.addWidget(status_widget)
        bottom_row_layout.addStretch()
        
        header_layout.addWidget(top_row)
        header_layout.addWidget(bottom_row)
        
        # Tabs for different features
        self.side_tabs = QTabWidget()
        self.side_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #505050;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: white;
                padding: 8px 12px;
                margin-right: 2px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #ff3333;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """)
        
        # Live Analysis Tab
        self.live_analysis_tab = self.create_live_analysis_tab()
        self.side_tabs.addTab(self.live_analysis_tab, "📊 Live Analysis")
        
        # Fire Detection Tab
        self.fire_detection_widget = FireDetectionSidePanelWidget(self.camera_id, self.camera_name, self.fire_detection_backend, self.notification_manager)
        self.fire_detection_widget.dispatch_clicked.connect(self.on_dispatch_clicked)
        self.fire_detection_widget.false_alert_clicked.connect(self.on_false_alert_clicked)
        self.side_tabs.addTab(self.fire_detection_widget, "🔥 Fire Detection")
        
        # Event Clips Tab
        self.event_clips_tab = self.create_event_clips_tab()
        self.side_tabs.addTab(self.event_clips_tab, "🎬 Event Clips")
        
        # Panic Detection Tab
        self.panic_detection_tab = self.create_panic_detection_tab()
        self.side_tabs.addTab(self.panic_detection_tab, "😰 Panic Detection")
        
        # Timeline Tab
        self.timeline_widget = ThumbnailTimelineWidget(self.clip_manager, self.camera_id)
        self.timeline_widget.thumbnail_clicked.connect(self.on_thumbnail_clicked)
        self.side_tabs.addTab(self.timeline_widget, "📹 Timeline")
        
        layout.addWidget(header)
        layout.addWidget(self.side_tabs)
        
        return panel
        
    def create_live_analysis_tab(self):
        """Create live analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Current detections display
        detections_group = QGroupBox("Current Detections")
        detections_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        detections_layout = QVBoxLayout(detections_group)
        
        # Fire/Smoke status
        self.fire_smoke_status = QLabel("🔥 Fire/Smoke: None detected")
        self.fire_smoke_status.setStyleSheet("color: #00ff00; font-size: 11px;")
        
        # People count status
        self.people_status = QLabel("👥 People: 0 detected")
        self.people_status.setStyleSheet("color: #00ff00; font-size: 11px;")
        
        # Panic behavior status
        self.panic_status = QLabel("😰 Panic Behaviors: None detected")
        self.panic_status.setStyleSheet("color: #00ff00; font-size: 11px;")
        
        detections_layout.addWidget(self.fire_smoke_status)
        detections_layout.addWidget(self.people_status)
        detections_layout.addWidget(self.panic_status)
        
        # Auto-recording controls
        recording_group = QGroupBox("Auto Event Recording")
        recording_group.setStyleSheet(detections_group.styleSheet())
        recording_layout = QVBoxLayout(recording_group)
        
        self.auto_record_checkbox = QCheckBox("Enable automatic event recording")
        self.auto_record_checkbox.setChecked(True)
        self.auto_record_checkbox.setStyleSheet("color: white; font-size: 11px;")
        
        clip_duration_layout = QHBoxLayout()
        clip_duration_layout.addWidget(QLabel("Clip Duration:"))
        self.clip_duration_spin = QSpinBox()
        self.clip_duration_spin.setRange(10, 60)
        self.clip_duration_spin.setValue(15)
        self.clip_duration_spin.setSuffix(" seconds")
        self.clip_duration_spin.setStyleSheet("font-size: 11px;")
        clip_duration_layout.addWidget(self.clip_duration_spin)
        clip_duration_layout.addStretch()
        
        recording_layout.addWidget(self.auto_record_checkbox)
        recording_layout.addLayout(clip_duration_layout)
        
        # Detection sensitivity controls
        sensitivity_group = QGroupBox("Detection Sensitivity")
        sensitivity_group.setStyleSheet(detections_group.styleSheet())
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        
        # Fire detection threshold
        fire_threshold_layout = QHBoxLayout()
        fire_threshold_layout.addWidget(QLabel("Fire Threshold:"))
        self.fire_threshold_slider = QSlider(Qt.Horizontal)
        self.fire_threshold_slider.setRange(50, 95)
        self.fire_threshold_slider.setValue(int(self.fire_detection_threshold * 100))
        self.fire_threshold_slider.valueChanged.connect(self.update_fire_threshold)
        self.fire_threshold_value = QLabel(f"{int(self.fire_detection_threshold * 100)}%")
        self.fire_threshold_value.setStyleSheet("color: white; font-size: 10px;")
        fire_threshold_layout.addWidget(self.fire_threshold_slider)
        fire_threshold_layout.addWidget(self.fire_threshold_value)
        
        sensitivity_layout.addLayout(fire_threshold_layout)
        
        # Event log
        log_group = QGroupBox("Recent Events")
        log_group.setStyleSheet(detections_group.styleSheet())
        log_layout = QVBoxLayout(log_group)
        
        self.event_log = QTextEdit()
        self.event_log.setMaximumHeight(150)
        self.event_log.setReadOnly(True)
        self.event_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                font-size: 10px;
            }
        """)
        
        log_layout.addWidget(self.event_log)
        
        layout.addWidget(detections_group)
        layout.addWidget(recording_group)
        layout.addWidget(sensitivity_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        return tab
    
    def create_event_clips_tab(self):
        """Create event clips review tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Filter controls
        filter_group = QGroupBox("Filter Events")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 12px;
            }
        """)
        filter_layout = QVBoxLayout(filter_group)
        
        # Event type filter
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.event_filter_combo = QComboBox()
        self.event_filter_combo.addItems([
            "All Events", "Fire Only", "Smoke Only", "Panic Only", "Combined"
        ])
        self.event_filter_combo.currentTextChanged.connect(self.filter_event_clips)
        self.event_filter_combo.setStyleSheet("font-size: 11px;")
        type_layout.addWidget(self.event_filter_combo)
        type_layout.addStretch()
        
        filter_layout.addLayout(type_layout)
        
        # Clips list
        clips_group = QGroupBox("Event Clips")
        clips_group.setStyleSheet(filter_group.styleSheet())
        clips_layout = QVBoxLayout(clips_group)
        
        self.clips_list = QListWidget()
        self.clips_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #505050;
                color: white;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QListWidget::item:selected {
                background-color: #ff3333;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        self.clips_list.itemDoubleClicked.connect(self.play_event_clip)
        
        clips_layout.addWidget(self.clips_list)
        
        # Clip actions
        actions_layout = QHBoxLayout()
        
        play_clip_btn = QPushButton("▶️ Play")
        play_clip_btn.clicked.connect(self.play_selected_clip)
        play_clip_btn.setStyleSheet("font-size: 10px; padding: 5px 10px;")
        
        export_clip_btn = QPushButton("📤 Export")
        export_clip_btn.clicked.connect(self.export_selected_clip)
        export_clip_btn.setStyleSheet("font-size: 10px; padding: 5px 10px;")
        
        delete_clip_btn = QPushButton("🗑️ Delete")
        delete_clip_btn.clicked.connect(self.delete_selected_clip)
        delete_clip_btn.setStyleSheet("QPushButton { background-color: #aa0000; font-size: 10px; padding: 5px 10px; }")
        
        actions_layout.addWidget(play_clip_btn)
        actions_layout.addWidget(export_clip_btn)
        actions_layout.addWidget(delete_clip_btn)
        actions_layout.addStretch()
        
        layout.addWidget(filter_group)
        layout.addWidget(clips_group)
        layout.addLayout(actions_layout)
        
        return tab
    
    def create_panic_detection_tab(self):
        """Create panic detection configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Panic detection settings
        settings_group = QGroupBox("Panic Detection Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 12px;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)
        
        # Enable/disable panic detection
        self.panic_detection_checkbox = QCheckBox("Enable Panic Behavior Detection")
        self.panic_detection_checkbox.setChecked(True)
        self.panic_detection_checkbox.setStyleSheet("color: white; font-size: 11px;")
        self.panic_detection_checkbox.toggled.connect(self.toggle_panic_detection)
        
        # Sensitivity settings
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_value = QLabel("5")
        self.sensitivity_value.setStyleSheet("color: white; font-size: 11px;")
        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_value)
        sensitivity_layout.addStretch()
        
        self.sensitivity_slider.valueChanged.connect(
            lambda v: self.sensitivity_value.setText(str(v))
        )
        
        # Behavior types to detect
        behaviors_layout = QVBoxLayout()
        behaviors_layout.addWidget(QLabel("Detect Behaviors:"))
        
        self.detect_running = QCheckBox("Running/Rapid Movement")
        self.detect_running.setChecked(True)
        self.detect_running.setStyleSheet("color: white; font-size: 11px;")
        
        self.detect_falling = QCheckBox("Falling")
        self.detect_falling.setChecked(True)
        self.detect_falling.setStyleSheet("color: white; font-size: 11px;")
        
        self.detect_erratic = QCheckBox("Erratic Movement")
        self.detect_erratic.setChecked(True)
        self.detect_erratic.setStyleSheet("color: white; font-size: 11px;")
        
        self.detect_crowd_panic = QCheckBox("Crowd Panic")
        self.detect_crowd_panic.setChecked(True)
        self.detect_crowd_panic.setStyleSheet("color: white; font-size: 11px;")
        
        behaviors_layout.addWidget(self.detect_running)
        behaviors_layout.addWidget(self.detect_falling)
        behaviors_layout.addWidget(self.detect_erratic)
        behaviors_layout.addWidget(self.detect_crowd_panic)
        
        settings_layout.addWidget(self.panic_detection_checkbox)
        settings_layout.addLayout(sensitivity_layout)
        settings_layout.addLayout(behaviors_layout)
        
        # Recent panic behaviors
        recent_group = QGroupBox("Recent Panic Behaviors")
        recent_group.setStyleSheet(settings_group.styleSheet())
        recent_layout = QVBoxLayout(recent_group)
        
        self.panic_behaviors_list = QListWidget()
        self.panic_behaviors_list.setMaximumHeight(150)
        self.panic_behaviors_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #505050;
                color: white;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #505050;
            }
        """)
        
        recent_layout.addWidget(self.panic_behaviors_list)
        
        layout.addWidget(settings_group)
        layout.addWidget(recent_group)
        layout.addStretch()
        
        return tab
    
    def create_top_controls(self, layout):
        """Create top control bar with AI review toggle"""
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(100)
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
        
        # Panic behavior alert display
        self.panic_alert_display = QLabel("😰 PANIC DETECTED!")
        self.panic_alert_display.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                background: rgba(255, 165, 0, 200);
                padding: 8px 15px;
                border: 3px solid #ffaa00;
                border-radius: 8px;
            }
        """)
        self.panic_alert_display.hide()
        
        detection_displays_layout.addWidget(self.people_count_display)
        detection_displays_layout.addWidget(self.fire_smoke_alert_display)
        detection_displays_layout.addWidget(self.panic_alert_display)
        
        status_layout.addWidget(top_status_widget)
        status_layout.addWidget(detection_displays_widget)
        
        # Back to Live button
        self.back_to_live_btn = QPushButton("⏮ Back to Live")
        self.back_to_live_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffaa00;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffcc66;
            }
        """)
        self.back_to_live_btn.clicked.connect(self.stop_clip_playback_and_return_to_live)
        self.back_to_live_btn.hide()
        
        top_layout.addWidget(back_btn)
        top_layout.addWidget(info_widget)
        top_layout.addStretch()
        top_layout.addWidget(status_container)
        top_layout.addWidget(self.back_to_live_btn)
        
        layout.addWidget(self.top_bar)
        
    def create_bottom_controls(self, layout):
        """Create complete bottom controls with improved horizontal layout"""
        self.bottom_bar = QWidget()
        self.bottom_bar.setFixedHeight(100)
        self.bottom_bar.setStyleSheet("""
            QWidget {
                background-color: #00000;
                border-top: 1px solid #333333;
            }
        """)
        
        main_layout = QHBoxLayout(self.bottom_bar)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(25)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Playback controls
        playback_group = self.create_playback_controls()
        main_layout.addWidget(playback_group)
        
        # Separator (hidden/transparent)
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("QFrame { color: transparent; border: none; }")
        main_layout.addWidget(separator1)
        
        # Detection controls
        detection_group = self.create_detection_controls()
        main_layout.addWidget(detection_group)
        
        # Separator (hidden/transparent)
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("QFrame { color: transparent; border: none; }")
        main_layout.addWidget(separator2)
        
        # Recording controls
        recording_group = self.create_recording_controls()
        main_layout.addWidget(recording_group)
        
        # Separator (hidden/transparent)
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setStyleSheet("QFrame { color: transparent; border: none; }")
        main_layout.addWidget(separator3)
        
        # View controls
        view_group = self.create_view_controls()
        main_layout.addWidget(view_group)
        
        # Add stretch to push everything to the left
        main_layout.addStretch()
        
        # Timeline/scrubber (if in playback mode) - moved to top bar or separate area
        # Removed from bottom bar for cleaner layout
        
        layout.addWidget(self.bottom_bar)
    
    def create_playback_controls(self):
        """Create playback control group with icon buttons"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)
        
        # Button style for icon buttons
        icon_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            QPushButton:disabled {
                opacity: 0.3;
            }
        """
        
        # Frame-by-frame controls
        self.frame_back_btn = QPushButton()
        self.frame_back_btn.setFixedSize(44, 44)
        self.frame_back_btn.setStyleSheet(icon_button_style)
        self.frame_back_btn.clicked.connect(self.step_frame_backward)
        self.frame_back_btn.setEnabled(False)
        self.set_button_icon(self.frame_back_btn, resource_path("assests/icons/fullscreen_sidebar/backward.png"), "⏮️")

        # Play/Pause button
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(44, 44)
        self.play_pause_btn.setStyleSheet(icon_button_style)
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        pause_icon = resource_path("assests/icons/fullscreen_sidebar/pause.png") if self.is_playing else resource_path("assests/icons/play.png")
        pause_fallback = "⏸️" if self.is_playing else "▶️"
        self.set_button_icon(self.play_pause_btn, pause_icon, pause_fallback)

        self.frame_forward_btn = QPushButton()
        self.frame_forward_btn.setFixedSize(44, 44)
        self.frame_forward_btn.setStyleSheet(icon_button_style)
        self.frame_forward_btn.clicked.connect(self.step_frame_forward)
        self.frame_forward_btn.setEnabled(False)
        self.set_button_icon(self.frame_forward_btn, resource_path("assests/icons/fullscreen_sidebar/forward.png"), "⏭️")
    
        layout.addWidget(self.frame_back_btn)
        layout.addWidget(self.play_pause_btn)
        layout.addWidget(self.frame_forward_btn)
    
        return group

    def create_detection_controls(self):
        """Create detection control group with icon buttons"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)
        
        # Toggle button style for detection controls
        toggle_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:checked {
                background-color: rgba(0, 255, 0, 30);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
            QPushButton::icon {
                width: 36px;
                height: 36px;
            }
        """
    
        # People detection toggle
        self.people_detection_btn = QPushButton()
        self.people_detection_btn.setCheckable(True)
        self.people_detection_btn.setChecked(self.people_detection_enabled)
        self.people_detection_btn.setFixedSize(44, 44)
        self.people_detection_btn.setStyleSheet(toggle_button_style)
        self.people_detection_btn.clicked.connect(self.toggle_people_detection)
        self.set_button_icon(self.people_detection_btn, resource_path("assests/icons/fullscreen_sidebar/people_detection.png"), "👥")
    
        # Fire/Smoke detection toggle
        self.fire_smoke_detection_btn = QPushButton()
        self.fire_smoke_detection_btn.setCheckable(True)
        self.fire_smoke_detection_btn.setChecked(self.fire_smoke_detection_enabled)
        self.fire_smoke_detection_btn.setFixedSize(44, 44)
        self.fire_smoke_detection_btn.setStyleSheet(toggle_button_style)
        self.fire_smoke_detection_btn.clicked.connect(self.toggle_fire_smoke_detection)
        self.set_button_icon(self.fire_smoke_detection_btn, resource_path("assests/icons/fullscreen_sidebar/fire_detection.png"), "🔥")
    
        layout.addWidget(self.people_detection_btn)
        layout.addWidget(self.fire_smoke_detection_btn)
    
        return group

    def create_recording_controls(self):
        """Create recording control group with icon buttons"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)
        
        # Record button style
        record_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 30);
            }
        """
        
        # Auto-record toggle style
        auto_record_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:checked {
                background-color: rgba(255, 165, 0, 30);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """
    
        # Record button
        self.record_btn = QPushButton()
        self.record_btn.setFixedSize(44, 44)
        self.record_btn.setStyleSheet(record_button_style)
        self.record_btn.clicked.connect(self.toggle_recording)
        record_icon = resource_path("assests/icons/stop.png") if self.is_recording else resource_path("assests/icons/fullscreen_sidebar/record.png")
        record_fallback = "⏹" if self.is_recording else "⏺"
        self.set_button_icon(self.record_btn, record_icon, record_fallback)
    
        # Auto-record toggle
        self.auto_record_btn = QPushButton()
        self.auto_record_btn.setCheckable(True)
        self.auto_record_btn.setChecked(True)
        self.auto_record_btn.setFixedSize(44, 44)
        self.auto_record_btn.setStyleSheet(auto_record_style)
        self.set_button_icon(self.auto_record_btn, resource_path("assests/icons/auto.png"), "🤖")
    
        layout.addWidget(self.record_btn)
        layout.addWidget(self.auto_record_btn)
    
        return group

    def create_view_controls(self):
        """Create view control group with icon buttons"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon button style
        icon_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """
        
        # Pump button style (toggleable)
        pump_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 255, 30);
            }
        """
        
        # Fan button style (toggleable)
        fan_button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: rgba(100, 200, 255, 30);
            }
        """
        
        # Zoom controls
        zoom_out_btn = QPushButton()
        zoom_out_btn.setFixedSize(44, 44)
        zoom_out_btn.setStyleSheet(icon_button_style)
        zoom_out_btn.clicked.connect(self.zoom_out)
        self.set_button_icon(zoom_out_btn, resource_path("assests/icons/zoom_out.png"), "🔍")
        
        zoom_in_btn = QPushButton()
        zoom_in_btn.setFixedSize(44, 44)
        zoom_in_btn.setStyleSheet(icon_button_style)
        zoom_in_btn.clicked.connect(self.zoom_in)
        self.set_button_icon(zoom_in_btn, resource_path("assests/icons/zoom_in.png"), "🔎")
        
        # Pump toggle
        self.pump_toggle_btn = QPushButton()
        self.pump_toggle_btn.setFixedSize(44, 44)
        self.pump_toggle_btn.setStyleSheet(pump_button_style)
        self.pump_toggle_btn.clicked.connect(self.toggle_pump)
        self.set_button_icon(self.pump_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/water_pump.png"), "💧")
        
        # Fan toggle
        self.fan_toggle_btn = QPushButton()
        self.fan_toggle_btn.setFixedSize(44, 44)
        self.fan_toggle_btn.setStyleSheet(fan_button_style)
        self.fan_toggle_btn.clicked.connect(self.toggle_fan)
        self.set_button_icon(self.fan_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/fan.png"), "🌀")
        
        layout.addWidget(zoom_out_btn)
        layout.addWidget(zoom_in_btn)
        layout.addWidget(self.pump_toggle_btn)
        layout.addWidget(self.fan_toggle_btn)
        
        # Update button states
        self._update_pump_button_ui()
        self._update_fan_button_ui()
    
        return group

    def toggle_playback(self):
        """Toggle playback state (live or recorded)."""
        if self.is_clip_playing:
            self.clip_is_paused = not self.clip_is_paused
            if self.clip_is_paused:
                self.set_button_icon(self.play_pause_btn, resource_path("assests/icons/play.png"), "▶️")
                self.clip_playback_timer.stop()
            else:
                self.set_button_icon(self.play_pause_btn, resource_path("assests/icons/fullscreen_sidebar/pause.png"), "⏸️")
                interval = int(1000 / (self.clip_playback_fps * self.playback_speed))
                self.clip_playback_timer.start(interval)
        else:
            # Live mode
            self.is_playing = not self.is_playing
            if self.is_playing:
                self.set_button_icon(self.play_pause_btn, resource_path("assests/icons/fullscreen_sidebar/pause.png"), "⏸️")
                self.status_label.setText("● LIVE")
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
            else:
                self.set_button_icon(self.play_pause_btn, resource_path("assests/icons/play.png"), "▶️")
                self.status_label.setText("⏸ PAUSED")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #ffaa00;
                        font-size: 14px;
                        font-weight: bold;
                        background: transparent;
                        padding: 3px 8px;
                        border: 1px solid #ffaa00;
                        border-radius: 4px;
                    }
                """)

    def step_frame_forward(self):
        """Step forward one frame in recorded playback."""
        if self.is_clip_playing and self.clip_is_paused and self.clip_playback_cap:
            next_pos = min(self.clip_current_frame_pos + 1, self.clip_total_frames - 1)
            self.clip_playback_cap.set(cv2.CAP_PROP_POS_FRAMES, next_pos)
            ret, frame = self.clip_playback_cap.read()
            if ret:
                self.clip_current_frame_pos = next_pos
                self.display_frame(frame)

    def step_frame_backward(self):
        """Step backward one frame in recorded playback."""
        if self.is_clip_playing and self.clip_is_paused and self.clip_playback_cap:
            prev_pos = max(self.clip_current_frame_pos - 2, 0)  # -2 because after set, read() advances one
            self.clip_playback_cap.set(cv2.CAP_PROP_POS_FRAMES, prev_pos)
            ret, frame = self.clip_playback_cap.read()
            if ret:
                self.clip_current_frame_pos = prev_pos + 1
                self.display_frame(frame)

    def stop_clip_playback_and_return_to_live(self):
        """Stop clip playback and return to live mode."""
        if self.clip_playback_cap:
            self.clip_playback_timer.stop()
            self.clip_playback_cap.release()
            self.clip_playback_cap = None
        self.is_clip_playing = False
        self.clip_is_paused = False
        self.frame_back_btn.setEnabled(False)
        self.frame_forward_btn.setEnabled(False)
        self.status_label.setText("● LIVE")
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
        self.back_to_live_btn.hide()
        # Optionally, refresh the live frame
        if self.current_frame is not None:
            self.display_frame(self.current_frame)

    def change_playback_speed(self, speed_text):
        try:
            self.playback_speed = float(speed_text.replace('x', ''))
            print(f"Playback speed changed to {self.playback_speed}x")

            # If a clip is currently playing, update the timer interval
            if self.is_clip_playing and not self.clip_is_paused:
                interval = int(1000 / (self.clip_playback_fps * self.playback_speed))
                self.clip_playback_timer.setInterval(interval)

        except ValueError:
            self.playback_speed = 1.0

    def toggle_people_detection(self):
        """Toggle people detection for this camera"""
        if not self.camera_manager:
            print("Camera manager not set for fullscreen widget.")
            self.log_event("Error: Camera manager not set for detection toggle.")
            return

        new_state = not self.people_detection_enabled
        try:
            self.camera_manager.enable_people_detection(self.camera_id, new_state)
            self.people_detection_enabled = new_state
            self._update_detection_button_states() # Update UI
            self.log_event(f"People detection {'enabled' if new_state else 'disabled'}")
        except Exception as e:
            print(f"Error toggling people detection: {e}")
            self.log_event(f"Error toggling people detection: {e}")

    def toggle_fire_smoke_detection(self):
        """Toggle fire/smoke detection for this camera"""
        if not self.camera_manager:
            print("Camera manager not set for fullscreen widget.")
            self.log_event("Error: Camera manager not set for detection toggle.")
            return

        new_state = not self.fire_smoke_detection_enabled
        try:
            self.camera_manager.enable_fire_smoke_detection(self.camera_id, new_state)
            self.fire_smoke_detection_enabled = new_state
            self._update_detection_button_states() # Update UI
            self.log_event(f"Fire/Smoke detection {'enabled' if new_state else 'disabled'}")
        except Exception as e:
            print(f"Error toggling fire/smoke detection: {e}")
            self.log_event(f"Error toggling fire/smoke detection: {e}")

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start manual recording"""
        try:
            if not self.is_recording:
                # Create recordings directory if it doesn't exist
                recordings_dir = "recordings"
                if not os.path.exists(recordings_dir):
                    os.makedirs(recordings_dir)
                    
                self.is_recording = True
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.recording_filename = f"manual_recording_{self.camera_id}_{timestamp}.mp4"
                self.recording_start_time = time.time()
                
                # Update UI
                self.set_button_icon(self.record_btn, resource_path("assests/icons/fullscreen_sidebar/record.png"), "⏹")
                self.record_btn.setStyleSheet("background-color: #ff3333; border-radius: 4px;")
                self.recording_indicator.show()
                self.recording_time_label.show()
                self.recording_time_label.setText("REC 00:00")
                
                # Start timer for UI update
                if not hasattr(self, 'recording_timer'):
                    self.recording_timer = QTimer()
                    self.recording_timer.timeout.connect(self.update_recording_time)
                self.recording_timer.start(1000)
                
                self.log_event(f"Manual recording started: {self.recording_filename}")
                print(f"⏺ Started recording: {self.recording_filename}")
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.is_recording = False

    def stop_recording(self):
        """Stop manual recording"""
        try:
            if self.is_recording:
                self.is_recording = False
                
                if self.video_writer:
                    self.video_writer.release()
                    self.video_writer = None
                
                # Update UI
                self.set_button_icon(self.record_btn, resource_path("assests/icons/fullscreen_sidebar/record.png"), "⏺")
                self.record_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.1);
                    }
                """)
                self.recording_indicator.hide()
                self.recording_time_label.hide()
                
                if hasattr(self, 'recording_timer'):
                    self.recording_timer.stop()
                
                self.log_event("Manual recording stopped")
                print(f"⏹ Stopped recording")
                
        except Exception as e:
            print(f"❌ Error stopping recording: {e}")


    def update_recording_time(self):
        """Update recording time display"""
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
      
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.recording_time_label.setText(time_str)

    def zoom_in(self):
        """Zoom in"""
        if self.zoom_level < 4.0:
            self.zoom_level = min(4.0, self.zoom_level + 0.25)
            print(f"Zoomed in to {self.zoom_level}x")

    def zoom_out(self):
        """Zoom out"""
        if self.zoom_level > 0.25:
            self.zoom_level = max(0.25, self.zoom_level - 0.25)
            print(f"Zoomed out to {self.zoom_level}x")

    def display_frame(self, frame):
        """Display frame in the video label with error handling"""
        try:
            if frame is None or frame.size == 0:
                return
              
            # Create a copy to avoid modifying the original
            display_frame = frame.copy()
          
            # Apply zoom if needed
            if self.zoom_level != 1.0:
                h, w = display_frame.shape[:2]
                new_h, new_w = int(h * self.zoom_level), int(w * self.zoom_level)
              
                if new_h > 0 and new_w > 0:
                    display_frame = cv2.resize(display_frame, (new_w, new_h))
              
                    # Center crop if zoomed in
                    if self.zoom_level > 1.0:
                        start_y = max(0, (new_h - h) // 2)
                        start_x = max(0, (new_w - w) // 2)
                        end_y = min(new_h, start_y + h)
                        end_x = min(new_w, start_x + w)
                        display_frame = display_frame[start_y:end_y, start_x:end_x]
            
            # Overlay latest fire/smoke boxes in live mode, using recent detections only
            if (self.fire_smoke_detection_enabled and not self.is_clip_playing and self.current_frame_index == -1
                and self.fire_smoke_detections and (time.time() - self.fire_smoke_last_update) < 2.0):
                self._draw_fire_smoke_overlays(display_frame, self.fire_smoke_detections)
          
            # Draw fire size/intensity HUD in fullscreen live mode, if data available
            if (self.is_playing and not self.is_clip_playing and self.current_frame_index == -1
                and self.fire_overlay_info):
                try:
                    h, w = display_frame.shape[:2]
                    hud_text = (
                        f"Fire size: {self.fire_overlay_info['coverage']*100:.1f}%  |  "
                        f"Intensity: {self.fire_overlay_info['intensity']*100:.0f}%  |  "
                        f"Max conf: {self.fire_overlay_info['max_confidence']:.2f}"
                    )
                    # Background banner lower-left
                    pad = 8
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 0.6
                    (tw, th), _ = cv2.getTextSize(hud_text, font, scale, 2)
                    x0, y0 = pad, h - pad
                    cv2.rectangle(display_frame, (x0 - 6, y0 - th - 10), (x0 + tw + 6, y0 + 4), (0, 0, 0), -1)
                    cv2.putText(display_frame, hud_text, (x0, y0 - 4), font, scale, (255, 255, 255), 2)
                except Exception:
                    pass

            # Ensure frame is valid
            if display_frame.size == 0:
                return
              
            # Convert to grayscale if Night Mode is enabled
            if self.force_grayscale and len(display_frame.shape) == 3:
                display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)

            # Convert frame to Qt format
            if len(display_frame.shape) == 3:
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            else:
                # Handle grayscale
                h, w = display_frame.shape
                qt_image = QImage(display_frame.data, w, h, w, QImage.Format_Grayscale8)
          
            # Create pixmap and scale
            pixmap = QPixmap.fromImage(qt_image)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)
          
        except Exception as e:
            print(f"Error displaying frame: {e}")
            # Don't let display errors crash the application
            pass

    def __del__(self):
        """Ensure recording is stopped on destruction"""
        try:
            if hasattr(self, 'is_recording') and self.is_recording:
                self.stop_recording()
            if hasattr(self, 'video_writer') and self.video_writer:
                self.video_writer.release()
                self.video_writer = None
        except:
            pass

    def toggle_night_mode(self, enabled: bool):
        """Toggle black & white display in fullscreen regardless of time of day."""
        try:
            self.force_grayscale = bool(enabled)
            # Refresh the current display immediately
            if self.is_clip_playing and self.clip_playback_cap is not None:
                # Force redraw using last displayed clip frame if possible
                if self.clip_playback_cap.isOpened():
                    pos = int(self.clip_playback_cap.get(cv2.CAP_PROP_POS_FRAMES))
                    if pos > 0:
                        self.clip_playback_cap.set(cv2.CAP_PROP_POS_FRAMES, pos - 1)
                        ret, frame = self.clip_playback_cap.read()
                        if ret:
                            self.display_frame(frame)
            elif self.current_frame is not None:
                self.display_frame(self.current_frame)
            elif self.current_detection_frame is not None:
                self.display_frame(self.current_detection_frame)
        except Exception as e:
            print(f"Error toggling Night Mode: {e}")

    def _draw_fire_smoke_overlays(self, frame, detections):
        """Draw minimal fire/smoke overlays on the provided BGR frame."""
        try:
            max_fire_area = 0
            total_fire_area = 0
            image_area = frame.shape[0] * frame.shape[1] if frame is not None else 1
            max_conf = 0.0
            for det in detections:
                bbox = det.get('bbox')
                if not bbox or len(bbox) != 4:
                    continue
                x1, y1, x2, y2 = bbox
                confidence = float(det.get('confidence', 0.0))
                det_type = det.get('type') or det.get('class_name')

                if det_type == 'fire':
                    color = (0, 0, 255)
                    label = f"FIRE {confidence:.2f}"
                    # Accumulate area metrics for intensity/size
                    area = max(0, x2 - x1) * max(0, y2 - y1)
                    total_fire_area += area
                    if area > max_fire_area:
                        max_fire_area = area
                    if confidence > max_conf:
                        max_conf = confidence
                elif det_type == 'smoke':
                    color = (128, 128, 128)
                    label = f"SMOKE {confidence:.2f}"
                else:
                    color = (0, 0, 255)
                    label = f"OBJ {confidence:.2f}"

                thickness = 3 if confidence > 0.7 else 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.55
                (tw, th), _ = cv2.getTextSize(label, font, font_scale, 2)
                y1_label = max(0, y1 - th - 6)
                cv2.rectangle(frame, (x1, y1_label), (x1 + tw + 6, y1), color, -1)
                cv2.putText(frame, label, (x1 + 3, y1 - 4), font, font_scale, (255, 255, 255), 2)

            # Store overlay info for fullscreen HUD (size and intensity)
            if image_area > 0 and total_fire_area > 0:
                coverage = total_fire_area / float(image_area)
                # Simple intensity heuristic: combine coverage and max confidence
                intensity = min(1.0, 0.5 * coverage * 10 + 0.5 * max_conf)
                self.fire_overlay_info = {
                    'coverage': coverage,
                    'intensity': intensity,
                    'max_confidence': max_conf
                }
            else:
                self.fire_overlay_info = None
        except Exception:
            pass

    def on_panic_detected(self, camera_id: str, panic_behavior: PanicBehavior):
        """Handle panic behavior detection"""
        if camera_id != self.camera_id:
            return
          
        # Add to panic behaviors list
        self.panic_behaviors.append(panic_behavior)
      
        # Update UI
        self.update_panic_status()
        self.add_panic_to_list(panic_behavior)
        self.log_event(f"Panic behavior detected: {panic_behavior.behavior_type}")
      
        # Show panic alert
        self.show_panic_alert(panic_behavior)
      
        # Start event recording if enabled
        if self.auto_record_checkbox.isChecked():
            self.start_event_recording('panic', {
                'confidence': panic_behavior.confidence,
                'severity': panic_behavior.severity,
                'behavior_type': panic_behavior.behavior_type
            })
  
    def on_clip_created(self, clip: EventClip):
        """Handle new event clip creation"""
        if clip.camera_id == self.camera_id:
            self.log_event(f"Event clip created: {clip.event_type} ({clip.duration:.1f}s)")
            self.load_event_clips()
            self.timeline_widget.load_thumbnails()
  
    def update_panic_status(self):
        """Update panic detection status display"""
        recent_behaviors = [
            b for b in self.panic_behaviors 
            if time.time() - b.timestamp < 30  # Last 30 seconds
        ]
      
        if recent_behaviors:
            behavior_types = set(b.behavior_type for b in recent_behaviors)
            behavior_text = ", ".join(behavior_types)
            self.panic_status.setText(f"😰 Panic Behaviors: {behavior_text}")
            self.panic_status.setStyleSheet("color: #ff6666; font-size: 11px; font-weight: bold;")
          
            # Show panic alert display
            self.panic_alert_display.show()
        else:
            self.panic_status.setText("😰 Panic Behaviors: None detected")
            self.panic_status.setStyleSheet("color: #00ff00; font-size: 11px;")
            self.panic_alert_display.hide()
  
    def show_panic_alert(self, panic_behavior: PanicBehavior):
        """Show panic behavior alert"""
        behavior_name = panic_behavior.behavior_type.replace('_', ' ').title()
        self.panic_alert_display.setText(f"😰 {behavior_name.upper()}!")
        self.panic_alert_display.show()
      
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.panic_alert_display.hide)
  
    def add_panic_to_list(self, panic_behavior: PanicBehavior):
        """Add panic behavior to the recent behaviors list"""
        timestamp = datetime.datetime.fromtimestamp(panic_behavior.timestamp)
        time_str = timestamp.strftime("%H:%M:%S")
      
        behavior_text = f"[{time_str}] {panic_behavior.behavior_type.replace('_', ' ').title()}"
        behavior_text += f" (Confidence: {panic_behavior.confidence:.2f}, Severity: {panic_behavior.severity})"
      
        item = QListWidgetItem(behavior_text)
      
        # Color code by severity
        if panic_behavior.severity == 'high':
            item.setBackground(QColor(255, 100, 100, 100))
        elif panic_behavior.severity == 'medium':
            item.setBackground(QColor(255, 200, 100, 100))
        else:
            item.setBackground(QColor(200, 200, 200, 100))
      
        self.panic_behaviors_list.insertItem(0, item)
      
        # Keep only last 20 items
        while self.panic_behaviors_list.count() > 20:
            self.panic_behaviors_list.takeItem(self.panic_behaviors_list.count() - 1)
  
    def log_event(self, message: str):
        """Add event to the event log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
      
        self.event_log.append(log_entry)
      
        # Auto-scroll to bottom
        scrollbar = self.event_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
  
    def start_event_recording(self, event_type: str, trigger_data: dict):
        """Start automatic event recording or extend existing one."""
        # If an auto-recording is already active for this camera, extend its duration
        if self.auto_record_checkbox.isChecked():
            # If an auto-recording is already active for this camera, extend its duration
            if self.current_auto_recording_clip_id:
                print(f"Extending existing auto-recording: {self.current_auto_recording_clip_id}")
                self.auto_record_timer.stop() # Stop existing timer
                self.auto_record_timer.start(self.clip_duration_spin.value() * 1000) # Restart with new duration
                self.log_event(f"Extended event recording: {event_type}")
                return

            # Start a new recording
            clip_id = self.clip_manager.start_event_recording(
                self.camera_id, 
                self.camera_name, 
                event_type, 
                trigger_data
            )
            self.current_auto_recording_clip_id = clip_id
      
            # Start timer to stop recording after specified duration
            self.auto_record_timer.start(self.clip_duration_spin.value() * 1000) # Convert seconds to milliseconds
      
            self.log_event(f"Started event recording: {event_type}")
            print(f"Started auto-recording for {self.camera_id} with clip ID: {clip_id}")

    def on_auto_record_timeout(self):
        """Called when the auto-recording timer expires."""
        if self.current_auto_recording_clip_id:
            print(f"Auto-recording timer expired for {self.current_auto_recording_clip_id}. Stopping recording.")
            self.clip_manager.finish_recording(self.camera_id)
            self.current_auto_recording_clip_id = None
            self.log_event("Auto event recording stopped (duration expired).")
  
    def load_event_clips(self):
        """Load event clips for this camera"""
        clips = self.clip_manager.get_clips_by_filter(camera_id=self.camera_id)
      
        self.clips_list.clear()
      
        for clip in clips[:20]:  # Show last 20 clips
            timestamp = datetime.datetime.fromtimestamp(clip.start_time)
            time_str = timestamp.strftime("%m/%d %H:%M")
          
            # Event type emoji
            type_emoji = {
                'fire': '🔥',
                'smoke': '💨',
                'panic': '😰',
                'combined': '🚨'
            }.get(clip.event_type, '📹')
          
            item_text = f"{type_emoji} {clip.event_type.title()} - {time_str}"
            item_text += f" ({clip.duration:.1f}s)"
          
            if clip.reviewed:
                item_text += " ✅"
            if clip.bookmarked:
                item_text += " 🔖"
          
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, clip.clip_id)
          
            self.clips_list.addItem(item)
  
    def filter_event_clips(self):
        """Filter event clips based on selected type"""
        filter_text = self.event_filter_combo.currentText()
      
        event_type_map = {
            "All Events": None,
            "Fire Only": "fire",
            "Smoke Only": "smoke",
            "Panic Only": "panic",
            "Combined": "combined"
        }
      
        event_type = event_type_map.get(filter_text)
        clips = self.clip_manager.get_clips_by_filter(
            camera_id=self.camera_id,
            event_type=event_type
        )
      
        self.clips_list.clear()
      
        for clip in clips[:20]:
            timestamp = datetime.datetime.fromtimestamp(clip.start_time)
            time_str = timestamp.strftime("%m/%d %H:%M")
          
            type_emoji = {
                'fire': '🔥',
                'smoke': '💨',
                'panic': '😰',
                'combined': '🚨'
            }.get(clip.event_type, '📹')
          
            item_text = f"{type_emoji} {clip.event_type.title()} - {time_str}"
            item_text += f" ({clip.duration:.1f}s)"
          
            if clip.reviewed:
                item_text += " ✅"
            if clip.bookmarked:
                item_text += " 🔖"
          
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, clip.clip_id)
          
            self.clips_list.addItem(item)
  
    def play_event_clip(self, item):
        """Play selected event clip"""
        clip_id = item.data(Qt.UserRole)
        clip = self.clip_manager.clips_database.get(clip_id)
      
        if clip and os.path.exists(clip.file_path):
            self.log_event(f"Playing clip: {clip.event_type} - {clip.duration:.1f}s")
            self.play_video_file(clip.file_path)
  
    def play_selected_clip(self):
        """Play currently selected clip"""
        current_item = self.clips_list.currentItem()
        if current_item:
            self.play_event_clip(current_item)
  
    def export_selected_clip(self):
        """Export currently selected clip"""
        current_item = self.clips_list.currentItem()
        if current_item:
            clip_id = current_item.data(Qt.UserRole)
            clip = self.clip_manager.clips_database.get(clip_id)
            if clip:
                # TODO: Implement clip export
                self.log_event(f"Exporting clip: {clip.event_type}")
                print(f"📤 Exporting clip: {clip.file_path}")
  
    def delete_selected_clip(self):
        """Delete currently selected clip"""
        current_item = self.clips_list.currentItem()
        if current_item:
            clip_id = current_item.data(Qt.UserRole)
            clip = self.clip_manager.clips_database.get(clip_id)
            if clip:
                # TODO: Implement clip deletion with confirmation
                self.log_event(f"Deleted clip: {clip.event_type}")
                print(f"🗑️ Deleting clip: {clip.file_path}")
                self.load_event_clips()
  
    def toggle_panic_detection(self, enabled: bool):
        """Toggle panic detection on/off"""
        self.panic_detector.enable_detection(self.camera_id, enabled)
        self.log_event(f"Panic detection {'enabled' if enabled else 'disabled'}")
  
    def update_fire_threshold(self, value):
        """Update fire detection threshold"""
        self.fire_detection_threshold = value / 100.0
        self.fire_threshold_value.setText(f"{value}%")
        self.log_event(f"Fire detection threshold set to {self.fire_detection_threshold:.2f}")

    # Update existing methods to integrate with AI review system
  
    def _update_detection_button_states(self):
        """Helper to update the UI elements for detection buttons and info labels"""
        # People detection button and info label
        if self.people_detection_enabled:
            # Keep the icon, don't set text
            self.people_detection_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 255, 0, 30);
                    border: none;
                    border-radius: 22px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 255, 0, 50);
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
            self.people_count_display.show() # Show if enabled
        else:
            # Keep the icon, don't set text
            self.people_detection_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 22px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 20);
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
            self.people_count_display.hide() # Hide if disabled
        self.people_detection_btn.setChecked(self.people_detection_enabled)
        
        # Re-apply the icon after style changes
        self.set_button_icon(self.people_detection_btn, resource_path("assests/icons/fullscreen_sidebar/people_detection.png"), "👥")

        # Fire/Smoke detection button and info label
        if self.fire_smoke_detection_enabled:
            # Keep the icon, don't set text
            self.fire_smoke_detection_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 0, 0, 30);
                    border: none;
                    border-radius: 22px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 0, 0, 50);
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
            self.fire_smoke_alert_display.show() # Show if enabled
        else:
            # Keep the icon, don't set text
            self.fire_smoke_detection_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 22px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 20);
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
            self.fire_smoke_alert_display.hide() # Hide if disabled
        self.fire_smoke_detection_btn.setChecked(self.fire_smoke_detection_enabled)
        
        # Re-apply the icon after style changes
        self.set_button_icon(self.fire_smoke_detection_btn, resource_path("assests/icons/fullscreen_sidebar/fire_detection.png"), "🔥")

    def update_frame(self, frame):
        """Update with original frame - always show clean feed on main display"""
        try:
            if self.is_clip_playing:
                # Ignore live updates during clip playback
                return
            
            self.current_frame = frame.copy()
            
            # Add frame to frame history for playback
            if self.current_frame_index == -1:  # Live mode
                self.frame_history.append(frame.copy())
                if len(self.frame_history) > self.max_history:
                    self.frame_history.pop(0)
            
            # MAIN FEED DISPLAY LOGIC - Always prioritize clean, lag-free display
            display_frame = frame.copy()  # Start with original frame
            
            # Only show people detection overlay if fire detection is OFF
            # This prevents conflicts and ensures fire detection doesn't affect main feed
            if (self.people_detection_enabled and not self.fire_smoke_detection_enabled 
                and self.current_detection_frame is not None):
                display_frame = self.current_detection_frame
            
            # Display the frame if in live playback mode
            if self.is_playing and self.current_frame_index == -1:
                self.display_frame(display_frame)
            elif not self.is_playing and self.current_frame_index != -1:  # Playback mode
                if self.current_frame_index < len(self.frame_history):
                    playback_frame = self.frame_history[self.current_frame_index]
                    self.display_frame(playback_frame)

            # Process with panic detector if people are detected
            panic_behaviors = []
            if self.people_detection_enabled and self.detections:
                panic_behaviors = self.panic_detector.detect_panic_behaviors(
                    self.camera_id, frame, self.detections
                )

            # Add frame to active event recording if any is in progress
            if self.auto_record_checkbox.isChecked() and self.current_auto_recording_clip_id:
                detection_data = {
                    'panic_behaviors': panic_behaviors,
                    'fire_detections': self.fire_smoke_detections,
                    'people_detections': self.detections
                }
                self.clip_manager.add_frame_to_recording(
                    self.camera_id, frame, detection_data
                )
                
            # Handle recording (manual recording)
            if self.is_recording:
                self.handle_recording(display_frame)
                
        except Exception as e:
            print(f"Error updating frame for camera {self.camera_id}: {e}")

    def update_fire_smoke_detection_frame(self, frame, detections, alert_info):
        """Update fire/smoke detection frame and handle alerts"""
        self.current_fire_smoke_frame = frame
        self.fire_smoke_detections = detections
        self.fire_smoke_alert_info = alert_info
        self.fire_smoke_last_update = time.time()
        
        # Do NOT render detection frames directly to the main display here.
        # The main display should remain the clean, lag-free live feed managed by update_frame().
        # Rendering from both update_frame() and here causes flicker/glitches.
        
        fire_detected = False
        smoke_detected = False
        
        for detection in detections:
            det_type = detection.get('type') or detection.get('class_name')
            if det_type == 'fire':
                fire_detected = True
            elif det_type == 'smoke':
                smoke_detected = True
        
        # If fire detected, start auto alarm and pump
        if fire_detected and alert_info and alert_info.get('confidence', 0) > 0.5:
            if not DISABLE_AUDIO_ALARM:
                try:
                    self.on_auto_fire_alarm()
                except Exception as e:
                    print(f"Error in on_auto_fire_alarm: {e}")
            else:
                 pass # Audio disabled in safe mode
        
        if fire_detected or smoke_detected:
            # Prepare frame data for side panel
            frame_data = {
                'frame': frame,
                'detections': detections,
                'alert_info': alert_info,
                'timestamp': datetime.datetime.now()
            }
            
            if not DISABLE_SIDE_PANEL_UPDATE:
                try:
                    # Update existing fire detection frames or create new list
                    if hasattr(self, 'fire_detection_frames'):
                        self.fire_detection_frames.append(frame_data)
                        # Keep only last 50 frames to prevent memory issues
                        if len(self.fire_detection_frames) > 50:
                            self.fire_detection_frames = self.fire_detection_frames[-50:]
                    else:
                        self.fire_detection_frames = [frame_data]
                    
                    # Update the fire detection widget with new frames
                    if hasattr(self, 'fire_detection_widget'):
                        if self.fire_detection_widget.detection_active:
                            # Update existing detection mode
                            self.fire_detection_widget.update_frames(self.fire_detection_frames)
                        else:
                            # Activate detection mode if not already active
                            alert_id = f"alert_{self.camera_id}_{int(datetime.datetime.now().timestamp())}"
                            self.fire_detection_widget.activate_fire_detection_mode(
                                self.fire_detection_frames, 
                                alert_id=alert_id
                            )
                            
                            # Switch to fire detection tab
                            self.side_tabs.setCurrentWidget(self.fire_detection_widget)
                            
                            print(f"🔥 Fire detection side panel activated in fullscreen mode")
                except Exception as e:
                     print(f"Error updating side panel: {e}")
            else:
                 pass # Side panel disabled in safe mode

            # Start or extend auto event recording for fire/smoke
            if not DISABLE_AUTO_RECORDING:
                try:
                    if self.auto_record_checkbox.isChecked():
                        event_type = 'combined' if (fire_detected and smoke_detected) else ('fire' if fire_detected else 'smoke')
                        trigger_data = {
                            'alert_info': alert_info,
                            'people_count': self.people_count,
                            'max_confidence': alert_info.get('max_confidence', 0.0),
                            'fire_count': alert_info.get('fire_count', 0),
                            'smoke_count': alert_info.get('smoke_count', 0)
                        }
                        # This will auto-extend if a clip is already recording
                        self.start_event_recording(event_type, trigger_data)
                except Exception as e:
                    self.log_event(f"Error starting auto recording on fire/smoke: {e}")
            else:
                pass # Auto recording disabled in safe mode

        # Update live analysis status text without touching the main video frame
        try:
            fire_count = alert_info.get('fire_count', 0)
            smoke_count = alert_info.get('smoke_count', 0)
            if fire_detected or smoke_detected:
                self.fire_smoke_status.setText(f"🔥 Fire/Smoke: Fire {fire_count} | Smoke {smoke_count}")
                self.fire_smoke_status.setStyleSheet("color: #ff6666; font-size: 11px; font-weight: bold;")
            else:
                self.fire_smoke_status.setText("🔥 Fire/Smoke: None detected")
                self.fire_smoke_status.setStyleSheet("color: #00ff00; font-size: 11px;")
        except Exception:
            pass

        # Continuous fire detection tracking for auto-alarm and side panel countdown
        try:
            current_time = time.time()
            if fire_detected:
                if self.fire_continuous_start_time is None:
                    self.fire_continuous_start_time = current_time
                elapsed = current_time - self.fire_continuous_start_time
                remaining = max(0.0, self.auto_alarm_threshold_seconds - elapsed)
                if hasattr(self, 'fire_detection_widget'):
                    self.fire_detection_widget.update_auto_countdown(remaining, active=True)
                if not self.auto_alarm_triggered and elapsed >= self.auto_alarm_threshold_seconds:
                    self.auto_alarm_triggered = True
                    if hasattr(self, 'fire_detection_widget') and not DISABLE_AUDIO_ALARM:
                        self.fire_detection_widget.start_auto_alarm()
                    
                    # Trigger ESP32 pump ON after auto countdown
                    if not DISABLE_ESP32_COMMANDS:
                        self._trigger_pump_on_if_configured()
            else:
                # Reset when fire not detected
                self.fire_continuous_start_time = None
                if self.auto_alarm_triggered:
                    self.auto_alarm_triggered = False
                if hasattr(self, 'fire_detection_widget'):
                    self.fire_detection_widget.update_auto_countdown(0.0, active=False)
        except Exception:
            pass

    def handle_recording(self, frame):
        """Handle manual recording frame writing"""
        try:
            if self.is_recording and frame is not None:
                # Initialize video writer if not done
                if self.video_writer is None:
                    h, w = frame.shape[:2]
                    # Use H264 for better compatibility if available, or XVID
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    recordings_dir = "recordings"
                    filepath = os.path.join(recordings_dir, self.recording_filename)
                    # Force .avi for XVID or .mp4 for mp4v
                    if self.recording_filename.endswith('.mp4'):
                        filepath = filepath.replace('.mp4', '.avi')
                        self.recording_filename = self.recording_filename.replace('.mp4', '.avi')
                        
                    self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (w, h))
                
                # Write frame
                if self.video_writer:
                    self.video_writer.write(frame)
                    
        except Exception as e:
            print(f"Error handling recording: {e}")

    def play_video_file(self, filepath):
        """Start playing a video file in the main video area."""
        if self.clip_playback_cap:
            self.clip_playback_cap.release()
        self.clip_playback_cap = cv2.VideoCapture(filepath)
        if not self.clip_playback_cap.isOpened():
            self.log_event("Failed to open video file for playback.")
            return
        self.is_clip_playing = True
        # Get FPS from the video file
        fps = self.clip_playback_cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1:
            fps = 25  # fallback to 25 FPS if not available
        self.clip_playback_fps = fps
        self.clip_total_frames = int(self.clip_playback_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.clip_current_frame_pos = 0
        
        interval = int(1000 / fps)
        self.clip_playback_timer.start(interval)
        
        # Enable frame controls
        self.frame_back_btn.setEnabled(True)
        self.frame_forward_btn.setEnabled(True)
        
        # Update UI to show "RECORDED FOOTAGE"
        self.status_label.setText("⏯ RECORDED FOOTAGE")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffaa00;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border: 1px solid #ffaa00;
                border-radius: 4px;
            }
        """)
        # Show "Back to Live" button
        self.back_to_live_btn.show()

    def _playback_next_clip_frame(self):
        """Advance to the next frame in clip playback."""
        if self.clip_playback_cap and self.clip_playback_cap.isOpened():
            ret, frame = self.clip_playback_cap.read()
            if ret:
                self.clip_current_frame_pos += 1
                self.display_frame(frame)
            else:
                self.stop_clip_playback_and_return_to_live()

    def on_thumbnail_clicked(self, clip_id):
        """Handle thumbnail click from timeline"""
        clip = self.clip_manager.clips_database.get(clip_id)
        if clip and os.path.exists(clip.file_path):
            self.play_video_file(clip.file_path)
            self.log_event(f"Playing clip from timeline: {clip.event_type}")

    def on_dispatch_clicked(self, camera_id, clip_id):
        """Handle dispatch button click from fire detection widget"""
        self.log_event(f"🚨 DISPATCH: Emergency services dispatched for fire detection")
        print(f"🚨 DISPATCH: Emergency services dispatched for camera {camera_id}, clip {clip_id}")
        
        # Reset fire detection state
        self.fire_detection_active = False
        self.fire_detection_frames = []

    def on_false_alert_clicked(self, camera_id, clip_id):
        """Handle false alert button click from fire detection widget"""
        self.log_event(f"❌ FALSE ALERT: Fire detection marked as false alert")
        print(f"❌ FALSE ALERT: Fire detection marked as false for camera {camera_id}, clip {clip_id}")
        # Turn OFF pump and fan if they were turned on
        self._trigger_pump_off_if_configured()
        self._trigger_fan_off_if_configured()
        
        # Reset fire detection state
        self.fire_detection_active = False
        self.fire_detection_frames = []

    def update_people_detection_frame(self, annotated_frame, detections, people_count):
        """Update people detection frame and display it if active"""
        self.current_detection_frame = annotated_frame.copy()
        self.detections = detections
        self.people_count = people_count
        
        # Update people status in live analysis tab
        self.people_status.setText(f"👥 People: {people_count} detected")
        if people_count > 0:
            self.people_status.setStyleSheet("color: #ffaa00; font-size: 11px;")
            self.people_count_display.setText(f"👥 People: {people_count}")
            self.people_count_display.show()
        else:
            self.people_status.setStyleSheet("color: #00ff00; font-size: 11px;")
            self.people_count_display.hide()

        # Only display this frame if people detection is enabled and fire detection is OFF
        # This prevents conflicts and ensures fire detection doesn't affect main feed
        if (self.people_detection_enabled and self.is_playing and 
            self.current_frame_index == -1 and not self.fire_smoke_detection_enabled and
            not self.is_clip_playing):
            self.display_frame(self.current_detection_frame)

    # ===== ESP32 Pump Control Helpers =====
    def set_esp32_base_url(self, base_url: str):

        """Set the base URL for ESP32 control, e.g., http://192.168.1.100"""
        try:
            self.esp32_base_url = base_url.strip() if base_url else None
            print(f"✅ ESP32 base URL set: {self.esp32_base_url}")
            # Refresh pump and fan button states once URL is set
            self._update_pump_button_ui()
            self._update_fan_button_ui()
        except Exception:
            self.esp32_base_url = None

    def _send_esp32_command(self, path: str):
        if not self.esp32_base_url:
            return False
        try:
            url = f"{self.esp32_base_url.rstrip('/')}/{path.lstrip('/')}"
            # Use QThread to prevent blocking the main UI thread during network calls
            worker = ESP32CommandThread(url)
            # We need to keep a reference to the worker so it doesn't get garbage collected immediately
            if not hasattr(self, 'esp32_workers'):
                self.esp32_workers = []
            
            # Clean up finished workers
            self.esp32_workers = [w for w in self.esp32_workers if w.isRunning()]
            
            self.esp32_workers.append(worker)
            worker.start()
            return True
        except Exception as e:
            print(f"❌ ESP32 command error: {e}")
            return False

    def _trigger_pump_on_if_configured(self):
        if self.esp32_base_url and not self._pump_on_sent:
            if self._send_esp32_command('pump_on'):
                self._pump_on_sent = True
                self.log_event("Pump ON command sent to ESP32")
                self._update_pump_button_ui()

    def _trigger_pump_off_if_configured(self):
        if self.esp32_base_url and self._pump_on_sent:
            if self._send_esp32_command('pump_off'):
                self._pump_on_sent = False
                self.log_event("Pump OFF command sent to ESP32")
                self._update_pump_button_ui()

    def _trigger_fan_on_if_configured(self):
        if self.esp32_base_url and not self._fan_on_sent:
            if self._send_esp32_command('fan_on'):
                self._fan_on_sent = True
                self.log_event("Fan ON command sent to ESP32")
                self._update_fan_button_ui()

    def _trigger_fan_off_if_configured(self):
        if self.esp32_base_url and self._fan_on_sent:
            if self._send_esp32_command('fan_off'):
                self._fan_on_sent = False
                self.log_event("Fan OFF command sent to ESP32")
                self._update_fan_button_ui()

    def toggle_pump(self):
        """Toggle pump ON/OFF via ESP32 button in UI."""
        if not self.esp32_base_url:
            self.log_event("ESP32 URL not configured. Set base URL to control pump.")
            QMessageBox.warning(self, "ESP32 Not Configured", "ESP32 base URL is not set.")
            return
        if not self._pump_on_sent:
            ok = self._send_esp32_command('pump_on')
            if ok:
                self._pump_on_sent = True
                self.log_event("Manual Pump ON sent to ESP32")
                self._update_pump_button_ui()
            else:
                QMessageBox.warning(self, "Pump Command Failed", "Could not reach ESP32 to turn ON pump.")
        else:
            ok = self._send_esp32_command('pump_off')
            if ok:
                self._pump_on_sent = False
                self.log_event("Manual Pump OFF sent to ESP32")
                self._update_pump_button_ui()
            else:
                QMessageBox.warning(self, "Pump Command Failed", "Could not reach ESP32 to turn OFF pump.")

    def toggle_fan(self):
        """Toggle fan ON/OFF via ESP32 button in UI."""
        if not self.esp32_base_url:
            self.log_event("ESP32 URL not configured. Set base URL to control fan.")
            QMessageBox.warning(self, "ESP32 Not Configured", "ESP32 base URL is not set.")
            return
        if not self._fan_on_sent:
            ok = self._send_esp32_command('fan_on')
            if ok:
                self._fan_on_sent = True
                self.log_event("Manual Fan ON sent to ESP32")
                self._update_fan_button_ui()
            else:
                QMessageBox.warning(self, "Fan Command Failed", "Could not reach ESP32 to turn ON fan.")
        else:
            ok = self._send_esp32_command('fan_off')
            if ok:
                self._fan_on_sent = False
                self.log_event("Manual Fan OFF sent to ESP32")
                self._update_fan_button_ui()
            else:
                QMessageBox.warning(self, "Fan Command Failed", "Could not reach ESP32 to turn OFF fan.")

    def _update_pump_button_ui(self):
        try:
            if not hasattr(self, 'pump_toggle_btn') or self.pump_toggle_btn is None:
                return
            if not self.esp32_base_url:
                self.pump_toggle_btn.setEnabled(False)
                self.pump_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                        opacity: 0.3;
                    }
                """)
                self.set_button_icon(self.pump_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/water_pump.png"), "💧")
                self.pump_toggle_btn.setToolTip("ESP32 not configured")
                return
            self.pump_toggle_btn.setEnabled(True)
            if self._pump_on_sent:
                self.pump_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(0, 150, 255, 50);
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 150, 255, 70);
                    }
                """)
                self.set_button_icon(self.pump_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/water_pump.png"), "🛑")
                self.pump_toggle_btn.setToolTip("Turn OFF Water Pump")
            else:
                self.pump_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 150, 255, 30);
                    }
                """)
                self.set_button_icon(self.pump_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/water_pump.png"), "💧")
                self.pump_toggle_btn.setToolTip("Turn ON Water Pump")
        except Exception:
            pass

    def _update_fan_button_ui(self):
        try:
            if not hasattr(self, 'fan_toggle_btn') or self.fan_toggle_btn is None:
                return
            if not self.esp32_base_url:
                self.fan_toggle_btn.setEnabled(False)
                self.fan_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                        opacity: 0.3;
                    }
                """)
                self.set_button_icon(self.fan_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/fan.png"), "🌀")
                self.fan_toggle_btn.setToolTip("ESP32 not configured")
                return
            self.fan_toggle_btn.setEnabled(True)
            if self._fan_on_sent:
                self.fan_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(100, 200, 255, 50);
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: rgba(100, 200, 255, 70);
                    }
                """)
                self.set_button_icon(self.fan_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/fan.png"), "🛑")
                self.fan_toggle_btn.setToolTip("Turn OFF Fan")
            else:
                self.fan_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 22px;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: rgba(100, 200, 255, 30);
                    }
                """)
                self.set_button_icon(self.fan_toggle_btn, resource_path("assests/icons/fullscreen_sidebar/fan.png"), "🌀")
                self.fan_toggle_btn.setToolTip("Turn ON Fan")
        except Exception:
            pass
