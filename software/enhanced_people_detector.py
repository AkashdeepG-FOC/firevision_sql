import cv2
import numpy as np
import time
import threading
from ultralytics import YOLO
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import json
from collections import deque
import os

class EnhancedPeopleDetector(QObject):
    """Enhanced YOLOv8-based people detection with panic behavior analysis"""
    
    detection_result = pyqtSignal(str, np.ndarray, list, int)
    line_crossing = pyqtSignal(str, str, int, int)
    panic_behavior_detected = pyqtSignal(str, dict, float)  # camera_id, behavior_info, confidence
    event_clip_ready = pyqtSignal(str, str, dict)  # camera_id, clip_path, event_data

    def __init__(self):
        super().__init__()
        self.model = None
        self.model_loaded = False
        self.detection_enabled = {}
        self.confidence_threshold = 0.5
        self.min_area = 3000
        self.count_history = {}
        self.smoothing_frames = 5
        
        # Enhanced tracking for panic behavior
        self.tracked_objects = {}
        self.object_trajectories = {}  # Store movement patterns
        self.panic_detection_enabled = {}
        self.behavior_history = {}  # Store behavior patterns
        
        # Event recording system
        self.event_buffers = {}  # Pre-event frame buffers
        self.recording_events = {}  # Currently recording events
        self.event_clips_dir = "event_clips"
        self.buffer_duration = 5  # seconds before event
        self.clip_duration = 15  # total clip duration
        self.max_buffer_frames = 150  # 5 seconds at 30fps
        
        # Panic behavior parameters
        self.panic_thresholds = {
            'rapid_movement': 50,  # pixels per frame
            'erratic_movement': 0.3,  # direction change threshold
            'crowd_density': 0.7,  # people per area ratio
            'sudden_gathering': 5,  # people count increase
            'running_speed': 80,  # pixels per frame for running
        }
        
        # Line crossing detection
        self.counting_lines = {}
        self.line_counts = {}
        self.object_id_counter = {}
        
        # Performance optimization
        self.frame_skip = {}
        self.process_every_n_frames = 3
        self.last_detection_time = {}
        self.last_detections = {}
        self.detection_threads = {}
        self.detection_queue = {}
        self.max_queue_size = 1
        
        # Create event clips directory
        os.makedirs(self.event_clips_dir, exist_ok=True)
        
        # Load model in separate thread
        self.model_thread = threading.Thread(target=self.load_model)
        self.model_thread.daemon = True
        self.model_thread.start()

    def load_model(self):
        """Load YOLO model for people detection"""
        try:
            print("🤖 Loading Enhanced YOLO model...")
            start_time = time.time()
            
            self.model = YOLO('yolov8n.pt')
            print(f"[EnhancedPeopleDetector] Model device: {self.model.device}")
            self.model.fuse()
            
            # Warm up the model
            dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
            for _ in range(3):
                self.model(dummy_input, verbose=False)
                
            self.model_loaded = True
            elapsed = time.time() - start_time
            print(f"✅ Enhanced YOLO model loaded successfully in {elapsed:.2f} seconds")
        except Exception as e:
            print(f"❌ Error loading Enhanced YOLO model: {e}")
            self.model_loaded = False

    def enable_detection(self, camera_id, enabled=True):
        """Enable or disable detection for a specific camera"""
        self.detection_enabled[camera_id] = enabled
        if enabled:
            self._initialize_camera_tracking(camera_id)
            
            # Start detection thread if not already running
            if camera_id not in self.detection_threads or not self.detection_threads[camera_id].isRunning():
                self.detection_threads[camera_id] = EnhancedDetectionThread(self, camera_id)
                self.detection_threads[camera_id].daemon = True
                self.detection_threads[camera_id].start()
        else:
            self._cleanup_camera_resources(camera_id)
                
        print(f"🔍 Enhanced people detection {'enabled' if enabled else 'disabled'} for camera {camera_id}")

    def enable_panic_detection(self, camera_id, enabled=True):
        """Enable or disable panic behavior detection"""
        self.panic_detection_enabled[camera_id] = enabled
        print(f"🚨 Panic behavior detection {'enabled' if enabled else 'disabled'} for camera {camera_id}")

    def _initialize_camera_tracking(self, camera_id):
        """Initialize tracking structures for a camera"""
        if camera_id not in self.tracked_objects:
            self.tracked_objects[camera_id] = {}
            self.object_trajectories[camera_id] = {}
            self.behavior_history[camera_id] = {}
            self.object_id_counter[camera_id] = 0
            self.event_buffers[camera_id] = deque(maxlen=self.max_buffer_frames)
            self.recording_events[camera_id] = {}
        
        if camera_id not in self.frame_skip:
            self.frame_skip[camera_id] = 0
        if camera_id not in self.detection_queue:
            self.detection_queue[camera_id] = []

    def _cleanup_camera_resources(self, camera_id):
        """Clean up resources when detection is disabled"""
        if camera_id in self.detection_queue:
            self.detection_queue[camera_id] = []

    def detect_people(self, camera_id, frame):
        """Queue frame for detection and return the most recent results"""
        if not self.model_loaded or not self.detection_enabled.get(camera_id, False):
            return frame, [], 0

        # Add frame to event buffer for potential clip creation
        if camera_id in self.event_buffers:
            self.event_buffers[camera_id].append({
                'frame': frame.copy(),
                'timestamp': time.time()
            })

        # Skip frames to reduce processing load
        if camera_id in self.frame_skip:
            self.frame_skip[camera_id] += 1
            if self.frame_skip[camera_id] < self.process_every_n_frames:
                if camera_id in self.last_detections:
                    last_frame, last_detections, last_count = self.last_detections[camera_id]
                    annotated_frame = frame.copy()
                    
                    for detection in last_detections:
                        x1, y1, x2, y2 = detection['bbox']
                        confidence = detection['confidence']
                        self._draw_box(annotated_frame, x1, y1, x2, y2, confidence)
                    
                    if self.is_counting_line_enabled(camera_id):
                        self._draw_counting_line(annotated_frame, camera_id)
                    
                    self._draw_count_text(annotated_frame, last_count, camera_id)
                    return annotated_frame, last_detections, last_count
                return frame, [], 0
            else:
                self.frame_skip[camera_id] = 0
        
        # Add frame to processing queue
        if camera_id in self.detection_queue:
            self.detection_queue[camera_id] = [frame.copy()]
        
        if camera_id not in self.last_detections:
            return frame, [], 0
            
        last_frame, last_detections, last_count = self.last_detections[camera_id]
        return last_frame, last_detections, last_count

    def _process_detection(self, camera_id, frame):
        """Process detection with enhanced panic behavior analysis"""
        if not self.model_loaded:
            return
            
        try:
            start_time = time.time()
            frame_copy = frame.copy()
            
            # Resize for faster processing if needed
            h, w = frame_copy.shape[:2]
            resized = False
            resized_frame = frame_copy
            
            if h > 720 or w > 1280:
                scale = min(720 / h, 1280 / w)
                new_h, new_w = int(h * scale), int(w * scale)
                resized_frame = cv2.resize(frame_copy, (new_w, new_h))
                resized = True
            
            # Run detection
            results = self.model(resized_frame, verbose=False)
            
            detections = []
            count = 0
            annotated_frame = frame_copy.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        if class_id == 0 and confidence >= self.confidence_threshold:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                            
                            if resized:
                                scale_factor = w / new_w
                                x1, x2 = int(x1 * scale_factor), int(x2 * scale_factor)
                                y1, y2 = int(y1 * scale_factor), int(y2 * scale_factor)
                            
                            area = (x2 - x1) * (y2 - y1)
                            if area < self.min_area:
                                continue
                                
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            
                            detections.append({
                                'bbox': (x1, y1, x2, y2),
                                'center': (center_x, center_y),
                                'confidence': confidence,
                                'class_id': class_id,
                                'area': area
                            })
                            count += 1
                            self._draw_enhanced_box(annotated_frame, x1, y1, x2, y2, confidence)
            
            # Enhanced tracking and behavior analysis
            if self.panic_detection_enabled.get(camera_id, False):
                panic_info = self._analyze_panic_behavior(camera_id, detections, frame_copy)
                if panic_info['panic_detected']:
                    self._handle_panic_event(camera_id, panic_info, frame_copy)
            
            # Process line crossing if enabled
            if self.is_counting_line_enabled(camera_id):
                self._process_line_crossing(camera_id, detections, annotated_frame)
                self._draw_counting_line(annotated_frame, camera_id)
                
            # Update object tracking
            self._update_object_tracking(camera_id, detections)
            
            # Smooth the count and draw info
            smoothed_count = self._smooth_count(camera_id, count)
            self._draw_enhanced_count_text(annotated_frame, smoothed_count, camera_id)
            
            # Store results
            self.last_detections[camera_id] = (annotated_frame, detections, smoothed_count)
            self.last_detection_time[camera_id] = time.time()
            
            # Emit signal with results
            self.detection_result.emit(camera_id, annotated_frame, detections, smoothed_count)
            
        except Exception as e:
            print(f"❌ Enhanced detection error for camera {camera_id}: {e}")

    def _analyze_panic_behavior(self, camera_id, detections, frame):
        """Analyze detections for panic behavior patterns"""
        panic_info = {
            'panic_detected': False,
            'behaviors': [],
            'confidence': 0.0,
            'people_count': len(detections),
            'timestamp': time.time()
        }
        
        if len(detections) < 2:  # Need at least 2 people for crowd analysis
            return panic_info
        
        # Analyze movement patterns
        rapid_movements = 0
        erratic_movements = 0
        running_detected = 0
        
        for detection in detections:
            center = detection['center']
            detection_id = self._get_closest_tracked_object(camera_id, center)
            
            if detection_id and detection_id in self.object_trajectories[camera_id]:
                trajectory = self.object_trajectories[camera_id][detection_id]
                
                if len(trajectory) >= 3:
                    # Calculate movement speed
                    recent_positions = trajectory[-3:]
                    speeds = []
                    for i in range(1, len(recent_positions)):
                        dx = recent_positions[i][0] - recent_positions[i-1][0]
                        dy = recent_positions[i][1] - recent_positions[i-1][1]
                        speed = np.sqrt(dx*dx + dy*dy)
                        speeds.append(speed)
                    
                    avg_speed = np.mean(speeds) if speeds else 0
                    
                    # Check for rapid movement (potential running)
                    if avg_speed > self.panic_thresholds['running_speed']:
                        running_detected += 1
                        panic_info['behaviors'].append('running')
                    elif avg_speed > self.panic_thresholds['rapid_movement']:
                        rapid_movements += 1
                        panic_info['behaviors'].append('rapid_movement')
                    
                    # Check for erratic movement (direction changes)
                    if len(recent_positions) >= 3:
                        directions = []
                        for i in range(1, len(recent_positions)):
                            dx = recent_positions[i][0] - recent_positions[i-1][0]
                            dy = recent_positions[i][1] - recent_positions[i-1][1]
                            if dx != 0 or dy != 0:
                                angle = np.arctan2(dy, dx)
                                directions.append(angle)
                        
                        if len(directions) >= 2:
                            direction_changes = 0
                            for i in range(1, len(directions)):
                                angle_diff = abs(directions[i] - directions[i-1])
                                if angle_diff > self.panic_thresholds['erratic_movement']:
                                    direction_changes += 1
                            
                            if direction_changes >= 1:
                                erratic_movements += 1
                                panic_info['behaviors'].append('erratic_movement')
        
        # Analyze crowd density and sudden gathering
        frame_area = frame.shape[0] * frame.shape[1]
        people_area = sum([det['area'] for det in detections])
        density = people_area / frame_area
        
        if density > self.panic_thresholds['crowd_density']:
            panic_info['behaviors'].append('high_density')
        
        # Check for sudden increase in people count
        if camera_id in self.count_history and len(self.count_history[camera_id]) > 0:
            prev_count = self.count_history[camera_id][-1]
            current_count = len(detections)
            if current_count - prev_count >= self.panic_thresholds['sudden_gathering']:
                panic_info['behaviors'].append('sudden_gathering')
        
        # Calculate overall panic confidence
        behavior_weights = {
            'running': 0.4,
            'rapid_movement': 0.2,
            'erratic_movement': 0.2,
            'high_density': 0.1,
            'sudden_gathering': 0.1
        }
        
        confidence = 0.0
        for behavior in panic_info['behaviors']:
            if behavior in behavior_weights:
                confidence += behavior_weights[behavior]
        
        # Additional factors
        if running_detected >= 2:
            confidence += 0.3  # Multiple people running
        if rapid_movements >= 3:
            confidence += 0.2  # Multiple rapid movements
        
        panic_info['confidence'] = min(confidence, 1.0)
        panic_info['panic_detected'] = confidence > 0.5
        
        return panic_info

    def _handle_panic_event(self, camera_id, panic_info, frame):
        """Handle detected panic event and create event clip"""
        print(f"🚨 Panic behavior detected on camera {camera_id}: {panic_info['behaviors']}")
        
        # Emit panic behavior signal
        self.panic_behavior_detected.emit(camera_id, panic_info, panic_info['confidence'])
        
        # Start recording event clip if not already recording
        event_id = f"panic_{int(time.time())}"
        if event_id not in self.recording_events[camera_id]:
            self._start_event_recording(camera_id, event_id, 'panic', panic_info)

    def _start_event_recording(self, camera_id, event_id, event_type, event_info):
        """Start recording an event clip"""
        try:
            # Create event data
            event_data = {
                'event_id': event_id,
                'camera_id': camera_id,
                'event_type': event_type,
                'start_time': time.time(),
                'info': event_info,
                'frames': []
            }
            
            # Add pre-event frames from buffer
            if camera_id in self.event_buffers:
                for buffered_frame in list(self.event_buffers[camera_id]):
                    event_data['frames'].append(buffered_frame)
            
            self.recording_events[camera_id][event_id] = event_data
            
            # Schedule clip completion
            clip_thread = threading.Thread(
                target=self._complete_event_recording,
                args=(camera_id, event_id)
            )
            clip_thread.daemon = True
            clip_thread.start()
            
        except Exception as e:
            print(f"❌ Error starting event recording: {e}")

    def _complete_event_recording(self, camera_id, event_id):
        """Complete event recording and save clip"""
        try:
            # Wait for clip duration
            time.sleep(self.clip_duration - self.buffer_duration)
            
            if event_id not in self.recording_events[camera_id]:
                return
            
            event_data = self.recording_events[camera_id][event_id]
            
            # Create video file
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(event_data['start_time']))
            clip_filename = f"{camera_id}_{event_data['event_type']}_{timestamp}.mp4"
            clip_path = os.path.join(self.event_clips_dir, clip_filename)
            
            if event_data['frames']:
                first_frame = event_data['frames'][0]['frame']
                h, w = first_frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(clip_path, fourcc, 30.0, (w, h))
                
                # Write frames with overlays
                for frame_data in event_data['frames']:
                    frame = frame_data['frame'].copy()
                    
                    # Add event overlay
                    self._add_event_overlay(frame, event_data)
                    
                    video_writer.write(frame)
                
                video_writer.release()
                
                # Save event metadata
                metadata_path = clip_path.replace('.mp4', '_metadata.json')
                with open(metadata_path, 'w') as f:
                    json.dump({
                        'event_id': event_data['event_id'],
                        'camera_id': event_data['camera_id'],
                        'event_type': event_data['event_type'],
                        'start_time': event_data['start_time'],
                        'duration': self.clip_duration,
                        'info': event_data['info']
                    }, f, indent=2)
                
                print(f"✅ Event clip saved: {clip_path}")
                
                # Emit signal that clip is ready
                self.event_clip_ready.emit(camera_id, clip_path, event_data)
            
            # Clean up
            del self.recording_events[camera_id][event_id]
            
        except Exception as e:
            print(f"❌ Error completing event recording: {e}")

    def _add_event_overlay(self, frame, event_data):
        """Add event information overlay to frame"""
        try:
            # Event type banner
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 0, 255), -1)
            
            event_text = f"🚨 {event_data['event_type'].upper()} EVENT DETECTED"
            cv2.putText(frame, event_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            # Timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event_data['start_time']))
            cv2.putText(frame, timestamp, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Event details
            if 'behaviors' in event_data['info']:
                behaviors_text = f"Behaviors: {', '.join(event_data['info']['behaviors'])}"
                cv2.putText(frame, behaviors_text, (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"❌ Error adding event overlay: {e}")

    # Include other methods from original PeopleDetector
    def _get_closest_tracked_object(self, camera_id, center):
        """Find closest tracked object to given center point"""
        if camera_id not in self.tracked_objects:
            return None
        
        min_distance = float('inf')
        closest_id = None
        
        for obj_id, obj_data in self.tracked_objects[camera_id].items():
            if len(obj_data['center_history']) > 0:
                last_center = obj_data['center_history'][-1]
                distance = np.sqrt((center[0] - last_center[0])**2 + (center[1] - last_center[1])**2)
                if distance < 100 and distance < min_distance:
                    min_distance = distance
                    closest_id = obj_id
        
        return closest_id

    def _update_object_tracking(self, camera_id, detections):
        """Update object tracking with trajectory analysis"""
        if camera_id not in self.tracked_objects:
            return
        
        current_objects = {}
        
        for detection in detections:
            center = detection['center']
            matched_id = self._get_closest_tracked_object(camera_id, center)
            
            if matched_id is not None:
                # Update existing object
                current_objects[matched_id] = {
                    'center_history': self.tracked_objects[camera_id][matched_id]['center_history'] + [center],
                    'last_seen': 0
                }
                
                # Update trajectory
                if matched_id not in self.object_trajectories[camera_id]:
                    self.object_trajectories[camera_id][matched_id] = deque(maxlen=10)
                self.object_trajectories[camera_id][matched_id].append(center)
                
                # Keep only recent positions
                if len(current_objects[matched_id]['center_history']) > 10:
                    current_objects[matched_id]['center_history'] = current_objects[matched_id]['center_history'][-10:]
            else:
                # Create new object
                new_id = self.object_id_counter[camera_id]
                self.object_id_counter[camera_id] += 1
                current_objects[new_id] = {
                    'center_history': [center],
                    'last_seen': 0
                }
                self.object_trajectories[camera_id][new_id] = deque(maxlen=10)
                self.object_trajectories[camera_id][new_id].append(center)
        
        self.tracked_objects[camera_id] = current_objects

    def _draw_enhanced_box(self, frame, x1, y1, x2, y2, confidence):
        """Draw enhanced bounding box with behavior indicators"""
        color = (0, 255, 0)
        label = f"Person {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Draw main box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label_size = cv2.getTextSize(label, font, 0.5, 2)[0]
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), font, 0.5, (0, 0, 0), 2)

    def _draw_enhanced_count_text(self, frame, count, camera_id):
        """Draw enhanced count text with panic indicators"""
        # People count
        text = f"People: {count}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        h, w = frame.shape[:2]
        x, y = w - text_size[0] - 30, 40

        cv2.rectangle(frame, (x - 10, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
        cv2.putText(frame, text, (x, y), font, font_scale, (0, 255, 0), thickness)

        # Panic detection status
        if self.panic_detection_enabled.get(camera_id, False):
            panic_text = "🚨 Panic Detection: ON"
            panic_size = cv2.getTextSize(panic_text, font, 0.5, 1)[0]
            panic_x, panic_y = 20, h - 80
            cv2.rectangle(frame, (panic_x - 5, panic_y - panic_size[1] - 5), 
                         (panic_x + panic_size[0] + 5, panic_y + 5), (255, 0, 0), -1)
            cv2.putText(frame, panic_text, (panic_x, panic_y), font, 0.5, (255, 255, 255), 1)

    # Include other necessary methods from original detector
    def is_counting_line_enabled(self, camera_id):
        return camera_id in self.counting_lines and self.counting_lines[camera_id]['enabled']

    def _process_line_crossing(self, camera_id, detections, frame):
        """Process line crossing detection"""
        # Implementation from original detector
        pass

    def _draw_counting_line(self, frame, camera_id):
        """Draw counting line"""
        # Implementation from original detector
        pass

    def _smooth_count(self, camera_id, new_count):
        """Apply moving average to smooth people count"""
        if camera_id not in self.count_history:
            self.count_history[camera_id] = []
        history = self.count_history[camera_id]
        history.append(new_count)
        if len(history) > self.smoothing_frames:
            history.pop(0)
        return int(round(sum(history) / len(history)))


class EnhancedDetectionThread(QThread):
    """Enhanced thread for running detection in background"""
    
    def __init__(self, detector, camera_id):
        super().__init__()
        self.detector = detector
        self.camera_id = camera_id
        self.running = True
        
    def run(self):
        """Main thread loop"""
        print(f"🧵 Starting enhanced detection thread for camera {self.camera_id}")
        
        while self.running and self.detector.detection_enabled.get(self.camera_id, False):
            if (self.camera_id in self.detector.detection_queue and 
                len(self.detector.detection_queue[self.camera_id]) > 0):
                
                frame = self.detector.detection_queue[self.camera_id].pop(0)
                self.detector._process_detection(self.camera_id, frame)
                
                # Continue recording event frames
                for event_id, event_data in list(self.detector.recording_events[self.camera_id].items()):
                    if len(event_data['frames']) < self.detector.clip_duration * 30:  # 30 fps
                        event_data['frames'].append({
                            'frame': frame.copy(),
                            'timestamp': time.time()
                        })
            
            time.sleep(0.01)
            
        print(f"🛑 Enhanced detection thread for camera {self.camera_id} stopped")
        
    def stop(self):
        """Stop the thread"""
        self.running = False
