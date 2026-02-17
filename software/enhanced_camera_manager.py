import cv2
import threading
import time
import numpy as np
import urllib.parse
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from people_detector import PeopleDetector
from fire_smoke_detector import FireSmokeDetector
from workers.base_worker import BaseWorker, WorkerStatus

class EnhancedCameraManager(QObject):
    frame_ready = pyqtSignal(str, np.ndarray)  # camera_id, frame (original)
    detection_frame_ready = pyqtSignal(str, np.ndarray, list, int)  # camera_id, annotated_frame, detections, people_count
    fire_smoke_frame_ready = pyqtSignal(str, np.ndarray, list, dict)  # camera_id, annotated_frame, detections, alert_info
    camera_error = pyqtSignal(str, str)  # camera_id, error_message
    fire_smoke_alert = pyqtSignal(str, str, float)  # camera_id, alert_type, confidence
    camera_status_changed = pyqtSignal(str, str)  # camera_id, status
    bandwidth_update = pyqtSignal(str, float)  # camera_id, bandwidth_mbps
    recording_status_changed = pyqtSignal(str, bool)  # camera_id, is_recording
    camera_tested = pyqtSignal(str, bool, str)  # camera_id, success, message
    camera_testing_started = pyqtSignal(str)  # camera_id

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.cameras = {}  # {camera_id: camera_info}
        self.capture_threads = {}  # {camera_id: thread}
        self.running_cameras = set()
        self.camera_settings = {}  # {camera_id: settings}
        self.recording_schedules = {}  # {camera_id: schedule}
        self.bandwidth_monitor = {}  # {camera_id: bandwidth_data}
        self.night_mode_settings = {}  # {camera_id: night_mode_config}
        self.test_threads = {}  # {camera_id: test_thread} - for background camera testing
        
        # Initialize detectors
        self.people_detector = PeopleDetector()
        self.people_detector.detection_result.connect(self.on_people_detection_result)
        
        self.fire_smoke_detector = FireSmokeDetector(config_manager=self.config_manager)
        self.fire_smoke_detector.detection_result.connect(self.on_fire_smoke_detection_result)
        self.fire_smoke_detector.fire_alert.connect(self.on_fire_smoke_alert)
        
        # Load settings
        self.load_camera_settings()
        self.load_recording_schedules()
        self.load_cameras()
        
        # Start monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_cameras)
        self.monitor_timer.start(5000)  # Monitor every 5 seconds

    def add_camera(self, camera_id, name, source, camera_type, settings=None, skip_test=False):
        """Add a new camera with enhanced settings
        
        Args:
            camera_id: Unique identifier for the camera
            name: Display name for the camera
            source: Camera source (URL or device index)
            camera_type: Type of camera ("webcam" or "ip")
            settings: Optional camera settings dict
            skip_test: If True, skip synchronous connection testing (for faster loading)
        """
        try:
            if not skip_test:
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
                            credentials, host = parsed_url.netloc.split('@', 1)
                            if ':' in credentials:
                                username, password = credentials.split(':', 1)
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
            else:
                print(f"⏩ Skipping camera test for {camera_id} - {name} (will test in background)")
            
            # Store camera info
            self.cameras[camera_id] = {
                'id': camera_id,
                'name': name,
                'source': source,
                'type': camera_type,
                'status': 'testing' if skip_test else 'stopped',
                'last_seen': time.time(),
                'frame_count': 0,
                'error_count': 0,
                'uptime': 0,
                'start_time': None
            }
            
            # Initialize camera settings
            default_settings = {
                'resolution': '1920x1080',
                'fps': 30,
                'brightness': 50,
                'contrast': 50,
                'saturation': 50,
                'exposure': 'auto',
                'white_balance': 'auto',
                'night_mode': False,
                'motion_detection': True,
                'audio_enabled': False,
                'recording_quality': 'high',
                'retention_days': 30,
                'alert_zones': [],
                'privacy_masks': []
            }
            
            if settings:
                default_settings.update(settings)
            
            self.camera_settings[camera_id] = default_settings
            
            # Initialize recording schedule
            self.recording_schedules[camera_id] = {
                'enabled': False,
                'schedule_type': 'always',  # 'always', 'scheduled', 'motion_only'
                'time_ranges': [],  # List of (start_time, end_time) tuples
                'days_of_week': [0, 1, 2, 3, 4, 5, 6],  # Monday=0, Sunday=6
                'motion_sensitivity': 50,
                'pre_record_seconds': 5,
                'post_record_seconds': 10
            }
            
            # Initialize bandwidth monitoring
            self.bandwidth_monitor[camera_id] = {
                'bytes_received': 0,
                'last_update': time.time(),
                'bandwidth_history': [],
                'avg_bandwidth': 0
            }
            
            self.save_camera_settings()
            self.save_cameras()
            
            print(f"✅ Camera {camera_id} added successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error adding camera: {str(e)}"
            print(f"❌ {error_msg}")
            self.camera_error.emit(camera_id, error_msg)
            return False

    def update_camera_settings(self, camera_id, settings):
        """Update camera settings"""
        if camera_id in self.camera_settings:
            self.camera_settings[camera_id].update(settings)
            self.save_camera_settings()
            
            # Apply settings to running camera
            if camera_id in self.running_cameras:
                self.apply_camera_settings(camera_id)
            
            return True
        return False

    def apply_camera_settings(self, camera_id):
        """Apply settings to a running camera"""
        if camera_id not in self.capture_threads:
            return
            
        thread = self.capture_threads[camera_id]
        settings = self.camera_settings.get(camera_id, {})
        
        try:
            if hasattr(thread, 'cap') and thread.cap:
                cap = thread.cap
                
                # Apply resolution
                resolution = settings.get('resolution', '1920x1080')
                width, height = map(int, resolution.split('x'))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Apply FPS
                fps = settings.get('fps', 30)
                cap.set(cv2.CAP_PROP_FPS, fps)
                
                # Apply brightness, contrast, saturation
                if settings.get('brightness') is not None:
                    cap.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'] / 100.0)
                if settings.get('contrast') is not None:
                    cap.set(cv2.CAP_PROP_CONTRAST, settings['contrast'] / 100.0)
                if settings.get('saturation') is not None:
                    cap.set(cv2.CAP_PROP_SATURATION, settings['saturation'] / 100.0)
                
                print(f"✅ Applied settings to camera {camera_id}")
                
        except Exception as e:
            print(f"❌ Error applying settings to camera {camera_id}: {e}")

    def reboot_camera(self, camera_id):
        """Reboot/restart a camera"""
        try:
            if camera_id in self.running_cameras:
                print(f"🔄 Rebooting camera {camera_id}")
                
                # Stop camera
                self.stop_camera(camera_id)
                
                # Wait a moment
                time.sleep(2)
                
                # Start camera again
                success = self.start_camera(camera_id)
                
                if success:
                    print(f"✅ Camera {camera_id} rebooted successfully")
                    self.camera_status_changed.emit(camera_id, "rebooted")
                else:
                    print(f"❌ Failed to reboot camera {camera_id}")
                    self.camera_status_changed.emit(camera_id, "reboot_failed")
                
                return success
            else:
                print(f"⚠️ Camera {camera_id} is not running")
                return False
                
        except Exception as e:
            print(f"❌ Error rebooting camera {camera_id}: {e}")
            return False

    def get_camera_status(self, camera_id):
        """Get detailed camera status"""
        if camera_id not in self.cameras:
            return None
            
        camera = self.cameras[camera_id]
        settings = self.camera_settings.get(camera_id, {})
        bandwidth = self.bandwidth_monitor.get(camera_id, {})
        
        status = {
            'id': camera_id,
            'name': camera['name'],
            'type': camera['type'],
            'source': camera['source'],
            'status': camera['status'],
            'last_seen': camera.get('last_seen', 0),
            'frame_count': camera.get('frame_count', 0),
            'error_count': camera.get('error_count', 0),
            'uptime': camera.get('uptime', 0),
            'resolution': settings.get('resolution', 'Unknown'),
            'fps': settings.get('fps', 0),
            'bandwidth_mbps': bandwidth.get('avg_bandwidth', 0),
            'recording': camera_id in self.running_cameras,
            'night_mode': settings.get('night_mode', False),
            'motion_detection': settings.get('motion_detection', False),
            'people_detection': self.is_people_detection_enabled(camera_id),
            'fire_detection': self.is_fire_smoke_detection_enabled(camera_id)
        }
        
        return status

    def get_all_camera_status(self):
        """Get status for all cameras"""
        return [self.get_camera_status(camera_id) for camera_id in self.cameras.keys()]

    def monitor_cameras(self):
        """Monitor camera health and performance"""
        if not hasattr(self, 'cameras') or not isinstance(self.cameras, dict):
            print("Error: self.cameras is not a dict!")
            return
        current_time = time.time()
        
        for camera_id in list(self.cameras.keys()):
            camera = self.cameras[camera_id]
            
            # Update uptime for running cameras
            if camera_id in self.running_cameras and camera.get('start_time'):
                camera['uptime'] = current_time - camera['start_time']
            
            # Check for stale cameras (no frames in last 30 seconds)
            if camera_id in self.running_cameras:
                last_seen = camera.get('last_seen', 0)
                if current_time - last_seen > 30:
                    print(f"⚠️ Camera {camera_id} appears stale, attempting restart")
                    self.reboot_camera(camera_id)
            
            # Update bandwidth monitoring
            self.update_bandwidth_monitoring(camera_id)
            
            # Check recording schedule
            self.check_recording_schedule(camera_id)

    def update_bandwidth_monitoring(self, camera_id):
        """Update bandwidth monitoring for a camera"""
        if camera_id not in self.bandwidth_monitor:
            return
            
        monitor = self.bandwidth_monitor[camera_id]
        current_time = time.time()
        
        # Calculate bandwidth (simplified - in real implementation, track actual bytes)
        if camera_id in self.running_cameras:
            # Estimate bandwidth based on resolution and FPS
            settings = self.camera_settings.get(camera_id, {})
            resolution = settings.get('resolution', '1920x1080')
            fps = settings.get('fps', 30)
            
            # Rough calculation: width * height * 3 (RGB) * fps * compression_ratio
            width, height = map(int, resolution.split('x'))
            estimated_bps = width * height * 3 * fps * 0.1  # Assume 10% compression
            estimated_mbps = estimated_bps / (1024 * 1024)
            
            monitor['avg_bandwidth'] = estimated_mbps
            monitor['bandwidth_history'].append({
                'timestamp': current_time,
                'bandwidth': estimated_mbps
            })
            
            # Keep only last hour of data
            cutoff_time = current_time - 3600
            monitor['bandwidth_history'] = [
                entry for entry in monitor['bandwidth_history']
                if entry['timestamp'] > cutoff_time
            ]
            
            self.bandwidth_update.emit(camera_id, estimated_mbps)

    def check_recording_schedule(self, camera_id):
        """Check if camera should be recording based on schedule"""
        if camera_id not in self.recording_schedules:
            return
            
        schedule = self.recording_schedules[camera_id]
        
        if not schedule['enabled']:
            return
            
        current_time = datetime.now()
        current_day = current_time.weekday()  # Monday=0, Sunday=6
        current_time_str = current_time.strftime('%H:%M')
        
        should_record = False
        
        if schedule['schedule_type'] == 'always':
            should_record = True
        elif schedule['schedule_type'] == 'scheduled':
            # Check if current day is in schedule
            if current_day in schedule['days_of_week']:
                # Check if current time is in any time range
                for start_time, end_time in schedule['time_ranges']:
                    if start_time <= current_time_str <= end_time:
                        should_record = True
                        break
        elif schedule['schedule_type'] == 'motion_only':
            # This would be handled by motion detection logic
            should_record = False  # Placeholder
        
        # Update recording status
        is_currently_recording = camera_id in self.running_cameras
        
        if should_record and not is_currently_recording:
            self.start_camera(camera_id)
        elif not should_record and is_currently_recording:
            self.stop_camera(camera_id)

    def set_recording_schedule(self, camera_id, schedule):
        """Set recording schedule for a camera"""
        if camera_id in self.cameras:
            self.recording_schedules[camera_id] = schedule
            self.save_recording_schedules()
            return True
        return False

    def get_recording_schedule(self, camera_id):
        """Get recording schedule for a camera"""
        return self.recording_schedules.get(camera_id, {})

    def save_camera_settings(self):
        """Save camera settings to file"""
        try:
            settings_file = "config/camera_settings.json"
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(self.camera_settings, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving camera settings: {e}")

    def load_camera_settings(self):
        """Load camera settings from file"""
        try:
            settings_file = "config/camera_settings.json"
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    self.camera_settings = json.load(f)
                    
        except Exception as e:
            print(f"❌ Error loading camera settings: {e}")

    def save_recording_schedules(self):
        """Save recording schedules to file"""
        try:
            schedules_file = "config/recording_schedules.json"
            os.makedirs(os.path.dirname(schedules_file), exist_ok=True)
            
            with open(schedules_file, 'w') as f:
                json.dump(self.recording_schedules, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving recording schedules: {e}")

    def load_recording_schedules(self):
        """Load recording schedules from file"""
        try:
            schedules_file = "config/recording_schedules.json"
            
            if os.path.exists(schedules_file):
                with open(schedules_file, 'r') as f:
                    self.recording_schedules = json.load(f)
                    
        except Exception as e:
            print(f"❌ Error loading recording schedules: {e}")

    def save_cameras(self):
        """Save cameras list to file"""
        try:
            cameras_file = "config/cameras.json"
            os.makedirs(os.path.dirname(cameras_file), exist_ok=True)
            
            # Convert cameras dict to list for saving
            cameras_data = []
            for camera_id, camera in self.cameras.items():
                cameras_data.append({
                    'id': camera['id'],
                    'name': camera['name'],
                    'source': camera['source'],
                    'type': camera['type']
                })
            
            with open(cameras_file, 'w') as f:
                json.dump(cameras_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving cameras: {e}")

    def load_cameras(self):
        """Load cameras from file"""
        try:
            cameras_file = "config/cameras.json"
            
            if os.path.exists(cameras_file):
                with open(cameras_file, 'r') as f:
                    cameras_data = json.load(f)
                
                for camera_data in cameras_data:
                    # We don't verify connection on load to speed up startup
                    # Instead just populate the dict
                    camera_id = camera_data['id']
                    self.cameras[camera_id] = {
                        'id': camera_id,
                        'name': camera_data['name'],
                        'source': camera_data['source'],
                        'type': camera_data['type'],
                        'status': 'stopped',
                        'last_seen': 0,
                        'frame_count': 0,
                        'error_count': 0,
                        'uptime': 0,
                        'start_time': None
                    }
                    
                    # Initialize bandwidth monitor for loaded camera
                    self.bandwidth_monitor[camera_id] = {
                        'bytes_received': 0,
                        'last_update': time.time(),
                        'bandwidth_history': [],
                        'avg_bandwidth': 0
                    }
                    
        except Exception as e:
            print(f"❌ Error loading cameras: {e}")

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
            self.cameras[camera_id]['start_time'] = time.time()
            self.cameras[camera_id]['error_count'] = 0
            self.running_cameras.add(camera_id)
            
            # Apply camera settings
            self.apply_camera_settings(camera_id)
            
            self.camera_status_changed.emit(camera_id, 'running')
            self.recording_status_changed.emit(camera_id, True)
            
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
                thread.wait(1000)  # Wait only 1 second (reduced from 5)
                if thread.isRunning():
                    print(f"⚠️ Camera thread {camera_id} still running, continuing anyway...")
                del self.capture_threads[camera_id]
            
            # Stop detection threads
            if hasattr(self, 'people_detector') and camera_id in self.people_detector.detection_threads:
                det_thread = self.people_detector.detection_threads[camera_id]
                det_thread.stop()
                det_thread.wait(500)  # Short wait
                
            if hasattr(self, 'fire_smoke_detector') and camera_id in self.fire_smoke_detector.detection_threads:
                fire_thread = self.fire_smoke_detector.detection_threads[camera_id]
                fire_thread.stop()
                fire_thread.wait(500)  # Short wait
            
            # Update status
            if camera_id in self.cameras:
                self.cameras[camera_id]['status'] = 'stopped'
                self.cameras[camera_id]['start_time'] = None
            
            self.running_cameras.discard(camera_id)
            
            self.camera_status_changed.emit(camera_id, 'stopped')
            self.recording_status_changed.emit(camera_id, False)
            
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
            
            # Remove settings
            if camera_id in self.camera_settings:
                del self.camera_settings[camera_id]
            
            # Remove schedule
            if camera_id in self.recording_schedules:
                del self.recording_schedules[camera_id]
            
            # Remove bandwidth monitoring
            if camera_id in self.bandwidth_monitor:
                del self.bandwidth_monitor[camera_id]
            
            self.save_camera_settings()
            self.save_recording_schedules()
            self.save_cameras()
            
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
        # Update camera stats
        if camera_id in self.cameras:
            self.cameras[camera_id]['last_seen'] = time.time()
            self.cameras[camera_id]['frame_count'] = self.cameras[camera_id].get('frame_count', 0) + 1
        
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

    def test_camera_async(self, camera_id):
        """Test camera connection asynchronously in background
        
        Args:
            camera_id: ID of the camera to test
        """
        if camera_id not in self.cameras:
            print(f"⚠️ Camera {camera_id} not found for testing")
            return
        
        camera_info = self.cameras[camera_id]
        
        # Emit testing started signal
        self.camera_testing_started.emit(camera_id)
        
        # Create test thread
        test_thread = CameraTestThread(
            camera_id,
            camera_info['source'],
            camera_info['type']
        )
        
        # Connect signals
        test_thread.test_complete.connect(self._on_camera_test_complete)
        
        # Store thread reference
        self.test_threads[camera_id] = test_thread
        
        # Start testing
        test_thread.start()
        
        print(f"🧪 Started background testing for camera {camera_id}")
    
    def _on_camera_test_complete(self, camera_id, success, message):
        """Handle camera test completion
        
        Args:
            camera_id: ID of the tested camera
            success: Whether the test was successful
            message: Test result message
        """
        print(f"{'✅' if success else '❌'} Camera test complete for {camera_id}: {message}")
        
        # Update camera status
        if camera_id in self.cameras:
            self.cameras[camera_id]['status'] = 'stopped' if success else 'error'
        
        # Clean up test thread
        if camera_id in self.test_threads:
            del self.test_threads[camera_id]
        
        # Emit test result signal
        self.camera_tested.emit(camera_id, success, message)

    def emit_error(self, camera_id, error):
        """Emit error signal - called by capture thread"""
        # Update error count
        if camera_id in self.cameras:
            self.cameras[camera_id]['error_count'] = self.cameras[camera_id].get('error_count', 0) + 1
        
        print(f"❌ Emitting error for camera {camera_id}: {error}")
        self.camera_error.emit(camera_id, error)


class EnhancedCaptureThread(BaseWorker):
    def __init__(self, camera_id, source, camera_type, camera_manager):
        super().__init__(f"Camera_{camera_id}")
        self.camera_id = camera_id
        self.source = source
        self.camera_type = camera_type
        self.camera_manager = camera_manager
        self.cap = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # seconds
        self.last_frame_time = None  # For watchdog

    def work(self):
        """Main capture loop - called by BaseWorker.run()"""
        print(f"🎬 Starting capture for camera {self.camera_id}")
        
        # Open camera with optimized settings for RTSP
        self._open_camera_with_optimal_settings()
        consecutive_failures = 0
        frame_count = 0
        last_fps_time = time.time()
        
        while self.is_running():
            # Try to grab frame first (faster than read)
            grabbed = self.cap.grab()
            
            if not grabbed:
                consecutive_failures += 1
                print(f"⚠️ Failed to grab frame from camera {self.camera_id} ({consecutive_failures})")
                
                if consecutive_failures >= 5:
                    print(f"🔄 Attempting to reconnect camera {self.camera_id}")
                    if not self._reconnect_camera():
                        # If reconnection fails, raise exception to trigger restart
                        raise Exception(f"Failed to reconnect after {self.max_reconnect_attempts} attempts")
                    consecutive_failures = 0
                
                time.sleep(0.1)  # Short delay before retry
                continue
            
            # Only retrieve the frame if grab was successful
            ret, frame = self.cap.retrieve()
            
            if not ret or frame is None:
                # Handle video file looping
                if self.camera_type in ["video_file", "Video File"]:
                    print(f"🔄 Looping video for camera {self.camera_id}")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(1/30) # Prevent tight loop if rewind fails
                    continue

                consecutive_failures += 1
                print(f"⚠️ Failed to retrieve frame from camera {self.camera_id} ({consecutive_failures})")
                time.sleep(0.1)
                continue
            
            # Reset failure counter on success
            consecutive_failures = 0
            
            # Update last frame timestamp for watchdog
            self.last_frame_time = time.time()
            
            # Emit frame signal to main thread
            self.camera_manager.emit_frame(self.camera_id, frame.copy())
            
            # Debug: Print FPS every 30 frames
            frame_count += 1
            if frame_count % 30 == 0:
                current_time = time.time()
                fps = 30 / (current_time - last_fps_time)
                print(f"📊 Camera {self.camera_id} capture FPS: {fps:.1f}")
                last_fps_time = current_time

            # FPS Limiting for video files to ensure smooth playback and reduce CPU usage
            if self.camera_type in ["video_file", "Video File"]:
                time.sleep(1/30) # Enforce approx 30 FPS for files
        
        # Cleanup
        if self.cap:
            self.cap.release()
        print(f"🔚 Camera {self.camera_id} capture stopped")
    
    def stop_work(self):
        """Override to handle cleanup"""
        if self.cap:
            self.cap.release()
            self.cap = None

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
                                credentials, host = parsed_url.netloc.split('@', 1)
                                username, password = credentials.split(':', 1)
                                
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

class CameraTestThread(BaseWorker):
    """Thread for testing camera connections in the background"""
    test_complete = pyqtSignal(str, bool, str)  # camera_id, success, message
    
    def __init__(self, camera_id, source, camera_type):
        super().__init__(f"CameraTest_{camera_id}")
        self.camera_id = camera_id
        self.source = source
        self.camera_type = camera_type
    
    def work(self):
        """Test camera connection - called by BaseWorker.run()"""
        print(f"🧪 Testing camera connection in background: {self.camera_id}")
        
        # Test camera connection
        if self.camera_type == "webcam":
            cap = cv2.VideoCapture(int(self.source))
        else:
            # For RTSP streams, use optimized connection
            if self.source.startswith(('rtsp://', 'rtmp://')):
                # Parse URL to handle credentials properly
                parsed_url = urllib.parse.urlparse(self.source)
                source = self.source
                if '@' in parsed_url.netloc:
                    credentials, host = parsed_url.netloc.split('@', 1)
                    if ':' in credentials:
                        username, password = credentials.split(':', 1)
                        # URL encode the password to handle special characters
                        encoded_password = urllib.parse.quote(password)
                        modified_url = self.source.replace(f"{username}:{password}@", f"{username}:{encoded_password}@")
                        source = modified_url
                # Try with FFMPEG backend and TCP transport
                cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                if hasattr(cv2, 'CAP_PROP_RTSP_TRANSPORT'):
                    cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)
            else:
                cap = cv2.VideoCapture(self.source)
        
        # Set timeout for connection attempt
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second timeout
        
        if not cap.isOpened():
            error_msg = f"Failed to open camera source: {self.source}"
            print(f"❌ {error_msg}")
            cap.release()
            self.test_complete.emit(self.camera_id, False, error_msg)
            raise Exception(error_msg)  # Trigger error handling
        
        # Test frame capture
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            error_msg = "Failed to capture test frame"
            print(f"❌ {error_msg}")
            self.test_complete.emit(self.camera_id, False, error_msg)
            raise Exception(error_msg)  # Trigger error handling
        
        print(f"✅ Test frame captured: {frame.shape}")
        cap.release()
        
        # Emit success
        success_msg = f"Camera connected successfully ({frame.shape[1]}x{frame.shape[0]})"
        self.test_complete.emit(self.camera_id, True, success_msg)
