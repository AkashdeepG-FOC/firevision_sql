import cv2
import threading
import time
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

class CameraManager(QObject):
    frame_ready = pyqtSignal(str, np.ndarray)  # camera_id, frame
    camera_error = pyqtSignal(str, str)  # camera_id, error_message

    def __init__(self):
        super().__init__()
        self.cameras = {}  # {camera_id: camera_info}
        self.capture_threads = {}  # {camera_id: thread}
        self.running_cameras = set()

    def add_camera(self, camera_id, name, source, camera_type):
        """Add a new camera"""
        try:
            print(f"🎥 Testing camera connection: {camera_id} - {name}")
            
            # Test camera connection first
            if camera_type == "webcam":
                cap = cv2.VideoCapture(int(source))
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
            capture_thread = CaptureThread(
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
        print(f"📸 Emitting frame for camera {camera_id}, shape: {frame.shape}")
        self.frame_ready.emit(camera_id, frame)

    def emit_error(self, camera_id, error):
        """Emit error signal - called by capture thread"""
        print(f"❌ Emitting error for camera {camera_id}: {error}")
        self.camera_error.emit(camera_id, error)


class CaptureThread(QThread):
    def __init__(self, camera_id, source, camera_type, camera_manager):
        super().__init__()
        self.camera_id = camera_id
        self.source = source
        self.camera_type = camera_type
        self.camera_manager = camera_manager
        self.running = False
        self.cap = None

    def run(self):
        """Main capture loop"""
        self.running = True
        
        try:
            print(f"🎬 Starting capture thread for camera {self.camera_id}")
            
            # Open camera
            if self.camera_type == "webcam":
                self.cap = cv2.VideoCapture(int(self.source))
            else:
                self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                error_msg = f"Failed to open camera: {self.source}"
                print(f"❌ {error_msg}")
                self.camera_manager.emit_error(self.camera_id, error_msg)
                return
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"✅ Camera {self.camera_id} capture started")
            
            frame_count = 0
            last_fps_time = time.time()
            
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    if self.camera_type in ["video_file", "Video File"]:
                        print(f"🔄 Looping video for camera {self.camera_id}")
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                        
                    print(f"⚠️ Failed to read frame from camera {self.camera_id}")
                    time.sleep(0.1)
                    continue
                
                # Emit frame signal to main thread
                self.camera_manager.emit_frame(self.camera_id, frame.copy())
                
                # FPS limiting (15 FPS to match stream)
                time.sleep(1/15)
                
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

    def stop(self):
        """Stop the capture thread"""
        print(f"🛑 Stopping capture thread for camera {self.camera_id}")
        self.running = False
