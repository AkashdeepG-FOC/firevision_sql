import cv2
import numpy as np
import threading
import time
import datetime
import os
from PyQt5.QtCore import QObject, pyqtSignal
import queue
from fire_detection_model import CustomFireDetectionModel


class DetectionThread(threading.Thread):
    def __init__(self, camera_id, frame_queue, event_callback, annotated_frame_callback,
                 motion_sensitivity=0.5, object_confidence=0.5,
                 fire_detection_enabled=True):
        """
        Initialize a detection thread

        Args:
            camera_id (str): Camera ID
            frame_queue (queue.Queue): Queue for frames
            event_callback (callable): Callback for detection events
            annotated_frame_callback (callable): Callback for annotated frames
            motion_sensitivity (float): Motion detection sensitivity (0.0-1.0)
            object_confidence (float): Object detection confidence threshold (0.0-1.0)
            fire_detection_enabled (bool): Enable fire detection
        """
        super().__init__()
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.event_callback = event_callback
        self.annotated_frame_callback = annotated_frame_callback
        self.motion_sensitivity = motion_sensitivity
        self.object_confidence = object_confidence
        self.fire_detection_enabled = fire_detection_enabled
        self.running = False

        # Initialize motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )

        # Previous frame for motion detection
        self.prev_frame = None

        # Cooldown for events to prevent spam
        self.last_motion_event = 0
        self.last_object_event = 0
        self.last_fire_event = 0
        self.event_cooldown = 2.0  # seconds

        # Motion detection parameters
        self.min_contour_area = 500
        self.motion_threshold = 25

        # Fire detection model
        self.fire_model = None
        if fire_detection_enabled:
            print(f"Initializing fire detection for camera {camera_id}...")
            self.fire_model = CustomFireDetectionModel()
            if not self.fire_model.model_loaded:
                print(f"Failed to load fire detection model for camera {camera_id}")
                self.fire_detection_enabled = False
            else:
                print(f"Fire detection model loaded successfully for camera {camera_id}")

    def run(self):
        """Main detection loop"""
        self.running = True

        try:
            while self.running:
                # Get frame from queue with timeout
                try:
                    frame = self.frame_queue.get(timeout=1.0)
                    if frame is None:
                        continue
                except queue.Empty:
                    continue

                # Process frame for detections
                self._process_frame(frame)

        except Exception as e:
            print(f"Detection thread error for camera {self.camera_id}: {e}")

    def _process_frame(self, frame):
        """
        Process a frame for motion and fire detection

        Args:
            frame (numpy.ndarray): Frame to process
        """
        current_time = time.time()
        annotated_frame = frame.copy()
        has_detections = False

        # Fire detection (priority)
        if self.fire_detection_enabled and self.fire_model and (
                current_time - self.last_fire_event) > self.event_cooldown:
            fire_detections, fire_annotated_frame = self.fire_model.detect_fire(frame)

            if fire_detections:
                self.last_fire_event = current_time
                has_detections = True
                annotated_frame = fire_annotated_frame

                # Get highest confidence detection
                highest_conf_detection = max(fire_detections, key=lambda x: x["confidence"])

                # Create event
                event = {
                    "type": "fire",
                    "subtype": highest_conf_detection["class"].lower(),  # fire or smoke
                    "camera_id": self.camera_id,
                    "timestamp": datetime.datetime.now(),
                    "frame": fire_annotated_frame.copy(),
                    "confidence": highest_conf_detection["confidence"] * 100,  # Convert to percentage
                    "details": {
                        "detections": fire_detections,
                        "confidence_threshold": self.fire_model.confidence_threshold
                    }
                }

                # Call event callback
                if self.event_callback:
                    self.event_callback(event)

                # Send to backend
                try:
                    from backend_client import backend_client
                    # Map values to backend expectations
                    # Assuming camera_id is an integer for backend, but might be string in local
                    # We need to handle this mapping carefully. For now, assuming direct mapping or using a default.
                    # Or we should fetch the camera ID from backend first.
                    # For simplicity in this migration step, let's try to send it if it's numeric, or handle conversion.
                    
                    camera_db_id = 1 # Placeholder: In real app, map self.camera_id (e.g. "cam_1") to DB ID
                    
                    if str(self.camera_id).isdigit():
                        camera_db_id = int(self.camera_id)
                    
                    image_path = event.get('image_path', '')
                    
                    backend_client.create_alert(
                        camera_id=camera_db_id,
                        alert_type=highest_conf_detection["class"].lower(),
                        confidence=float(highest_conf_detection["confidence"]),
                        image_path=image_path
                    )
                except Exception as e:
                     print(f"Failed to send alert to backend: {e}")

                print(f"Fire detected on camera {self.camera_id}: {highest_conf_detection['class']} "
                      f"({highest_conf_detection['confidence']:.2f})")

        # Motion detection (if no fire detected)
        if not has_detections:
            motion_detected, motion_area = self._detect_motion(frame)

            # Handle motion event
            if motion_detected and (current_time - self.last_motion_event) > self.event_cooldown:
                self.last_motion_event = current_time

                # Add motion overlay to frame
                annotated_frame = self._add_motion_overlay(annotated_frame)

                # Create event
                event = {
                    "type": "motion",
                    "camera_id": self.camera_id,
                    "timestamp": datetime.datetime.now(),
                    "frame": annotated_frame.copy(),
                    "confidence": min(motion_area * 100, 100.0),  # Convert to percentage
                    "details": {
                        "motion_area": motion_area,
                        "sensitivity": self.motion_sensitivity
                    }
                }

                # Call event callback
                if self.event_callback:
                    self.event_callback(event)

        # Always send the annotated frame to the main window
        if self.annotated_frame_callback:
            self.annotated_frame_callback(self.camera_id, annotated_frame)

    def _add_motion_overlay(self, frame):
        """Add motion detection overlay to frame"""
        try:
            # Add motion indicator
            cv2.putText(frame, "MOTION DETECTED", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Add timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            return frame
        except Exception as e:
            print(f"Error adding motion overlay: {e}")
            return frame

    def _detect_motion(self, frame):
        """
        Detect motion in a frame using background subtraction

        Args:
            frame (numpy.ndarray): Frame to process

        Returns:
            tuple: (motion_detected: bool, motion_area: float)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Initialize previous frame if needed
            if self.prev_frame is None:
                self.prev_frame = gray
                return False, 0.0

            # Calculate absolute difference between frames
            frame_diff = cv2.absdiff(self.prev_frame, gray)

            # Apply threshold
            threshold = int(self.motion_threshold * (1.0 - self.motion_sensitivity))
            _, thresh = cv2.threshold(frame_diff, threshold, 255, cv2.THRESH_BINARY)

            # Dilate to fill holes
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.dilate(thresh, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Calculate total motion area
            motion_area = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_contour_area:
                    motion_area += area

            # Calculate relative motion area
            frame_area = frame.shape[0] * frame.shape[1]
            relative_motion = motion_area / frame_area if frame_area > 0 else 0

            # Update previous frame
            self.prev_frame = gray

            # Determine if motion is significant
            motion_threshold = 0.01 * self.motion_sensitivity
            motion_detected = relative_motion > motion_threshold

            return motion_detected, relative_motion

        except Exception as e:
            print(f"Error in motion detection: {e}")
            return False, 0.0

    def stop(self):
        """Stop the detection thread"""
        self.running = False
        self.join(timeout=5.0)

    def update_sensitivity(self, motion_sensitivity, object_confidence):
        """
        Update detection sensitivity parameters

        Args:
            motion_sensitivity (float): Motion detection sensitivity (0.0-1.0)
            object_confidence (float): Object detection confidence threshold (0.0-1.0)
        """
        self.motion_sensitivity = motion_sensitivity
        self.object_confidence = object_confidence

        # Update fire model confidence if available
        if self.fire_model:
            self.fire_model.set_confidence_threshold(object_confidence)

    def enable_fire_detection(self, enable=True):
        """
        Enable or disable fire detection

        Args:
            enable (bool): True to enable, False to disable

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if enable and not self.fire_detection_enabled:
                if not self.fire_model:
                    self.fire_model = CustomFireDetectionModel()

                if self.fire_model.model_loaded:
                    self.fire_detection_enabled = True
                    print(f"Fire detection enabled for camera {self.camera_id}")
                    return True
                else:
                    print(f"Failed to enable fire detection for camera {self.camera_id}")
                    return False
            elif not enable:
                self.fire_detection_enabled = False
                print(f"Fire detection disabled for camera {self.camera_id}")
                return True

            return self.fire_detection_enabled

        except Exception as e:
            print(f"Error enabling fire detection: {e}")
            return False


class DetectionManager(QObject):
    detection_event = pyqtSignal(dict)  # event dict
    annotated_frame_ready = pyqtSignal(str, np.ndarray)  # camera_id, annotated_frame

    def __init__(self):
        super().__init__()
        self.detectors = {}  # {camera_id: {thread, queue, settings}}
        self.events = []
        self.max_events = 1000
        self.events_dir = "detection_events"

        # Create events directory if it doesn't exist
        os.makedirs(self.events_dir, exist_ok=True)

        # Default settings
        self.default_settings = {
            "motion_enabled": True,
            "motion_sensitivity": 0.5,
            "object_enabled": False,
            "object_confidence": 0.7,
            "fire_enabled": True,
            "notifications_enabled": True,
            "sound_enabled": False
        }

    def start_detection(self, camera_id, motion_sensitivity=0.5, object_confidence=0.7, fire_detection=True):
        """
        Start detection for a camera

        Args:
            camera_id (str): Camera ID
            motion_sensitivity (float): Motion detection sensitivity (0.0-1.0)
            object_confidence (float): Object detection confidence threshold (0.0-1.0)
            fire_detection (bool): Enable fire detection

        Returns:
            bool: True if detection started successfully, False otherwise
        """
        if camera_id in self.detectors:
            return False  # Already detecting

        try:
            # Create frame queue and detection thread
            frame_queue = queue.Queue(maxsize=10)
            thread = DetectionThread(
                camera_id, frame_queue, self._handle_event, self._handle_annotated_frame,
                motion_sensitivity, object_confidence, fire_detection
            )

            # Store detector info
            self.detectors[camera_id] = {
                "thread": thread,
                "queue": frame_queue,
                "settings": {
                    "motion_sensitivity": motion_sensitivity,
                    "object_confidence": object_confidence,
                    "fire_detection": fire_detection
                }
            }

            # Start detection thread
            thread.start()

            print(f"Detection started for camera {camera_id}")
            return True

        except Exception as e:
            print(f"Error starting detection for camera {camera_id}: {e}")
            return False

    def _handle_annotated_frame(self, camera_id, annotated_frame):
        """
        Handle annotated frame from detection thread

        Args:
            camera_id (str): Camera ID
            annotated_frame (numpy.ndarray): Annotated frame
        """
        # Emit signal to update main window
        self.annotated_frame_ready.emit(camera_id, annotated_frame)

    def stop_detection(self, camera_id):
        """
        Stop detection for a camera

        Args:
            camera_id (str): Camera ID

        Returns:
            bool: True if detection stopped successfully, False otherwise
        """
        if camera_id not in self.detectors:
            return False

        try:
            # Get detector info
            detector = self.detectors[camera_id]
            thread = detector["thread"]

            # Stop thread
            thread.stop()

            # Remove from detectors
            del self.detectors[camera_id]

            print(f"Detection stopped for camera {camera_id}")
            return True

        except Exception as e:
            print(f"Error stopping detection for camera {camera_id}: {e}")
            return False

    def add_frame(self, camera_id, frame):
        """
        Add a frame to the detection queue for a camera

        Args:
            camera_id (str): Camera ID
            frame (numpy.ndarray): Frame to add

        Returns:
            bool: True if frame added successfully, False otherwise
        """
        if camera_id in self.detectors:
            try:
                # Add frame to queue, non-blocking
                queue_obj = self.detectors[camera_id]["queue"]
                queue_obj.put(frame.copy(), block=False)
                return True
            except queue.Full:
                # Queue full, skip frame
                pass
            except Exception as e:
                print(f"Error adding frame to detection {camera_id}: {e}")

        return False

    def _handle_event(self, event):
        """
        Handle a detection event

        Args:
            event (dict): Event data
        """
        try:
            # Save event image
            event_id = f"{event['camera_id']}_{int(time.time())}"
            image_path = os.path.join(self.events_dir, f"{event_id}.jpg")

            # Save the frame
            cv2.imwrite(image_path, event["frame"])

            # Add image path to event
            event["image_path"] = image_path

            # Remove frame from event to save memory
            del event["frame"]

            # Add to events list
            self.events.append(event)

            # Limit events list size
            if len(self.events) > self.max_events:
                # Remove oldest events
                events_to_remove = self.events[:len(self.events) - self.max_events]
                self.events = self.events[-self.max_events:]

                # Delete old image files
                for old_event in events_to_remove:
                    if "image_path" in old_event and os.path.exists(old_event["image_path"]):
                        try:
                            os.remove(old_event["image_path"])
                        except:
                            pass

            # Emit signal
            self.detection_event.emit(event)

            # Print event info
            event_type = event.get("type", "unknown")
            confidence = event.get("confidence", 0)
            print(f"Detection event: {event_type} on camera {event['camera_id']} "
                  f"(confidence: {confidence:.1f}%)")

        except Exception as e:
            print(f"Error handling detection event: {e}")

    def get_events(self, limit=None, event_type=None, camera_id=None):
        """
        Get detection events with optional filtering

        Args:
            limit (int, optional): Maximum number of events to return
            event_type (str, optional): Filter by event type ('motion', 'object', 'fire')
            camera_id (str, optional): Filter by camera ID

        Returns:
            list: List of events, newest first
        """
        # Filter events
        filtered_events = self.events

        if event_type:
            filtered_events = [e for e in filtered_events if e.get("type") == event_type]

        if camera_id:
            filtered_events = [e for e in filtered_events if e.get("camera_id") == camera_id]

        # Sort by timestamp, newest first
        filtered_events = sorted(filtered_events, key=lambda e: e.get("timestamp", datetime.datetime.min), reverse=True)

        # Apply limit
        if limit is not None:
            filtered_events = filtered_events[:limit]

        return filtered_events

    def get_active_detections(self):
        """
        Get a list of cameras with active detection

        Returns:
            dict: Dictionary of active detections
        """
        return {k: v["settings"] for k, v in self.detectors.items()}

    def is_detection_active(self, camera_id):
        """
        Check if detection is active for a camera

        Args:
            camera_id (str): Camera ID

        Returns:
            bool: True if detection is active, False otherwise
        """
        return camera_id in self.detectors

    def update_detection_settings(self, camera_id, motion_sensitivity=None, object_confidence=None,
                                  fire_detection=None):
        """
        Update detection settings for a camera

        Args:
            camera_id (str): Camera ID
            motion_sensitivity (float, optional): Motion detection sensitivity
            object_confidence (float, optional): Object detection confidence threshold
            fire_detection (bool, optional): Enable/disable fire detection

        Returns:
            bool: True if settings updated successfully, False otherwise
        """
        if camera_id not in self.detectors:
            return False

        try:
            detector = self.detectors[camera_id]
            thread = detector["thread"]
            settings = detector["settings"]

            # Update settings
            if motion_sensitivity is not None:
                settings["motion_sensitivity"] = motion_sensitivity
            if object_confidence is not None:
                settings["object_confidence"] = object_confidence
            if fire_detection is not None:
                settings["fire_detection"] = fire_detection
                thread.enable_fire_detection(fire_detection)

            # Update thread settings
            thread.update_sensitivity(
                settings.get("motion_sensitivity", 0.5),
                settings.get("object_confidence", 0.7)
            )

            return True

        except Exception as e:
            print(f"Error updating detection settings for camera {camera_id}: {e}")
            return False

    def stop_all_detections(self):
        """Stop all detections"""
        for camera_id in list(self.detectors.keys()):
            self.stop_detection(camera_id)

    def clear_events(self):
        """Clear all detection events"""
        # Delete image files
        for event in self.events:
            if "image_path" in event and os.path.exists(event["image_path"]):
                try:
                    os.remove(event["image_path"])
                except:
                    pass

        # Clear events list
        self.events.clear()

    def get_event_statistics(self):
        """
        Get statistics about detection events

        Returns:
            dict: Event statistics
        """
        try:
            total_events = len(self.events)
            motion_events = len([e for e in self.events if e.get("type") == "motion"])
            object_events = len([e for e in self.events if e.get("type") == "object"])
            fire_events = len([e for e in self.events if e.get("type") == "fire"])

            # Events by camera
            camera_stats = {}
            for event in self.events:
                camera_id = event.get("camera_id", "unknown")
                if camera_id not in camera_stats:
                    camera_stats[camera_id] = 0
                camera_stats[camera_id] += 1

            # Events by date
            today = datetime.date.today()
            today_events = len([e for e in self.events
                                if e.get("timestamp", datetime.datetime.min).date() == today])

            return {
                "total_events": total_events,
                "motion_events": motion_events,
                "object_events": object_events,
                "fire_events": fire_events,
                "today_events": today_events,
                "camera_stats": camera_stats
            }

        except Exception as e:
            print(f"Error getting event statistics: {e}")
            return {
                "total_events": 0,
                "motion_events": 0,
                "object_events": 0,
                "fire_events": 0,
                "today_events": 0,
                "camera_stats": {}
            }

    def enable_fire_detection(self, camera_id, enable=True):
        """
        Enable or disable fire detection for a specific camera

        Args:
            camera_id (str): Camera ID
            enable (bool): True to enable, False to disable

        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_detection_settings(camera_id, fire_detection=enable)

    def get_fire_events(self, limit=None, camera_id=None):
        """
        Get fire detection events

        Args:
            limit (int, optional): Maximum number of events to return
            camera_id (str, optional): Filter by camera ID

        Returns:
            list: List of fire events, newest first
        """
        return self.get_events(limit, "fire", camera_id)