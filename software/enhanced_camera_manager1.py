import cv2
import threading
import time
import numpy as np
import urllib.parse
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from people_detector import PeopleDetector
from fire_smoke_detector import FireSmokeDetector

class EnhancedCameraManager(QObject):
    frame_ready = pyqtSignal(str, np.ndarray)  # camera_id, frame (original)
    detection_frame_ready = pyqtSignal(str, np.ndarray, list, int)  # camera_id, annotated_frame, detections, people_count
    fire_smoke_frame_ready = pyqtSignal(str, np.ndarray, list, dict)  # camera_id, annotated_frame, detections, alert_info
    camera_error = pyqtSignal(str, str)  # camera_id, error_message
    fire_smoke_alert = pyqtSignal(str, str, float)  # camera_id, alert_type, confidence

    def __init__(self):
        super().__init__()
        self.cameras = {}  # {camera_id: camera_info}
        self.capture_threads = {}  # {camera_id: thread}
        self.running_cameras = set()
        
        # Initialize detectors
        self.people_detector = PeopleDetector()
        self.people_detector.detection_result.connect(self.on_people_detection_result)
        
        self.fire_smoke_detector = FireSmokeDetector()
        self.fire_smoke_detector.detection_result.connect(self.on_fire_smoke_detection_result)
        self.fire_smoke_detector.fire_alert.connect(self.on_fire_smoke_alert)

    def add_camera(self, camera_id, name, source, camera_type):
        """Add a new camera"""
        try:
            print(f"🎥 Testing camera connection: {camera_id} - {name}")
            
            # Test camera connection first
            if camera_type == "webcam":
                cap = cv2.VideoCapture(int(source))
            else:
                # For RTSP streams, use optimized connection
                if source.startswith(('rtsp://', 'rtmp://')):
                    # Parse URL to handle credentials properly
                    parsed_url = urllib.parse.urlparse(source)
                    if '@' in parsed_url.netloc:
                        credentials, host = parsed_url.netloc.split('@')
                        username, password = credentials.split(':')
                        # URL encode the password to handle special characters
                        encoded_password = urllib.parse.quote(password)
                        modified_url = source.replace(f"{username}:{password}@", f"{username}:{encoded_password}@")
                        source = modified_url
                    
                    # Try with FFMPEG backend and TCP transport
                    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    if hasattr(cv2, 'CAP_PROP_RTSP_TRANSPORT'):
                        cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
                else:
                    cap = cv2.VideoCapture(source)
            
            if not cap.isOpened():
                error_msg = f"Failed to open camera source: {source}"
                print(f"❌ {error_msg}")
                self.camera_error.emit(camera_id, error_msg)
                return False
            
            # Test frame capture
            ret, frame = cap.read()
            if not ret:
                cap.release()
                error_msg = "Failed to capture test frame"
                print(f"❌ {error_msg}")
                self.camera_error.emit(camera_id, error_msg)
                return False
            
            print(f"✅ Test frame captured: {frame.shape}")
            cap.release()
            
            # Store camera info
            self.cameras[camera_id] = {
                'id': camera_id,
                'name': name,
                'source': source,
                'type': camera_type,
                'status': 'stopped'
            }
            
            print(f"✅ Camera {camera_id} added successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error adding camera: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False

    def start_camera(self, camera_id):
        """Start capturing from a camera"""
        if camera_id not in self.cameras:
            error_msg = "Camera not found"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False
        
        if camera_id in self.running_cameras:
            print(f"⚠️ Camera {camera_id} already running")
            return True  # Already running
        
        try:
            camera_info = self.cameras[camera_id]
            print(f"🚀 Starting camera capture: {camera_id}")
            
            # Create and start capture thread
            capture_thread = EnhancedCaptureThread(
                camera_id,
                camera_info['source'],
                camera_info['type'],
                self
            )
            
            # Store thread reference
            self.capture_threads[camera_id] = capture_thread
            
            # Start thread
            capture_thread.start()
            
            # Update status
            self.cameras[camera_id]['status'] = 'running'
            self.running_cameras.add(camera_id)
            
            print(f"✅ Camera {camera_id} started successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error starting camera: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False

    def stop_camera(self, camera_id):
        """Stop capturing from a camera"""
        if camera_id not in self.running_cameras:
            return True
        
        try:
            print(f"🛑 Stopping camera: {camera_id}")
            
            # Stop capture thread
            if camera_id in self.capture_threads:
                thread = self.capture_threads[camera_id]
                thread.stop()
                thread.wait(5000)  # Wait up to 5 seconds
                del self.capture_threads[camera_id]
            
            # Update status
            if camera_id in self.cameras:
                self.cameras[camera_id]['status'] = 'stopped'
            
            self.running_cameras.discard(camera_id)
            
            print(f"✅ Camera {camera_id} stopped")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping camera: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False

    def enable_people_detection(self, camera_id, enabled=True):
        """Enable/disable people detection for a camera"""
        self.people_detector.enable_detection(camera_id, enabled)

    def is_people_detection_enabled(self, camera_id):
        """Check if people detection is enabled for a camera"""
        return self.people_detector.is_detection_enabled(camera_id)

    def enable_fire_smoke_detection(self, camera_id, enabled=True):
        """Enable/disable fire/smoke detection for a camera"""
        self.fire_smoke_detector.enable_detection(camera_id, enabled)

    def is_fire_smoke_detection_enabled(self, camera_id):
        """Check if fire/smoke detection is enabled for a camera"""
        return self.fire_smoke_detector.is_detection_enabled(camera_id)

    def set_detection_confidence(self, threshold):
        """Set detection confidence threshold for both detectors"""
        self.people_detector.set_confidence_threshold(threshold)
        self.fire_smoke_detector.set_confidence_threshold(threshold)

    def set_fire_smoke_alert_sound(self, enabled):
        """Enable/disable fire/smoke alert sounds"""
        self.fire_smoke_detector.set_alert_sound_enabled(enabled)

    def remove_camera(self, camera_id):
        """Remove a camera"""
        try:
            # Stop camera first
            self.stop_camera(camera_id)
            
            # Remove from cameras dict
            if camera_id in self.cameras:
                del self.cameras[camera_id]
            
            print(f"✅ Camera {camera_id} removed")
            return True
            
        except Exception as e:
            error_msg = f"Error removing camera: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False

    def stop_all_cameras(self):
        """Stop all cameras"""
        print("🛑 Stopping all cameras")
        for camera_id in list(self.running_cameras):
            self.stop_camera(camera_id)

    def get_camera_info(self, camera_id):
        """Get camera information"""
        return self.cameras.get(camera_id)

    def get_all_cameras(self):
        """Get all cameras"""
        return list(self.cameras.values())

    def is_camera_running(self, camera_id):
        """Check if camera is running"""
        return camera_id in self.running_cameras

    def emit_frame(self, camera_id, frame):
        """Emit frame signal - called by capture thread"""
        # Emit original frame
        self.frame_ready.emit(camera_id, frame)
        
        # Process with people detection if enabled
        if self.people_detector.is_detection_enabled(camera_id):
            self.people_detector.detect_people(camera_id, frame)
        
        # Process with fire/smoke detection if enabled
        if self.fire_smoke_detector.is_detection_enabled(camera_id):
            self.fire_smoke_detector.detect_fire_smoke(camera_id, frame)

    def on_people_detection_result(self, camera_id, annotated_frame, detections, people_count):
        """Handle people detection results"""
        self.detection_frame_ready.emit(camera_id, annotated_frame, detections, people_count)

    def on_fire_smoke_detection_result(self, camera_id, annotated_frame, detections, alert_info):
        """Handle fire/smoke detection results"""
        self.fire_smoke_frame_ready.emit(camera_id, annotated_frame, detections, alert_info)

    def on_fire_smoke_alert(self, camera_id, alert_type, confidence):
        """Handle fire/smoke alert"""
        self.fire_smoke_alert.emit(camera_id, alert_type, confidence)

    def emit_error(self, camera_id, error):
        """Emit error signal - called by capture thread"""
        print(f"❌ Emitting error for camera {camera_id}: {error}")
        self.camera_error.emit(camera_id, error)


class EnhancedCaptureThread(QThread):
    def __init__(self, camera_id, source, camera_type, camera_manager):
        super().__init__()
        self.camera_id = camera_id
        self.source = source
        self.camera_type = camera_type
        self.camera_manager = camera_manager
        self.running = False
        self.cap = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # seconds

    def run(self):
        """Main capture loop"""
        self.running = True
        
        try:
            print(f"🎬 Starting capture thread for camera {self.camera_id}")
            
            # Open camera with optimized settings for RTSP
            self._open_camera_with_optimal_settings()
            
            if not self.cap.isOpened():
                error_msg = f"Failed to open camera: {self.source}"
                print(f"❌ {error_msg}")
                self.camera_manager.emit_error(self.camera_id, error_msg)
                return
            
            print(f"✅ Camera {self.camera_id} capture started")
            
            frame_count = 0
            last_fps_time = time.time()
            consecutive_failures = 0
            
            while self.running:
                # Try to grab frame first (faster than read)
                grabbed = self.cap.grab()
                
                if not grabbed:
                    consecutive_failures += 1
                    print(f"⚠️ Failed to grab frame from camera {self.camera_id} ({consecutive_failures})")
                    
                    if consecutive_failures >= 5:
                        print(f"🔄 Attempting to reconnect camera {self.camera_id}")
                        if not self._reconnect_camera():
                            # If reconnection fails, exit the thread
                            break
                        consecutive_failures = 0
                    
                    time.sleep(0.1)  # Short delay before retry
                    continue
                
                # Only retrieve the frame if grab was successful
                ret, frame = self.cap.retrieve()
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    print(f"⚠️ Failed to retrieve frame from camera {self.camera_id} ({consecutive_failures})")
                    time.sleep(0.1)
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # Emit frame signal to main thread
                self.camera_manager.emit_frame(self.camera_id, frame.copy())
                
                # Debug: Print FPS every 30 frames
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    fps = 30 / (current_time - last_fps_time)
                    print(f"📊 Camera {self.camera_id} capture FPS: {fps:.1f}")
                    last_fps_time = current_time
                
        except Exception as e:
            error_msg = f"Capture error: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_manager.emit_error(self.camera_id, error_msg)
        
        finally:
            if self.cap:
                self.cap.release()
            print(f"🔚 Camera {self.camera_id} capture stopped")

    def _open_camera_with_optimal_settings(self):
        """Open camera with optimized settings for RTSP"""
        try:
            if self.camera_type == "webcam":
                self.cap = cv2.VideoCapture(int(self.source))
            else:
                # For RTSP streams, use optimized settings
                if self.source.startswith(('rtsp://', 'rtmp://')):
                    # Try different connection methods
                    
                    # Method 1: Use FFMPEG backend with TCP transport (most reliable)
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                    
                    # Set important RTSP options
                    if hasattr(cv2, 'CAP_PROP_RTSP_TRANSPORT'):
                        self.cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
                    
                    # Reduce buffer size for lower latency
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Check if connection was successful
                    if not self.cap.isOpened():
                        print(f"⚠️ Failed with FFMPEG+TCP, trying GStreamer...")
                        
                        # Method 2: Try with GStreamer if available
                        if cv2.getBuildInformation().find("GStreamer") != -1:
                            # Parse URL to get credentials
                            parsed_url = urllib.parse.urlparse(self.source)
                            credentials = None
                            if '@' in parsed_url.netloc:
                                credentials, host = parsed_url.netloc.split('@')
                                username, password = credentials.split(':')
                                
                                # Create GStreamer pipeline with authentication
                                pipeline = (
                                    f'rtspsrc location="{self.source}" latency=0 user-id="{username}" '
                                    f'user-pw="{password}" ! rtph264depay ! h264parse ! avdec_h264 ! '
                                    f'videoconvert ! appsink max-buffers=1 drop=true'
                                )
                                
                                self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                else:
                    # For other IP cameras (HTTP streams, etc.)
                    self.cap = cv2.VideoCapture(self.source)
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Check if camera opened successfully
            if not self.cap.isOpened():
                raise Exception(f"Failed to open camera source: {self.source}")
                
            print(f"✅ Camera opened successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error opening camera: {str(e)}")
            return False
            
    def _reconnect_camera(self):
        """Attempt to reconnect to the camera"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            error_msg = f"Failed to reconnect after {self.max_reconnect_attempts} attempts"
            self.camera_manager.emit_error(self.camera_id, error_msg)
            return False
            
        self.reconnect_attempts += 1
        print(f"🔄 Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        # Release current capture if it exists
        if self.cap:
            self.cap.release()
            self.cap = None
            
        # Wait before reconnecting
        time.sleep(self.reconnect_delay)
        
        # Try to reopen
        success = self._open_camera_with_optimal_settings()
        
        if success:
            print(f"✅ Successfully reconnected to camera {self.camera_id}")
            self.reconnect_attempts = 0
            return True
        else:
            print(f"❌ Failed to reconnect to camera {self.camera_id}")
            return False

    def stop(self):
        """Stop the capture thread"""
        print(f"🛑 Stopping capture thread for camera {self.camera_id}")
        self.running = False
