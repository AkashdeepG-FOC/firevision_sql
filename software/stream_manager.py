import cv2
import requests
import threading
import time
import json
import base64
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
import socket

class StreamManager(QObject):
    stream_started = pyqtSignal(str)  # camera_id
    stream_stopped = pyqtSignal(str)  # camera_id
    stream_error = pyqtSignal(str, str)  # camera_id, error_message

    def __init__(self, server_url="http://localhost:5000"):
        super().__init__()
        self.server_url = server_url
        self.config_manager = None
        self.streams = {}  # {camera_id: {thread, active, quality, fps}}
        self.camera_info = {}  # {camera_id: {name, type}}
        
        # Test server connection - DISABLED
        print(f"📡 Stream Manager initialized (Local Mode)")
        # try:
        #     response = requests.get(f"{self.server_url}/api/status", timeout=5)
        #     if response.status_code == 200:
        #         print(f"✅ Connected to streaming server: {self.server_url}")
        #         print(f"Server response: {response.json()}")
        #     else:
        #         print(f"❌ Server returned status code: {response.status_code}")
        # except Exception as e:
        #     print(f"⚠️ Warning: Could not connect to streaming server: {e}")
        #     print(f"   Streaming will be disabled. Camera feeds will still work locally.")

    def set_config_manager(self, config_manager):
        """Set configuration manager"""
        self.config_manager = config_manager
        
    def register_camera(self, camera_id, camera_name, camera_type):
        """Register a camera with the streaming server"""
        try:
            # Store camera info locally
            self.camera_info[camera_id] = {
                "name": camera_name,
                "type": camera_type
            }
            
            # Register with server - DISABLED
            print(f"✅ Camera {camera_id} registered (Local Mode)")
            return True
                
        except Exception as e:
            print(f"⚠️ Warning: Could not register camera {camera_id}: {e}")
            return False

    def start_stream(self, camera_id, quality=75, fps=15):
        """Start streaming a camera to the server"""
        if camera_id in self.streams and self.streams[camera_id]["active"]:
            print(f"⚠️ Stream for camera {camera_id} already active")
            return True  # Already streaming
            
        try:
            print(f"🚀 Starting stream for camera {camera_id}")
            
            # Get settings from config if available
            stream_fps = fps
            stream_quality = quality
            server_url = self.server_url
            
            if self.config_manager:
                # Use network config
                net_conf = self.config_manager.get_config("network", {})
                if "backend_url" in net_conf and net_conf["backend_url"]:
                     server_url = net_conf["backend_url"]
                     
                # Use active streams config (if previously saved) or defaults
                # Actually, quality/fps might be stored in a generic 'stream' config too?
                # For now using defaults passed or potentially from app_settings
                stream_quality = self.config_manager.get_config("app_settings.stream_quality", quality)
                stream_fps = self.config_manager.get_config("app_settings.stream_fps", fps)

            # Create streaming thread (HTTP-based, not WebSocket)
            stream_thread = StreamThread(
                camera_id, 
                server_url,
                stream_quality,
                stream_fps
            )
            
            # Store stream info
            self.streams[camera_id] = {
                "thread": stream_thread,
                "active": True,
                "quality": quality,
                "fps": fps
            }
            
            # Start thread
            stream_thread.start()
            
            # Emit signal
            self.stream_started.emit(camera_id)
            
            print(f"✅ Stream started for camera {camera_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting stream for camera {camera_id}: {e}")
            self.stream_error.emit(camera_id, str(e))
            return False

    def stop_stream(self, camera_id):
        """Stop streaming a camera"""
        if camera_id not in self.streams:
            return False
            
        try:
            print(f"🛑 Stopping stream for camera {camera_id}")
            
            # Get stream info
            stream = self.streams[camera_id]
            thread = stream["thread"]
            
            # Stop thread
            thread.stop()
            
            # Update status
            stream["active"] = False
            
            # Emit signal
            self.stream_stopped.emit(camera_id)
            
            print(f"✅ Stream stopped for camera {camera_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping stream for camera {camera_id}: {e}")
            self.stream_error.emit(camera_id, str(e))
            return False

    def add_frame(self, camera_id, frame):
        """Add a frame to the streaming queue for a camera"""
        if camera_id in self.streams and self.streams[camera_id]["active"]:
            try:
                thread = self.streams[camera_id]["thread"]
                thread.add_frame(frame)
                return True
            except Exception as e:
                print(f"❌ Error adding frame to stream {camera_id}: {e}")
        return False

    def is_streaming(self, camera_id):
        """Check if a camera is currently streaming"""
        return camera_id in self.streams and self.streams[camera_id]["active"]

    def get_stream_url(self, camera_id):
        """Get the URL for viewing a camera stream"""
        return f"{self.server_url}/view/{camera_id}"

    def stop_all_streams(self):
        """Stop all streams"""
        for camera_id in list(self.streams.keys()):
            self.stop_stream(camera_id)


class StreamThread(threading.Thread):
    def __init__(self, camera_id, server_url, quality=75, fps=15):
        """Initialize a streaming thread - HTTP-based streaming"""
        super().__init__()
        self.camera_id = camera_id
        self.server_url = server_url
        self.quality = quality
        self.fps = fps
        self.running = False
        self.frame_queue = []
        self.frame_lock = threading.Lock()
        self.last_frame_time = 0
        self.frame_interval = 1.0 / fps
        self.frames_sent = 0
        self.last_stats_time = time.time()
        self.daemon = True

    def run(self):
        """Main streaming loop - uses HTTP POST instead of WebSocket"""
        self.running = True
        
        print(f"📡 Starting HTTP-based streaming for camera {self.camera_id}")
        
        # Process frames
        while self.running:
            try:
                # Get frame from queue
                frame = None
                with self.frame_lock:
                    if self.frame_queue:
                        frame = self.frame_queue.pop(0)
                
                if frame is None:
                    time.sleep(0.01)  # Small sleep if no frames
                    continue
                
                # Check if we should send this frame (fps limiting)
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_interval:
                    self.last_frame_time = current_time
                    
                    # Resize frame for better performance
                    frame_resized = cv2.resize(frame, (640, 480))
                    
                    # Encode frame as JPEG
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                    _, jpeg_data = cv2.imencode('.jpg', frame_resized, encode_param)
                    
                    # Convert to base64
                    base64_frame = base64.b64encode(jpeg_data).decode('utf-8')
                    
                    # Note: Streaming is disabled for now to avoid connection errors
                    # The camera feed will still work locally in the application
                    # Uncomment below to enable remote streaming when server is ready
                    
                    # try:
                    #     requests.post(
                    #         f"{self.server_url}/api/stream/frame",
                    #         json={
                    #             "camera_id": self.camera_id,
                    #             "frame": base64_frame,
                    #             "timestamp": current_time
                    #         },
                    #         timeout=1
                    #     )
                    # except:
                    #     pass  # Silently fail if server unavailable
                    
                    self.frames_sent += 1
                    
                    # Print stats every 100 frames
                    if self.frames_sent % 100 == 0:
                        elapsed = current_time - self.last_stats_time
                        fps = 100 / elapsed if elapsed > 0 else 0
                        print(f"📊 Camera {self.camera_id} Local FPS: {fps:.1f}, Total frames: {self.frames_sent}")
                        self.last_stats_time = current_time
                
            except Exception as e:
                print(f"❌ Error in streaming thread for {self.camera_id}: {e}")
                time.sleep(1)  # Avoid tight loop on error
                
        print(f"🔌 Streaming thread stopped for camera {self.camera_id}")

    def add_frame(self, frame):
        """Add a frame to the streaming queue"""
        try:
            with self.frame_lock:
                # Keep only last 2 frames to prevent lag
                if len(self.frame_queue) >= 2:
                    self.frame_queue.pop(0)
                self.frame_queue.append(frame.copy())
        except Exception as e:
            print(f"❌ Error adding frame to stream queue for {self.camera_id}: {e}")

    def stop(self):
        """Stop the streaming thread"""
        print(f"🛑 Stopping streaming thread for camera {self.camera_id}")
        self.running = False
        self.join(timeout=5.0)
