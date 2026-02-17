import cv2
import numpy as np
import time
import datetime
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
class PanicBehavior:
    """Data class for panic behavior detection"""
    behavior_type: str  # 'running', 'falling', 'crowd_panic', 'erratic_movement'
    confidence: float
    timestamp: float
    bbox: Tuple[int, int, int, int]
    severity: str  # 'low', 'medium', 'high'

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
    panic_behaviors: List[PanicBehavior]
    max_confidence: float
    severity_level: str
    description: str
    reviewed: bool = False
    bookmarked: bool = False

class PanicBehaviorDetector(QObject):
    """AI system for detecting panic behaviors in video streams"""
    
    panic_detected = pyqtSignal(str, PanicBehavior)  # camera_id, panic_behavior
    
    def __init__(self):
        super().__init__()
        self.enabled_cameras = set()
        self.behavior_history = {}  # camera_id -> list of recent behaviors
        self.movement_trackers = {}  # camera_id -> movement tracking data
        self.crowd_density_threshold = 5
        self.movement_speed_threshold = 50  # pixels per frame
        
    def enable_detection(self, camera_id: str, enabled: bool = True):
        """Enable/disable panic detection for a camera"""
        if enabled:
            self.enabled_cameras.add(camera_id)
            self.behavior_history[camera_id] = []
            self.movement_trackers[camera_id] = {
                'previous_frame': None,
                'optical_flow': None,
                'person_tracks': {}
            }
        else:
            self.enabled_cameras.discard(camera_id)
            
    def detect_panic_behaviors(self, camera_id: str, frame: np.ndarray, 
                             people_detections: List[Dict]) -> List[PanicBehavior]:
        """Detect panic behaviors in the current frame"""
        if camera_id not in self.enabled_cameras:
            return []
            
        behaviors = []
        current_time = time.time()
        
        # Detect various panic behaviors
        behaviors.extend(self._detect_erratic_movement(camera_id, frame, people_detections))
        behaviors.extend(self._detect_crowd_panic(camera_id, frame, people_detections))
        behaviors.extend(self._detect_running_behavior(camera_id, frame, people_detections))
        behaviors.extend(self._detect_falling_behavior(camera_id, frame, people_detections))
        
        # Store in history and emit signals
        for behavior in behaviors:
            self.behavior_history[camera_id].append(behavior)
            self.panic_detected.emit(camera_id, behavior)
            
        # Keep only recent history (last 30 seconds)
        cutoff_time = current_time - 30
        self.behavior_history[camera_id] = [
            b for b in self.behavior_history[camera_id] 
            if b.timestamp > cutoff_time
        ]
        
        return behaviors
    
    def _detect_erratic_movement(self, camera_id: str, frame: np.ndarray, 
                                people_detections: List[Dict]) -> List[PanicBehavior]:
        """Detect erratic movement patterns"""
        behaviors = []
        tracker = self.movement_trackers[camera_id]
        
        if tracker['previous_frame'] is None:
            tracker['previous_frame'] = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return behaviors
            
        # Calculate optical flow
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowPyrLK(
            tracker['previous_frame'], gray, None, None
        )[0] if len(people_detections) > 0 else None
        
        for detection in people_detections:
            bbox = detection['bbox']
            center = detection['center']
            
            # Analyze movement in person's bounding box
            x1, y1, x2, y2 = bbox
            roi_flow = flow[y1:y2, x1:x2] if flow is not None else None
            
            if roi_flow is not None and roi_flow.size > 0:
                # Calculate movement metrics
                movement_magnitude = np.mean(np.sqrt(
                    roi_flow[:, :, 0]**2 + roi_flow[:, :, 1]**2
                ))
                movement_variance = np.var(np.sqrt(
                    roi_flow[:, :, 0]**2 + roi_flow[:, :, 1]**2
                ))
                
                # Detect erratic movement (high variance in movement)
                if movement_variance > 20 and movement_magnitude > 10:
                    confidence = min(0.95, movement_variance / 50)
                    severity = 'high' if movement_variance > 40 else 'medium'
                    
                    behavior = PanicBehavior(
                        behavior_type='erratic_movement',
                        confidence=confidence,
                        timestamp=time.time(),
                        bbox=bbox,
                        severity=severity
                    )
                    behaviors.append(behavior)
        
        tracker['previous_frame'] = gray
        return behaviors
    
    def _detect_crowd_panic(self, camera_id: str, frame: np.ndarray, 
                           people_detections: List[Dict]) -> List[PanicBehavior]:
        """Detect crowd panic situations"""
        behaviors = []
        
        if len(people_detections) < self.crowd_density_threshold:
            return behaviors
            
        # Calculate crowd density and movement correlation
        centers = [det['center'] for det in people_detections]
        
        # Check for synchronized rapid movement (crowd panic indicator)
        if len(centers) >= 3:
            # Calculate average movement direction
            movements = []
            for i in range(len(centers) - 1):
                for j in range(i + 1, len(centers)):
                    dx = centers[j][0] - centers[i][0]
                    dy = centers[j][1] - centers[i][1]
                    movements.append((dx, dy))
            
            if movements:
                avg_dx = np.mean([m[0] for m in movements])
                avg_dy = np.mean([m[1] for m in movements])
                movement_coherence = np.std([m[0] for m in movements]) + np.std([m[1] for m in movements])
                
                # Low coherence (similar movement) + high density = potential crowd panic
                if movement_coherence < 30 and len(people_detections) > 7:
                    confidence = min(0.9, (len(people_detections) - 5) / 10)
                    
                    # Use the center of the crowd as bbox
                    min_x = min(center[0] for center in centers) - 50
                    min_y = min(center[1] for center in centers) - 50
                    max_x = max(center[0] for center in centers) + 50
                    max_y = max(center[1] for center in centers) + 50
                    
                    behavior = PanicBehavior(
                        behavior_type='crowd_panic',
                        confidence=confidence,
                        timestamp=time.time(),
                        bbox=(min_x, min_y, max_x, max_y),
                        severity='high'
                    )
                    behaviors.append(behavior)
        
        return behaviors
    
    def _detect_running_behavior(self, camera_id: str, frame: np.ndarray, 
                                people_detections: List[Dict]) -> List[PanicBehavior]:
        """Detect running/rapid movement behavior"""
        behaviors = []
        tracker = self.movement_trackers[camera_id]
        
        for detection in people_detections:
            # Use a more robust ID for tracking, e.g., from a proper tracker if available
            # For now, a simple bbox-based ID
            bbox_str = str(detection['bbox'])
            current_center = detection['center']
            current_time = time.time()
            
            if bbox_str in tracker['person_tracks']:
                prev_data = tracker['person_tracks'][bbox_str]
                prev_center = prev_data['center']
                prev_time = prev_data['time']
                
                # Calculate speed
                distance = np.sqrt(
                    (current_center[0] - prev_center[0])**2 + 
                    (current_center[1] - prev_center[1])**2
                )
                time_diff = current_time - prev_time
                speed = distance / time_diff if time_diff > 0 else 0
                
                # Detect running (high speed movement)
                if speed > self.movement_speed_threshold:
                    confidence = min(0.9, speed / 100)
                    severity = 'high' if speed > 80 else 'medium'
                    
                    behavior = PanicBehavior(
                        behavior_type='running',
                        confidence=confidence,
                        timestamp=current_time,
                        bbox=detection['bbox'],
                        severity=severity
                    )
                    behaviors.append(behavior)
            
            # Update tracking
            tracker['person_tracks'][bbox_str] = {
                'center': current_center,
                'time': current_time
            }
        
        return behaviors
    
    def _detect_falling_behavior(self, camera_id: str, frame: np.ndarray, 
                                people_detections: List[Dict]) -> List[PanicBehavior]:
        """Detect falling behavior (aspect ratio analysis)"""
        behaviors = []
        
        for detection in people_detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            
            # Normal standing person has height > width
            # Falling person has width > height or very low height
            aspect_ratio = width / height if height > 0 else 0
            
            # Detect potential falling (unusual aspect ratio)
            if aspect_ratio > 1.2 or height < 60:  # Person is wider than tall or very short
                confidence = min(0.8, aspect_ratio / 2) if aspect_ratio > 1.2 else 0.7
                
                behavior = PanicBehavior(
                    behavior_type='falling',
                    confidence=confidence,
                    timestamp=time.time(),
                    bbox=bbox,
                    severity='high'
                )
                behaviors.append(behavior)
        
        return behaviors

class EventClipManager(QObject):
    """Manager for creating and managing event clips"""
    
    clip_created = pyqtSignal(EventClip)  # New clip created
    clip_updated = pyqtSignal(EventClip)  # Clip updated
    
    def __init__(self):
        super().__init__()
        self.clips_directory = "recordings/event_clips" # Updated path
        self.thumbnails_directory = "recordings/event_thumbnails" # Updated path
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
                            event_type: str, trigger_data: Dict) -> str:
        """Start recording an event clip"""
        # Check if there's already an active recording for this camera
        # If so, we might want to extend it or ignore the new trigger
        for cid, record_data in list(self.active_recordings.items()):
            if cid == camera_id:
                print(f"EventClipManager: Existing recording for camera {camera_id} is active. Not starting new one.")
                return record_data['clip'].clip_id # Return existing clip ID

        clip_id = f"{camera_id}_{event_type}_{int(time.time())}"
        start_time = time.time() - self.pre_event_buffer
        
        # Create clip metadata
        clip = EventClip(
            clip_id=clip_id,
            camera_id=camera_id,
            camera_name=camera_name,
            event_type=event_type,
            start_time=start_time,
            end_time=start_time + self.clip_duration, # Initial end time
            duration=self.clip_duration, # Initial duration
            file_path=os.path.join(self.clips_directory, f"{clip_id}.mp4"),
            thumbnail_path=os.path.join(self.thumbnails_directory, f"{clip_id}.jpg"),
            fire_detections=[],
            smoke_detections=[],
            panic_behaviors=[],
            max_confidence=trigger_data.get('confidence', 0.0),
            severity_level=trigger_data.get('severity', 'medium'),
            description=f"{event_type.title()} event detected on {camera_name}"
        )
        
        # Start recording
        self.active_recordings[camera_id] = {
            'clip': clip,
            'writer': None, # Will be initialized with first frame
            'start_time': time.time() # Actual start time of recording frames
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
        
        # Ensure frame is valid
        if frame is None or frame.size == 0:
            print(f"EventClipManager: Received empty frame for {clip.clip_id}. Skipping.")
            return

        # Initialize video writer if not done
        if recording['writer'] is None:
            h, w = frame.shape[:2]
            fps = 20.0 # Assuming 20 FPS for event clips, can be configurable
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for .mp4
            
            # Ensure the directory exists
            os.makedirs(self.clips_directory, exist_ok=True)
            
            filename = os.path.join(self.clips_directory, f"{clip.clip_id}.mp4")
            recording['writer'] = cv2.VideoWriter(filename, fourcc, fps, (w, h))
            clip.file_path = filename # Update the clip object with the actual file path
            print(f"EventClipManager: Initialized VideoWriter for {clip.clip_id} at {filename} with resolution {w}x{h}")
        
        # Write frame directly to video writer
        if recording['writer'].isOpened():
            recording['writer'].write(frame)
        else:
            print(f"EventClipManager: VideoWriter not open for {clip.clip_id}. Cannot write frame.")
            
        # Store detections
        if detections:
            if 'fire_detections' in detections:
                clip.fire_detections.extend(detections['fire_detections'])
            if 'smoke_detections' in detections:
                clip.smoke_detections.extend(detections['smoke_detections'])
            if 'panic_behaviors' in detections:
                # Panic behaviors are already PanicBehavior objects, so no need to convert
                clip.panic_behaviors.extend(detections['panic_behaviors'])
    
    def finish_recording(self, camera_id: str):
        """Finish and save event recording for a given camera_id"""
        if camera_id not in self.active_recordings:
            print(f"EventClipManager: No active recording found for camera {camera_id} to finish.")
            return
            
        recording = self.active_recordings.pop(camera_id) # Remove from active recordings
        clip = recording['clip']
        
        # Close video writer
        if recording['writer']:
            recording['writer'].release()
            print(f"EventClipManager: VideoWriter released for {clip.clip_id}")
        else:
            print(f"EventClipManager: No active or open VideoWriter found for {clip.clip_id}.")
        
        # Generate thumbnail
        self.generate_thumbnail(clip)
        
        # Update clip metadata
        clip.end_time = time.time()
        clip.duration = clip.end_time - clip.start_time
        
        # Determine final event type based on detections
        has_fire = len(clip.fire_detections) > 0
        has_smoke = len(clip.smoke_detections) > 0
        has_panic = len(clip.panic_behaviors) > 0
        
        if has_fire and (has_smoke or has_panic):
            clip.event_type = 'combined'
        elif has_fire:
            clip.event_type = 'fire'
        elif has_smoke and has_panic:
            clip.event_type = 'combined'
        elif has_smoke:
            clip.event_type = 'smoke'
        elif has_panic:
            clip.event_type = 'panic'
        
        # Calculate max confidence
        all_confidences = []
        all_confidences.extend([d.get('confidence', 0) for d in clip.fire_detections])
        all_confidences.extend([d.get('confidence', 0) for d in clip.smoke_detections])
        all_confidences.extend([b.confidence for b in clip.panic_behaviors])
        
        if all_confidences:
            clip.max_confidence = max(all_confidences)
        else:
            clip.max_confidence = 0.0 # Default if no detections
        
        # Save to database
        self.clips_database[clip.clip_id] = clip
        self.save_clips_database()
        
        # Emit signal
        self.clip_created.emit(clip)
        
        print(f"✅ Event clip saved: {clip.clip_id}")
    
    def generate_thumbnail(self, clip: EventClip):
        """Generate thumbnail for the clip"""
        try:
            if not os.path.exists(clip.file_path):
                print(f"❌ Clip file not found for thumbnail generation: {clip.file_path}")
                return

            cap = cv2.VideoCapture(clip.file_path)
            
            # Seek to middle of clip
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count == 0:
                print(f"❌ No frames in clip for thumbnail generation: {clip.file_path}")
                cap.release()
                return

            middle_frame = frame_count // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            if ret:
                # Resize to thumbnail size
                thumbnail = cv2.resize(frame, (320, 240))
                os.makedirs(self.thumbnails_directory, exist_ok=True) # Ensure thumbnail dir exists
                cv2.imwrite(clip.thumbnail_path, thumbnail)
                print(f"Generated thumbnail for {clip.clip_id} at {clip.thumbnail_path}")
            else:
                print(f"❌ Failed to read frame for thumbnail generation: {clip.file_path}")
            
            cap.release()
        except Exception as e:
            print(f"❌ Error generating thumbnail for {clip.clip_id}: {e}")
    
    def get_clips_by_filter(self, event_type: str = None, camera_id: str = None,
                           start_date: datetime.datetime = None,
                           end_date: datetime.datetime = None) -> List[EventClip]:
        """Get clips filtered by criteria"""
        clips = list(self.clips_database.values())
        
        if event_type and event_type != 'All Events': # Changed 'all' to 'All Events' for UI consistency
            if event_type == 'Fire Only':
                clips = [c for c in clips if c.event_type == 'fire']
            elif event_type == 'Smoke Only':
                clips = [c for c in clips if c.event_type == 'smoke']
            elif event_type == 'Panic Only':
                clips = [c for c in clips if c.event_type == 'panic']
            elif event_type == 'Combined':
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
    
    def get_clip(self, clip_id: str) -> Optional[EventClip]:
        """Retrieve a specific clip by its ID."""
        return self.clips_database.get(clip_id)

    def delete_clip(self, clip_id: str) -> bool:
        """Deletes a clip and its associated files."""
        clip = self.clips_database.pop(clip_id, None)
        if clip:
            if clip.file_path and os.path.exists(clip.file_path):
                try:
                    os.remove(clip.file_path)
                    print(f"Deleted clip file: {clip.file_path}")
                except OSError as e:
                    print(f"Error deleting clip file {clip.file_path}: {e}")
            if clip.thumbnail_path and os.path.exists(clip.thumbnail_path):
                try:
                    os.remove(clip.thumbnail_path)
                    print(f"Deleted thumbnail file: {clip.thumbnail_path}")
                except OSError as e:
                    print(f"Error deleting thumbnail file {clip.thumbnail_path}: {e}")
            self.save_clips_database()
            print(f"Clip {clip_id} deleted from database.")
            return True
        print(f"Clip {clip_id} not found for deletion.")
        return False

    def save_clips_database(self):
        """Save clips database to file"""
        try:
            db_file = os.path.join(self.clips_directory, "clips_database.json")
            
            # Convert clips to serializable format
            serializable_clips = {}
            for clip_id, clip in self.clips_database.items():
                clip_dict = asdict(clip)
                # Convert PanicBehavior objects to dicts
                clip_dict['panic_behaviors'] = [
                    asdict(behavior) for behavior in clip.panic_behaviors
                ]
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
                    # Convert panic behaviors back to objects
                    panic_behaviors = [
                        PanicBehavior(**behavior_dict) 
                        for behavior_dict in clip_dict.get('panic_behaviors', [])
                    ]
                    clip_dict['panic_behaviors'] = panic_behaviors
                    
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
        self.video_player = None # Placeholder for actual video player
        self.current_playing_clip_id = None
        self.video_capture = None
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self._play_next_frame)
        self.playback_fps = 20 # Default playback FPS
        
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
            "All Events", "Fire Only", "Smoke Only", "Panic Only", "Combined"
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
        self.play_btn.setEnabled(False) # Disable until clip is loaded
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setRange(0, 1000) # Arbitrary range for progress
        self.progress_slider.sliderMoved.connect(self.set_playback_position)
        
        # Time labels
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white;")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: white;")

        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("color: white;")
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self.change_playback_speed)
        self.speed_combo.setEnabled(False) # Disable until clip is loaded
        
        layout.addWidget(self.play_btn)
        layout.addWidget(self.current_time_label)
        layout.addWidget(self.progress_slider)
        layout.addWidget(self.total_time_label)
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
            "Panic Only": "panic_only",
            "Combined": "combined"
        }
        
        event_type = event_type_map.get(self.event_type_combo.currentText())
        camera_name = self.camera_combo.currentText()
        camera_id = None
        
        if camera_name != "All Cameras":
            # Find camera_id by name
            # This is inefficient, better to store camera_id in combo box data
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
                'panic': '😰',
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
        self.stop_playback() # Stop any currently playing video

        if not os.path.exists(clip.file_path):
            self.video_label.setText("Video file not found.")
            self.play_btn.setEnabled(False)
            self.progress_slider.setEnabled(False)
            self.speed_combo.setEnabled(False)
            print(f"Error: Video file not found at {clip.file_path}")
            return

        self.video_capture = cv2.VideoCapture(clip.file_path)
        if not self.video_capture.isOpened():
            self.video_label.setText("Failed to open video.")
            self.play_btn.setEnabled(False)
            self.progress_slider.setEnabled(False)
            self.speed_combo.setEnabled(False)
            print(f"Error: Could not open video file {clip.file_path}")
            return

        self.current_playing_clip_id = clip.clip_id
        self.play_btn.setEnabled(True)
        self.progress_slider.setEnabled(True)
        self.speed_combo.setEnabled(True)

        # Set slider range based on video length
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.progress_slider.setRange(0, self.total_frames - 1)
        
        total_seconds = self.total_frames / self.video_fps
        self.total_time_label.setText(f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}")
        self.current_time_label.setText("00:00")

        self.play_btn.setText("▶️") # Reset play button text
        self.video_label.setText("") # Clear text
        self.progress_slider.setValue(0) # Reset slider

        # Always start at normal speed
        self.speed_combo.setCurrentText("1.0x")
        self.current_playback_speed = 1.0

        # Display first frame as preview
        ret, frame = self.video_capture.read()
        if ret:
            self._display_frame_on_label(frame)
        else:
            self.video_label.setText("No frames in video.")
            self.play_btn.setEnabled(False)

    def _play_next_frame(self):
        """Reads and displays the next frame of the video."""
        if self.video_capture and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                self._display_frame_on_label(frame)
                current_frame_pos = int(self.video_capture.get(cv2.CAP_PROP_POS_FRAMES))
                self.progress_slider.setValue(current_frame_pos)
                
                current_seconds = current_frame_pos / self.video_fps
                self.current_time_label.setText(f"{int(current_seconds // 60):02d}:{int(current_seconds % 60):02d}")
            else:
                self.stop_playback()
                self.video_label.setText("Video finished.")
                self.play_btn.setText("▶️")
                self.progress_slider.setValue(self.total_frames - 1) # Set slider to end
                total_seconds = self.total_frames / self.video_fps
                self.current_time_label.setText(f"{int(total_seconds // 60):02d}:{int(total_seconds % 60):02d}")

    def _display_frame_on_label(self, frame: np.ndarray):
        """Helper to convert OpenCV frame to QPixmap and display."""
        if frame is None or frame.size == 0:
            return
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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

    def toggle_playback(self):
        """Toggle video playback"""
        if self.video_capture and self.video_capture.isOpened():
            if self.playback_timer.isActive():
                self.stop_playback()
                self.play_btn.setText("▶️")
            else:
                # If at end, restart from beginning
                if self.video_capture.get(cv2.CAP_PROP_POS_FRAMES) >= self.total_frames - 1:
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.progress_slider.setValue(0)
                    self.current_time_label.setText("00:00")

                # Always use the current speed and fps
                interval = int(1000 / (self.playback_fps * self.current_playback_speed))
                self.playback_timer.start(interval)
                self.play_btn.setText("⏸️")
        else:
            # If no clip loaded, try to load the selected one
            current_item = self.clips_list_widget.currentItem()
            if current_item:
                clip_id = current_item.data(Qt.UserRole)
                clip = self.clip_manager.clips_database.get(clip_id)
                if clip:
                    self.load_clip_video(clip)
                    self.toggle_playback() # Start playing after loading

    def stop_playback(self):
        """Stops video playback."""
        self.playback_timer.stop()

    def set_playback_position(self, value):
        """Sets video playback position based on slider value."""
        if self.video_capture and self.video_capture.isOpened():
            frame_pos = value
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            # Immediately display the frame at the new position
            ret, frame = self.video_capture.read()
            if ret:
                self._display_frame_on_label(frame)
                current_seconds = frame_pos / self.video_fps
                self.current_time_label.setText(f"{int(current_seconds // 60):02d}:{int(current_seconds % 60):02d}")

    def change_playback_speed(self, speed_text):
        """Change playback speed"""
        try:
            self.current_playback_speed = float(speed_text.replace('x', ''))
            if self.playback_timer.isActive():
                self.playback_timer.stop()
                interval = int(1000 / (self.playback_fps * self.current_playback_speed))
                self.playback_timer.start(interval)
        except ValueError:
            self.current_playback_speed = 1.0
            print("Invalid playback speed selected.")

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
        <h4 style="color: #ff6666;">😰 Panic Behaviors: {len(clip.panic_behaviors)}</h4>
        
        <h4 style="color: #66ff66;">📝 Description:</h4>
        <p>{clip.description}</p>
        """
        
        if clip.panic_behaviors:
            details_html += "<h4 style='color: #ff6666;'>Detected Panic Behaviors:</h4><ul>"
            for behavior in clip.panic_behaviors:
                details_html += f"<li>{behavior.behavior_type.replace('_', ' ').title()} "
                details_html += f"(Confidence: {behavior.confidence:.2f}, Severity: {behavior.severity})</li>"
            details_html += "</ul>"
        
        self.details_text.setHtml(details_html)
        
        # Update button states
        self.bookmark_btn.setText("🔖 Bookmarked" if clip.bookmarked else "🔖 Bookmark")
        self.reviewed_btn.setText("✅ Reviewed" if clip.reviewed else "✅ Mark Reviewed")
    
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
                # Open a file dialog to choose save location
                options = QFileDialog.Options()
                file_name, _ = QFileDialog.getSaveFileName(
                    self, "Export Clip", clip.file_path, "Video Files (*.mp4);;All Files (*)", options=options
                )
                if file_name:
                    try:
                        import shutil
                        shutil.copy(clip.file_path, file_name)
                        QMessageBox.information(self, "Export Successful", f"Clip exported to:\n{file_name}")
                        print(f"📤 Exporting clip: {clip.clip_id} to {file_name}")
                    except Exception as e:
                        QMessageBox.critical(self, "Export Failed", f"Error exporting clip: {e}")
                        print(f"❌ Error exporting clip: {e}")
