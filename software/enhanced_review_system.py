import cv2
import numpy as np
import time
import datetime
import threading
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QComboBox,
                             QSlider, QProgressBar, QListWidget, QListWidgetItem,
                             QDialog, QTextEdit, QCheckBox, QSpinBox)
from PyQt5.QtGui import QPixmap, QImage, QFont, QMovie
from PyQt5.QtCore import Qt


@dataclass
class EventClip:
    """Data class for event clips"""
    clip_id: str
    camera_id: str
    camera_name: str
    event_type: str  # 'fire', 'smoke', 'panic', 'combined'
    start_time: float
    end_time: float
    duration: float
    file_path: str
    thumbnail_path: str
    fire_detections: List[Dict]
    smoke_detections: List[Dict]
    max_confidence: float
    severity_level: str
    description: str
    reviewed: bool = False
    bookmarked: bool = False


class EventClipManager(QObject):
    """Manager for creating and managing event clips"""
    
    clip_created = pyqtSignal(EventClip)  # New clip created
    clip_updated = pyqtSignal(EventClip)  # Clip updated
    
    def __init__(self):
        super().__init__()
        self.clips_directory = "event_clips"
        self.thumbnails_directory = "event_thumbnails"
        self.clips_database = {}  # clip_id -> EventClip
        self.active_recordings = {}  # camera_id -> recording data
        self.clip_duration = 15  # seconds
        self.pre_event_buffer = 5  # seconds before event
        
        # Create directories
        os.makedirs(self.clips_directory, exist_ok=True)
        os.makedirs(self.thumbnails_directory, exist_ok=True)
        
        # Load existing clips
        self.load_clips_database()
    
    def start_event_recording(self, camera_id: str, camera_name: str, 
                            event_type: str, trigger_data: Dict):
        """Start recording an event clip"""
        clip_id = f"{camera_id}_{int(time.time())}"
        start_time = time.time() - self.pre_event_buffer
        
        # Create clip metadata
        clip = EventClip(
            clip_id=clip_id,
            camera_id=camera_id,
            camera_name=camera_name,
            event_type=event_type,
            start_time=start_time,
            end_time=start_time + self.clip_duration,
            duration=self.clip_duration,
            file_path=os.path.join(self.clips_directory, f"{clip_id}.mp4"),
            thumbnail_path=os.path.join(self.thumbnails_directory, f"{clip_id}.jpg"),
            fire_detections=[],
            smoke_detections=[],
            max_confidence=trigger_data.get('confidence', 0.0),
            severity_level=trigger_data.get('severity', 'medium'),
            description=f"{event_type.title()} event detected on {camera_name}"
        )
        
        # Start recording
        self.active_recordings[camera_id] = {
            'clip': clip,
            'writer': None,
            'frame_buffer': [],
            'start_time': time.time()
        }
        
        print(f"🎬 Started event recording: {clip_id}")
        return clip_id
    
    def add_frame_to_recording(self, camera_id: str, frame: np.ndarray, 
                             detections: Dict = None):
        """Add frame to active recording"""
        if camera_id not in self.active_recordings:
            return
            
        recording = self.active_recordings[camera_id]
        clip = recording['clip']
        
        # Initialize video writer if not done
        if recording['writer'] is None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            h, w = frame.shape[:2]
            recording['writer'] = cv2.VideoWriter(
                clip.file_path, fourcc, 30.0, (w, h)
            )
        
        # Write frame
        recording['writer'].write(frame)
        
        # Store detections
        if detections:
            current_time = time.time()
            if 'fire_detections' in detections:
                clip.fire_detections.extend(detections['fire_detections'])
            if 'smoke_detections' in detections:
                clip.smoke_detections.extend(detections['smoke_detections'])
        
        # Check if recording is complete
        if time.time() - recording['start_time'] >= self.clip_duration:
            self.finish_recording(camera_id)
    
    def finish_recording(self, camera_id: str):
        """Finish and save event recording"""
        if camera_id not in self.active_recordings:
            return
            
        recording = self.active_recordings[camera_id]
        clip = recording['clip']
        
        # Close video writer
        if recording['writer']:
            recording['writer'].release()
        
        # Generate thumbnail
        self.generate_thumbnail(clip)
        
        # Update clip metadata
        clip.end_time = time.time()
        clip.duration = clip.end_time - clip.start_time
        
        # Determine final event type based on detections
        has_fire = len(clip.fire_detections) > 0
        has_smoke = len(clip.smoke_detections) > 0
        
        if has_fire and has_smoke:
            clip.event_type = 'combined'
        elif has_fire:
            clip.event_type = 'fire'
        elif has_smoke:
            clip.event_type = 'smoke'
        
        # Calculate max confidence
        all_confidences = []
        all_confidences.extend([d.get('confidence', 0) for d in clip.fire_detections])
        all_confidences.extend([d.get('confidence', 0) for d in clip.smoke_detections])
        
        if all_confidences:
            clip.max_confidence = max(all_confidences)
        
        # Save to database
        self.clips_database[clip.clip_id] = clip
        self.save_clips_database()
        
        # Clean up
        del self.active_recordings[camera_id]
        
        # Emit signal
        self.clip_created.emit(clip)
        
        print(f"✅ Event clip saved: {clip.clip_id}")
    
    def generate_thumbnail(self, clip: EventClip):
        """Generate thumbnail for the clip"""
        try:
            cap = cv2.VideoCapture(clip.file_path)
            
            # Seek to middle of clip
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame = frame_count // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            if ret:
                # Resize to thumbnail size
                thumbnail = cv2.resize(frame, (320, 240))
                cv2.imwrite(clip.thumbnail_path, thumbnail)
            
            cap.release()
        except Exception as e:
            print(f"❌ Error generating thumbnail: {e}")
    
    def get_clips_by_filter(self, event_type: str = None, camera_id: str = None,
                           start_date: datetime.datetime = None,
                           end_date: datetime.datetime = None) -> List[EventClip]:
        """Get clips filtered by criteria"""
        clips = list(self.clips_database.values())
        
        if event_type and event_type != 'all':
            if event_type == 'fire_only':
                clips = [c for c in clips if c.event_type == 'fire']
            elif event_type == 'smoke_only':
                clips = [c for c in clips if c.event_type == 'smoke']
            elif event_type == 'combined':
                clips = [c for c in clips if c.event_type == 'combined']
        
        if camera_id:
            clips = [c for c in clips if c.camera_id == camera_id]
        
        if start_date:
            start_timestamp = start_date.timestamp()
            clips = [c for c in clips if c.start_time >= start_timestamp]
        
        if end_date:
            end_timestamp = end_date.timestamp()
            clips = [c for c in clips if c.start_time <= end_timestamp]
        
        # Sort by timestamp (newest first)
        clips.sort(key=lambda x: x.start_time, reverse=True)
        
        return clips
    
    def save_clips_database(self):
        """Save clips database to file"""
        try:
            db_file = os.path.join(self.clips_directory, "clips_database.json")
            
            # Convert clips to serializable format
            serializable_clips = {}
            for clip_id, clip in self.clips_database.items():
                clip_dict = asdict(clip)
                serializable_clips[clip_id] = clip_dict
            
            with open(db_file, 'w') as f:
                json.dump(serializable_clips, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving clips database: {e}")
    
    def load_clips_database(self):
        """Load clips database from file"""
        try:
            db_file = os.path.join(self.clips_directory, "clips_database.json")
            
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    data = json.load(f)
                
                for clip_id, clip_dict in data.items():
                    
                    # Create EventClip object
                    clip = EventClip(**clip_dict)
                    self.clips_database[clip_id] = clip
                
                print(f"📚 Loaded {len(self.clips_database)} clips from database")
                
        except Exception as e:
            print(f"❌ Error loading clips database: {e}")

class EventReviewWidget(QWidget):
    """Widget for reviewing event clips in story/reel format"""
    
    def __init__(self, clip_manager: EventClipManager):
        super().__init__()
        self.clip_manager = clip_manager
        self.current_clips = []
        self.current_clip_index = 0
        self.video_player = None
        
        self.setup_ui()
        self.load_clips()
    
    def setup_ui(self):
        """Setup the review interface"""
        layout = QVBoxLayout(self)
        
        # Header with filters
        header_widget = self.create_header()
        layout.addWidget(header_widget)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Clips list (left side)
        self.clips_list = self.create_clips_list()
        content_layout.addWidget(self.clips_list, 1)
        
        # Video player (right side)
        self.player_widget = self.create_video_player()
        content_layout.addWidget(self.player_widget, 2)
        
        layout.addWidget(content_widget)
    
    def create_header(self) -> QWidget:
        """Create header with filters and controls"""
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title
        title = QLabel("🎬 Event Review Dashboard")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: transparent;
            }
        """)
        
        # Event type filter
        type_label = QLabel("Event Type:")
        type_label.setStyleSheet("color: white; background: transparent;")
        
        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems([
            "All Events", "Fire Only", "Smoke Only", "Combined"
        ])
        self.event_type_combo.currentTextChanged.connect(self.filter_clips)
        
        # Camera filter
        camera_label = QLabel("Camera:")
        camera_label.setStyleSheet("color: white; background: transparent;")
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItem("All Cameras")
        self.camera_combo.currentTextChanged.connect(self.filter_clips)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_clips)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(type_label)
        layout.addWidget(self.event_type_combo)
        layout.addWidget(camera_label)
        layout.addWidget(self.camera_combo)
        layout.addWidget(refresh_btn)
        
        return header
    
    def create_clips_list(self) -> QWidget:
        """Create clips list widget"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # List header
        header = QLabel("Event Clips")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background-color: #3d3d3d;
                border-radius: 4px;
            }
        """)
        
        # Clips list
        self.clips_list_widget = QListWidget()
        self.clips_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #505050;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #505050;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #ff3333;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        self.clips_list_widget.itemClicked.connect(self.on_clip_selected)
        
        layout.addWidget(header)
        layout.addWidget(self.clips_list_widget)
        
        return container
    
    def create_video_player(self) -> QWidget:
        """Create video player widget"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Video display area
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #505050;
                border-radius: 8px;
            }
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("Select a clip to play")
        
        # Controls
        controls_widget = self.create_player_controls()
        
        # Clip details
        self.details_widget = self.create_clip_details()
        
        layout.addWidget(self.video_label)
        layout.addWidget(controls_widget)
        layout.addWidget(self.details_widget)
        
        return container
    
    def create_player_controls(self) -> QWidget:
        """Create video player controls"""
        controls = QWidget()
        controls.setFixedHeight(60)
        layout = QHBoxLayout(controls)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶️")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self.toggle_playback)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        
        # Time labels
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white;")
        
        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: white;")
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        
        layout.addWidget(self.play_btn)
        layout.addWidget(self.progress_slider)
        layout.addWidget(self.time_label)
        layout.addWidget(speed_label)
        layout.addWidget(self.speed_combo)
        
        return controls
    
    def create_clip_details(self) -> QWidget:
        """Create clip details panel"""
        details = QWidget()
        details.setMaximumHeight(200)
        layout = QVBoxLayout(details)
        
        # Details text area
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        
        # Action buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        self.bookmark_btn = QPushButton("🔖 Bookmark")
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        
        self.reviewed_btn = QPushButton("✅ Mark Reviewed")
        self.reviewed_btn.clicked.connect(self.toggle_reviewed)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_clip)
        
        buttons_layout.addWidget(self.bookmark_btn)
        buttons_layout.addWidget(self.reviewed_btn)
        buttons_layout.addWidget(export_btn)
        buttons_layout.addStretch()
        
        layout.addWidget(self.details_text)
        layout.addWidget(buttons_widget)
        
        return details
    
    def load_clips(self):
        """Load clips into the list"""
        self.current_clips = self.clip_manager.get_clips_by_filter()
        self.update_clips_list()
        
        # Update camera filter
        cameras = set(clip.camera_name for clip in self.current_clips)
        self.camera_combo.clear()
        self.camera_combo.addItem("All Cameras")
        self.camera_combo.addItems(sorted(cameras))
    
    def filter_clips(self):
        """Filter clips based on selected criteria"""
        event_type_map = {
            "All Events": None,
            "Fire Only": "fire_only",
            "Smoke Only": "smoke_only", 
            "Combined": "combined"
        }
        
        event_type = event_type_map.get(self.event_type_combo.currentText())
        camera_name = self.camera_combo.currentText()
        camera_id = None
        
        if camera_name != "All Cameras":
            # Find camera_id by name
            for clip in self.clip_manager.clips_database.values():
                if clip.camera_name == camera_name:
                    camera_id = clip.camera_id
                    break
        
        self.current_clips = self.clip_manager.get_clips_by_filter(
            event_type=event_type,
            camera_id=camera_id
        )
        self.update_clips_list()
    
    def update_clips_list(self):
        """Update the clips list widget"""
        self.clips_list_widget.clear()
        
        for clip in self.current_clips:
            # Create list item
            item = QListWidgetItem()
            
            # Format clip info
            timestamp = datetime.datetime.fromtimestamp(clip.start_time)
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Event type emoji
            type_emoji = {
                'fire': '🔥',
                'smoke': '💨', 
                'smoke': '💨', 
                'combined': '🚨'
            }.get(clip.event_type, '📹')
            
            # Status indicators
            status = ""
            if clip.bookmarked:
                status += "🔖 "
            if clip.reviewed:
                status += "✅ "
            
            item_text = f"{type_emoji} {clip.camera_name}\n"
            item_text += f"📅 {time_str}\n"
            item_text += f"⏱️ {clip.duration:.1f}s | 🎯 {clip.max_confidence:.2f}\n"
            item_text += f"{status}{clip.description}"
            
            item.setText(item_text)
            item.setData(Qt.UserRole, clip.clip_id)
            
            self.clips_list_widget.addItem(item)
    
    def on_clip_selected(self, item):
        """Handle clip selection"""
        clip_id = item.data(Qt.UserRole)
        clip = self.clip_manager.clips_database.get(clip_id)
        
        if clip:
            self.load_clip_video(clip)
            self.update_clip_details(clip)
    
    def load_clip_video(self, clip: EventClip):
        """Load and display clip video"""
        try:
            # Load thumbnail first
            if os.path.exists(clip.thumbnail_path):
                pixmap = QPixmap(clip.thumbnail_path)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)
            
            # TODO: Implement actual video playback
            # For now, just show the thumbnail
            
        except Exception as e:
            print(f"❌ Error loading clip video: {e}")
    
    def update_clip_details(self, clip: EventClip):
        """Update clip details panel"""
        details_html = f"""
        <h3 style="color: #ff3333;">📹 {clip.camera_name}</h3>
        <p><strong>Event Type:</strong> {clip.event_type.title()}</p>
        <p><strong>Duration:</strong> {clip.duration:.1f} seconds</p>
        <p><strong>Max Confidence:</strong> {clip.max_confidence:.2f}</p>
        <p><strong>Severity:</strong> {clip.severity_level.title()}</p>
        <p><strong>Timestamp:</strong> {datetime.datetime.fromtimestamp(clip.start_time).strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h4 style="color: #ffaa00;">🔥 Fire Detections: {len(clip.fire_detections)}</h4>
        <h4 style="color: #aaaaaa;">💨 Smoke Detections: {len(clip.smoke_detections)}</h4>
        <h4 style="color: #aaaaaa;">💨 Smoke Detections: {len(clip.smoke_detections)}</h4>
        
        <h4 style="color: #66ff66;">📝 Description:</h4>
        <p>{clip.description}</p>
        """
        
        
        self.details_text.setHtml(details_html)
        
        # Update button states
        self.bookmark_btn.setText("🔖 Bookmarked" if clip.bookmarked else "🔖 Bookmark")
        self.reviewed_btn.setText("✅ Reviewed" if clip.reviewed else "✅ Mark Reviewed")
    
    def toggle_playback(self):
        """Toggle video playback"""
        # TODO: Implement video playback controls
        if self.play_btn.text() == "▶️":
            self.play_btn.setText("⏸️")
        else:
            self.play_btn.setText("▶️")
    
    def toggle_bookmark(self):
        """Toggle clip bookmark status"""
        current_item = self.clips_list_widget.currentItem()
        if current_item:
            clip_id = current_item.data(Qt.UserRole)
            clip = self.clip_manager.clips_database.get(clip_id)
            if clip:
                clip.bookmarked = not clip.bookmarked
                self.clip_manager.save_clips_database()
                self.update_clip_details(clip)
                self.update_clips_list()
    
    def toggle_reviewed(self):
        """Toggle clip reviewed status"""
        current_item = self.clips_list_widget.currentItem()
        if current_item:
            clip_id = current_item.data(Qt.UserRole)
            clip = self.clip_manager.clips_database.get(clip_id)
            if clip:
                clip.reviewed = not clip.reviewed
                self.clip_manager.save_clips_database()
                self.update_clip_details(clip)
                self.update_clips_list()
    
    def export_clip(self):
        """Export selected clip"""
        current_item = self.clips_list_widget.currentItem()
        if current_item:
            clip_id = current_item.data(Qt.UserRole)
            clip = self.clip_manager.clips_database.get(clip_id)
            if clip:
                # TODO: Implement clip export functionality
                print(f"📤 Exporting clip: {clip.clip_id}")
