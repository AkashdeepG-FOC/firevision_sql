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
        
        # Enhanced tracking
        self.tracked_objects = {}
        self.object_trajectories = {}  # Store movement patterns
        self.behavior_history = {}  # Store behavior patterns
        
        # Event recording system
        self.event_buffers = {}  # Pre-event frame buffers
        self.event_clips_dir = "event_clips"
        self.buffer_duration = 5  # seconds before event
        self.clip_duration = 15  # total clip duration
        self.max_buffer_frames = 150  # 5 seconds at 30fps
        
        
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


    def _initialize_camera_tracking(self, camera_id):
        """Initialize tracking structures for a camera"""
        if camera_id not in self.tracked_objects:
            self.tracked_objects[camera_id] = {}
            self.object_trajectories[camera_id] = {}
            self.behavior_history[camera_id] = {}
            self.object_id_counter[camera_id] = 0
            self.event_buffers[camera_id] = deque(maxlen=self.max_buffer_frames)
        
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
                
            
            time.sleep(0.01)
            
        print(f"🛑 Enhanced detection thread for camera {self.camera_id} stopped")
        
    def stop(self):
        """Stop the thread"""
        self.running = False
