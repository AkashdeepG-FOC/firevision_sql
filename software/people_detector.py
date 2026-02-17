import cv2
import numpy as np
import time
import threading
import sys
import os
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    print("Warning: ultralytics not found. People detection disabled.")
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from workers.base_worker import BaseWorker, WorkerStatus


class PeopleDetector(QObject):
    """YOLOv8-based people detection system with line crossing detection for people counting"""
    
    detection_result = pyqtSignal(str, np.ndarray, list, int)  # camera_id, frame_with_boxes, detections, people_count
    line_crossing = pyqtSignal(str, str, int, int)  # camera_id, direction ('in'/'out'), in_count, out_count

    def __init__(self):
        super().__init__()
        self.model = None
        self.model_loaded = False
        self.detection_enabled = {}
        self.confidence_threshold = 0.5
        self.min_area = 3000
        self.count_history = {}  # camera_id -> list of last N counts
        self.smoothing_frames = 5  # Reduced from 10 for faster response
        
        # Line crossing detection
        self.counting_lines = {}  # camera_id -> {start_point, end_point, enabled}
        self.tracked_objects = {}  # camera_id -> {object_id: {center_history, last_seen}}
        self.line_counts = {}  # camera_id -> {in_count, out_count}
        self.object_id_counter = {}  # camera_id -> counter for unique object IDs
        
        # Performance optimization
        self.frame_skip = {}  # camera_id -> counter for frame skipping
        self.process_every_n_frames = 3  # Process every Nth frame for detection
        self.last_detection_time = {}  # camera_id -> timestamp of last detection
        self.last_detections = {}  # camera_id -> last detection results
        self.detection_threads = {}  # camera_id -> detection thread
        self.detection_queue = {}  # camera_id -> queue of frames for processing
        self.max_queue_size = 1  # Only keep the latest frame in queue
        
        # Load model in a separate thread to avoid blocking UI
        self.model_thread = threading.Thread(target=self.load_model)
        self.model_thread.daemon = True
        self.model_thread.start()

    def load_model(self):
        """Load YOLO model for people detection"""
        try:
            print("🤖 Loading YOLO model...")
            start_time = time.time()
            
            # Use a smaller model for faster inference
            if HAS_YOLO:
                # Look for model in models/ subdirectory
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                model_path = os.path.join(base_path, 'models', 'yolov8n.pt')
                
                # Fallback for development (current directory)
                if not os.path.exists(model_path):
                    model_path = 'yolov8n.pt'
                
                if os.path.exists(model_path):
                    print(f"[PeopleDetector] Loading model from: {model_path}")
                    self.model = YOLO(model_path)
                    print(f"[PeopleDetector] Model device: {self.model.device}")
                    
                    # Optimize model for inference
                    self.model.fuse()  # Fuse layers for faster inference
                    
                    # Warm up the model
                    dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
                    for _ in range(3):  # Run a few times to warm up
                        self.model(dummy_input, verbose=False)
                        
                    self.model_loaded = True
                    elapsed = time.time() - start_time
                    print(f"✅ YOLO model loaded successfully in {elapsed:.2f} seconds")
                else:
                    print(f"⚠️ YOLO model not found at {model_path} - People detection disabled")
                    self.model_loaded = False
            else:
                print("⚠️ YOLO not available - People detection disabled")
                self.model_loaded = False
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            self.model_loaded = False

    def enable_detection(self, camera_id, enabled=True):
        """Enable or disable detection for a specific camera"""
        self.detection_enabled[camera_id] = enabled
        if enabled:
            if camera_id not in self.tracked_objects:
                self.tracked_objects[camera_id] = {}
                self.object_id_counter[camera_id] = 0
            if camera_id not in self.frame_skip:
                self.frame_skip[camera_id] = 0
            if camera_id not in self.detection_queue:
                self.detection_queue[camera_id] = []
                
            # Start detection thread if not already running
            if camera_id not in self.detection_threads or not self.detection_threads[camera_id].isRunning():
                self.detection_threads[camera_id] = DetectionThread(self, camera_id)
                self.detection_threads[camera_id].daemon = True
                self.detection_threads[camera_id].start()
        else:
            # Clean up resources when detection is disabled
            if camera_id in self.detection_queue:
                self.detection_queue[camera_id] = []
                
        print(f"🔍 People detection {'enabled' if enabled else 'disabled'} for camera {camera_id}")

    def is_detection_enabled(self, camera_id):
        """Check if detection is enabled for a camera"""
        return self.detection_enabled.get(camera_id, False)

    def set_counting_line(self, camera_id, start_point, end_point, enabled=True):
        """Set the counting line for a camera"""
        self.counting_lines[camera_id] = {
            'start_point': start_point,
            'end_point': end_point,
            'enabled': enabled
        }
        if camera_id not in self.line_counts:
            self.line_counts[camera_id] = {'in_count': 0, 'out_count': 0}
        print(f"📏 Counting line set for camera {camera_id}: {start_point} -> {end_point}")

    def is_counting_line_enabled(self, camera_id):
        """Check if counting line is enabled for a camera"""
        return camera_id in self.counting_lines and self.counting_lines[camera_id]['enabled']

    def get_line_counts(self, camera_id):
        """Get in/out counts for a camera"""
        return self.line_counts.get(camera_id, {'in_count': 0, 'out_count': 0})

    def reset_line_counts(self, camera_id):
        """Reset line counts for a camera"""
        if camera_id in self.line_counts:
            self.line_counts[camera_id] = {'in_count': 0, 'out_count': 0}

    def detect_people(self, camera_id, frame):
        """Queue frame for detection and return the most recent results"""
        if not self.model_loaded or not self.is_detection_enabled(camera_id):
            return frame, [], 0

        # Skip frames to reduce processing load
        if camera_id in self.frame_skip:
            self.frame_skip[camera_id] += 1
            if self.frame_skip[camera_id] < self.process_every_n_frames:
                # Return the last detection results if available
                if camera_id in self.last_detections:
                    last_frame, last_detections, last_count = self.last_detections[camera_id]
                    
                    # Create a fresh copy of the current frame
                    annotated_frame = frame.copy()
                    
                    # Draw the last detections on the new frame
                    for detection in last_detections:
                        x1, y1, x2, y2 = detection['bbox']
                        confidence = detection['confidence']
                        self._draw_box(annotated_frame, x1, y1, x2, y2, confidence)
                    
                    # Draw counting line if enabled
                    if self.is_counting_line_enabled(camera_id):
                        self._draw_counting_line(annotated_frame, camera_id)
                    
                    # Draw count text
                    self._draw_count_text(annotated_frame, last_count, camera_id)
                    
                    return annotated_frame, last_detections, last_count
                return frame, [], 0
            else:
                self.frame_skip[camera_id] = 0
        
        # Add frame to processing queue (replace any existing frame)
        if camera_id in self.detection_queue:
            self.detection_queue[camera_id] = [frame.copy()]  # Only keep the latest frame
        
        # If we don't have any previous detections, return the original frame
        if camera_id not in self.last_detections:
            return frame, [], 0
            
        # Return the last detection results
        last_frame, last_detections, last_count = self.last_detections[camera_id]
        return last_frame, last_detections, last_count

    def _process_detection(self, camera_id, frame):
        """Process detection in background thread"""
        if not self.model_loaded:
            return
            
        try:
            start_time = time.time()
            
            # Create a copy to avoid modifying the original
            frame_copy = frame.copy()
            
            # Resize frame for faster processing if it's large
            h, w = frame_copy.shape[:2]
            resized = False
            resized_frame = frame_copy
            
            if h > 720 or w > 1280:
                # Resize to 720p for faster processing
                scale = min(720 / h, 1280 / w)
                new_h, new_w = int(h * scale), int(w * scale)
                resized_frame = cv2.resize(frame_copy, (new_w, new_h))
                resized = True
            
            # Run detection on resized frame
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
                        
                        if class_id == 0 and confidence >= self.confidence_threshold:  # 0 = person
                            # Get coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                            
                            # Scale back if we resized
                            if resized:
                                scale_factor = w / new_w
                                x1, x2 = int(x1 * scale_factor), int(x2 * scale_factor)
                                y1, y2 = int(y1 * scale_factor), int(y2 * scale_factor)
                            
                            area = (x2 - x1) * (y2 - y1)
                            if area < self.min_area:
                                continue  # Skip small detections
                                
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            
                            detections.append({
                                'bbox': (x1, y1, x2, y2),
                                'center': (center_x, center_y),
                                'confidence': confidence,
                                'class_id': class_id
                            })
                            count += 1
                            self._draw_box(annotated_frame, x1, y1, x2, y2, confidence)
            
            # Process line crossing if enabled
            if self.is_counting_line_enabled(camera_id):
                self._process_line_crossing(camera_id, detections, annotated_frame)
                
            # Draw counting line if enabled
            if self.is_counting_line_enabled(camera_id):
                self._draw_counting_line(annotated_frame, camera_id)
                
            # Smooth the count
            smoothed_count = self._smooth_count(camera_id, count)
            self._draw_count_text(annotated_frame, smoothed_count, camera_id)
            
            # Store the results
            self.last_detections[camera_id] = (annotated_frame, detections, smoothed_count)
            self.last_detection_time[camera_id] = time.time()
            
            # Calculate and log processing time
            elapsed = time.time() - start_time
            fps = 1.0 / elapsed if elapsed > 0 else 0
            print(f"🔍 Detection for camera {camera_id}: {count} people, {elapsed:.3f}s ({fps:.1f} FPS)")
            
            # Emit signal with results
            self.detection_result.emit(camera_id, annotated_frame, detections, smoothed_count)
            
        except Exception as e:
            print(f"❌ Detection error for camera {camera_id}: {e}")

    def _process_line_crossing(self, camera_id, detections, frame):
        """Process line crossing detection for people counting"""
        if camera_id not in self.tracked_objects:
            self.tracked_objects[camera_id] = {}
            self.object_id_counter[camera_id] = 0

        current_objects = {}
        line_info = self.counting_lines[camera_id]
        
        # Match detections to existing tracked objects or create new ones
        for detection in detections:
            center = detection['center']
            matched_id = None
            min_distance = float('inf')
            
            # Find closest existing object
            for obj_id, obj_data in self.tracked_objects[camera_id].items():
                if len(obj_data['center_history']) > 0:
                    last_center = obj_data['center_history'][-1]
                    distance = np.sqrt((center[0] - last_center[0])**2 + (center[1] - last_center[1])**2)
                    if distance < 100 and distance < min_distance:  # 100 pixel threshold
                        min_distance = distance
                        matched_id = obj_id
            
            if matched_id is not None:
                # Update existing object
                current_objects[matched_id] = {
                    'center_history': self.tracked_objects[camera_id][matched_id]['center_history'] + [center],
                    'last_seen': 0
                }
                # Keep only last 5 positions (reduced from 10)
                if len(current_objects[matched_id]['center_history']) > 5:
                    current_objects[matched_id]['center_history'] = current_objects[matched_id]['center_history'][-5:]
            else:
                # Create new object
                new_id = self.object_id_counter[camera_id]
                self.object_id_counter[camera_id] += 1
                current_objects[new_id] = {
                    'center_history': [center],
                    'last_seen': 0
                }

        # Check for line crossings
        for obj_id, obj_data in current_objects.items():
            if len(obj_data['center_history']) >= 2:
                # Check if the last two points cross the line
                p1 = obj_data['center_history'][-2]
                p2 = obj_data['center_history'][-1]
                
                if self._line_intersection(p1, p2, line_info['start_point'], line_info['end_point']):
                    # Determine direction based on line orientation and movement
                    direction = self._determine_crossing_direction(
                        p1, p2, line_info['start_point'], line_info['end_point']
                    )
                    
                    if direction == 'in':
                        self.line_counts[camera_id]['in_count'] += 1
                    elif direction == 'out':
                        self.line_counts[camera_id]['out_count'] += 1
                    
                    print(f"🚶 Person crossed line {direction} - In: {self.line_counts[camera_id]['in_count']}, Out: {self.line_counts[camera_id]['out_count']}")
                    
                    # Emit line crossing signal
                    self.line_crossing.emit(
                        camera_id, 
                        direction, 
                        self.line_counts[camera_id]['in_count'],
                        self.line_counts[camera_id]['out_count']
                    )

        # Update tracked objects
        self.tracked_objects[camera_id] = current_objects

    def _line_intersection(self, p1, p2, line_start, line_end):
        """Check if line segment p1-p2 intersects with line segment line_start-line_end"""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, line_start, line_end) != ccw(p2, line_start, line_end) and \
               ccw(p1, p2, line_start) != ccw(p1, p2, line_end)

    def _determine_crossing_direction(self, p1, p2, line_start, line_end):
        """Determine if crossing is 'in' or 'out' based on movement direction"""
        # Calculate line vector
        line_vec = (line_end[0] - line_start[0], line_end[1] - line_start[1])
        # Calculate movement vector
        move_vec = (p2[0] - p1[0], p2[1] - p1[1])
        
        # Cross product to determine which side
        cross_product = line_vec[0] * move_vec[1] - line_vec[1] * move_vec[0]
        
        return 'in' if cross_product > 0 else 'out'

    def _draw_counting_line(self, frame, camera_id):
        """Draw the counting line on the frame"""
        if camera_id in self.counting_lines:
            line_info = self.counting_lines[camera_id]
            start_point = line_info['start_point']
            end_point = line_info['end_point']
            
            # Draw line
            cv2.line(frame, start_point, end_point, (0, 255, 255), 3)  # Yellow line
            
            # Draw endpoints
            cv2.circle(frame, start_point, 8, (0, 255, 0), -1)  # Green start
            cv2.circle(frame, end_point, 8, (0, 0, 255), -1)    # Red end
            
            # Draw direction arrows
            mid_point = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
            
            # Calculate perpendicular direction for arrows
            line_vec = (end_point[0] - start_point[0], end_point[1] - start_point[1])
            length = np.sqrt(line_vec[0]**2 + line_vec[1]**2)
            if length > 0:
                perp_vec = (-line_vec[1] / length * 30, line_vec[0] / length * 30)
                
                # "IN" arrow (pointing to one side)
                in_point = (int(mid_point[0] + perp_vec[0]), int(mid_point[1] + perp_vec[1]))
                cv2.arrowedLine(frame, mid_point, in_point, (0, 255, 0), 2)
                cv2.putText(frame, "IN", (in_point[0] + 5, in_point[1] - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # "OUT" arrow (pointing to other side)
                out_point = (int(mid_point[0] - perp_vec[0]), int(mid_point[1] - perp_vec[1]))
                cv2.arrowedLine(frame, mid_point, out_point, (0, 0, 255), 2)
                cv2.putText(frame, "OUT", (out_point[0] + 5, out_point[1] - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    def _draw_box(self, frame, x1, y1, x2, y2, confidence):
        """Draw bounding box and label"""
        color = (0, 255, 0)
        label = f"Person {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label_size = cv2.getTextSize(label, font, 0.5, 2)[0]
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), font, 0.5, (0, 0, 0), 2)

    def _draw_count_text(self, frame, count, camera_id):
        """Draw the people count and line crossing counts on the frame"""
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

        # Line crossing counts
        if self.is_counting_line_enabled(camera_id):
            counts = self.get_line_counts(camera_id)
            in_text = f"IN: {counts['in_count']}"
            out_text = f"OUT: {counts['out_count']}"
            
            # Draw IN count
            in_size = cv2.getTextSize(in_text, font, 0.7, 2)[0]
            in_x, in_y = 20, 40
            cv2.rectangle(frame, (in_x - 5, in_y - in_size[1] - 5), (in_x + in_size[0] + 5, in_y + 5), (0, 255, 0), -1)
            cv2.putText(frame, in_text, (in_x, in_y), font, 0.7, (0, 0, 0), 2)
            
            # Draw OUT count
            out_size = cv2.getTextSize(out_text, font, 0.7, 2)[0]
            out_x, out_y = 20, 80
            cv2.rectangle(frame, (out_x - 5, out_y - out_size[1] - 5), (out_x + out_size[0] + 5, out_y + 5), (0, 0, 255), -1)
            cv2.putText(frame, out_text, (out_x, out_y), font, 0.7, (255, 255, 255), 2)

    def _smooth_count(self, camera_id, new_count):
        """Apply moving average to smooth people count"""
        if camera_id not in self.count_history:
            self.count_history[camera_id] = []
        history = self.count_history[camera_id]
        history.append(new_count)
        if len(history) > self.smoothing_frames:
            history.pop(0)
        return int(round(sum(history) / len(history)))

    def set_confidence_threshold(self, threshold):
        """Set detection confidence threshold"""
        self.confidence_threshold = max(0.1, min(1.0, threshold))
        print(f"🎯 Confidence threshold set to {self.confidence_threshold}")
        
    def set_frame_skip(self, n_frames):
        """Set number of frames to skip between detections"""
        self.process_every_n_frames = max(1, int(n_frames))
        print(f"⏭️ Processing every {self.process_every_n_frames} frames")


class DetectionThread(BaseWorker):
    """Thread for running detection in background"""
    
    def __init__(self, detector, camera_id):
        super().__init__(f"PeopleDetection_{camera_id}")
        self.detector = detector
        self.camera_id = camera_id
        
    def work(self):
        """Main thread loop - called by BaseWorker.run()"""
        print(f"🧵 Starting detection thread for camera {self.camera_id}")
        
        while self.is_running() and self.detector.is_detection_enabled(self.camera_id):
            # Check if there's a frame to process
            if (self.camera_id in self.detector.detection_queue and 
                len(self.detector.detection_queue[self.camera_id]) > 0):
                
                # Get the latest frame
                frame = self.detector.detection_queue[self.camera_id].pop(0)
                
                # Process the frame
                self.detector._process_detection(self.camera_id, frame)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.01)
            
        print(f"🛑 Detection thread for camera {self.camera_id} stopped")