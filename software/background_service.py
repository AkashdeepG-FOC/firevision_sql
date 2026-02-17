import threading
import time
import signal
import sys
import os
from typing import Dict, List
from config_manager import ConfigManager
from stream_manager import StreamManager
from enhanced_camera_manager import EnhancedCameraManager

class BackgroundService:
    """Background service to keep cameras and streaming running even when GUI is closed"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager if config_manager else ConfigManager()
        self.camera_manager = EnhancedCameraManager(config_manager=self.config_manager)
        self.stream_manager = StreamManager()
        if hasattr(self.stream_manager, 'set_config_manager'):
             self.stream_manager.set_config_manager(self.config_manager)
        self.current_user: str = ""
        self.running = False
        self.service_thread = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🔧 Background service initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down background service...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the background service"""
        if self.running:
            print("⚠️ Background service already running")
            return
        
        print("🚀 Starting background service...")
        self.running = True
        
        # Start service in a separate thread
        self.service_thread = threading.Thread(target=self._service_loop, daemon=True)
        self.service_thread.start()
        
        print("✅ Background service started successfully")
        # If a user is already set, auto start their resources
        if self.current_user:
            self.auto_start_cameras()
            if self.config_manager.should_auto_start_streams():
                self.auto_start_streams()
    
    def stop(self):
        """Stop the background service"""
        if not self.running:
            return
        
        print("🛑 Stopping background service...")
        self.running = False
        
        # Stop all cameras and streams
        self.camera_manager.stop_all_cameras()
        self.stream_manager.stop_all_streams()
        
        # Clear active streams
        self.config_manager.save_active_streams({})
        
        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5)
        
        print("✅ Background service stopped")
    
    def _service_loop(self):
        """Main service loop"""
        print("🔄 Background service loop started")
        
        while self.running:
            try:
                # Monitor cameras and streams
                self._monitor_cameras()
                self._monitor_streams()
                
                # Health check every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Error in service loop: {e}")
                time.sleep(10)  # Wait before retrying
        
        print("🔚 Background service loop ended")
    
    def _monitor_cameras(self):
        """Monitor camera status and restart if needed"""
        try:
            cameras = self.config_manager.load_cameras()
            
            for camera_id, camera_data in cameras.items():
                if camera_data.get("auto_start", True):
                    if not self.camera_manager.is_camera_running(camera_id):
                        print(f"🔄 Restarting camera {camera_id}")
                        self._start_camera(camera_id, camera_data)
                        
        except Exception as e:
            print(f"❌ Error monitoring cameras: {e}")
    
    def _monitor_streams(self):
        """Monitor stream status and restart if needed"""
        try:
            active_streams = self.config_manager.get_active_streams()
            
            for camera_id, stream_info in active_streams.items():
                if not self.stream_manager.is_streaming(camera_id):
                    print(f"🔄 Restarting stream for camera {camera_id}")
                    self.stream_manager.start_stream(camera_id)
                        
        except Exception as e:
            print(f"❌ Error monitoring streams: {e}")
    
    def auto_start_cameras(self):
        """Auto-start cameras that are configured to start automatically"""
        print("🎥 Auto-starting cameras...")
        
        cameras = self.config_manager.get_auto_start_cameras()
        
        for camera_data in cameras:
            camera_id = camera_data["id"]
            print(f"🚀 Starting camera {camera_id}: {camera_data['name']}")
            
            success = self._start_camera(camera_id, camera_data)
            if success:
                print(f"✅ Camera {camera_id} started successfully")
            else:
                print(f"❌ Failed to start camera {camera_id}")
    
    def auto_start_streams(self):
        """Auto-start streams for active cameras"""
        print("📡 Auto-starting streams...")
        
        cameras = self.config_manager.load_cameras()
        
        for camera_id, camera_data in cameras.items():
            if camera_data.get("stream_enabled", True) and self.camera_manager.is_camera_running(camera_id):
                print(f"🚀 Starting stream for camera {camera_id}")
                
                # Register camera with stream manager
                self.stream_manager.register_camera(
                    camera_id,
                    camera_data["name"],
                    camera_data["type"]
                )
                
                # Start stream
                success = self.stream_manager.start_stream(camera_id)
                if success:
                    # Save to active streams
                    self.config_manager.add_active_stream(camera_id, {
                        "camera_name": camera_data["name"],
                        "camera_type": camera_data["type"],
                        "quality": self.config_manager.get_config("app_settings.stream_quality", 75),
                        "fps": self.config_manager.get_config("app_settings.stream_fps", 15)
                    })
                    print(f"✅ Stream started for camera {camera_id}")
                else:
                    print(f"❌ Failed to start stream for camera {camera_id}")
    
    def _start_camera(self, camera_id: str, camera_data: Dict) -> bool:
        """Start a single camera"""
        try:
            # Add camera to manager
            success = self.camera_manager.add_camera(
                camera_id,
                camera_data["name"],
                camera_data["source"],
                camera_data["type"]
            )
            
            if success:
                # Start camera
                success = self.camera_manager.start_camera(camera_id)
                
                if success:
                    # Enable detection if configured
                    if camera_data.get("detection_enabled", False):
                        self.camera_manager.enable_people_detection(camera_id, True)
                    
                    # Update last active time
                    self.config_manager.update_camera(camera_id, {
                        "last_active": time.time()
                    })
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error starting camera {camera_id}: {e}")
            return False
    
    def add_camera_to_service(self, camera_id: str, camera_data: Dict):
        """Add a camera to the background service"""
        # Save camera configuration
        result = self.config_manager.add_camera(camera_id, camera_data)
        
        if result is None:
            print(f"❌ Failed to add camera {camera_id} to backend")
            return False
        
        print(f"✅ Camera {camera_id} added to backend successfully")
        
        # Start camera if service is running
        if self.running:
            self._start_camera(camera_id, camera_data)
            
            # Start stream if enabled
            if camera_data.get("stream_enabled", True):
                self.stream_manager.register_camera(
                    camera_id,
                    camera_data["name"],
                    camera_data["type"]
                )
                
                if self.stream_manager.start_stream(camera_id):
                    self.config_manager.add_active_stream(camera_id, {
                        "camera_name": camera_data["name"],
                        "camera_type": camera_data["type"]
                    })
        
        return True
    
    def remove_camera_from_service(self, camera_id: str):
        """Remove a camera from the background service"""
        # Stop camera and stream
        self.camera_manager.stop_camera(camera_id)
        self.stream_manager.stop_stream(camera_id)
        
        # Remove from configurations
        self.config_manager.remove_camera(camera_id)
        self.config_manager.remove_active_stream(camera_id)
    
    def is_running(self) -> bool:
        """Check if service is running"""
        return self.running
    
    def get_status(self) -> Dict:
        """Get service status"""
        cameras = self.config_manager.load_cameras()
        active_streams = self.config_manager.get_active_streams()
        
        running_cameras = []
        for camera_id in cameras.keys():
            if self.camera_manager.is_camera_running(camera_id):
                running_cameras.append(camera_id)
        
        return {
            "service_running": self.running,
            "total_cameras": len(cameras),
            "running_cameras": len(running_cameras),
            "active_streams": len(active_streams),
            "camera_details": running_cameras,
            "stream_details": list(active_streams.keys())
        }

    def set_current_user(self, username: str):
        """Set current user context for per-user data isolation."""
        self.current_user = username or ""
        self.config_manager.set_current_user(self.current_user or None)
        # After setting user, restart monitors to reflect user-specific cameras
        if self.running:
            # Stop everything from previous user context
            self.camera_manager.stop_all_cameras()
            self.stream_manager.stop_all_streams()
            # Start resources for the new user
            self.auto_start_cameras()
            if self.config_manager.should_auto_start_streams():
                self.auto_start_streams()


def run_background_service():
    """Run the background service as a standalone process"""
    print("🔧 Starting Fire Vision Pro Background Service...")
    
    service = BackgroundService()
    
    try:
        service.start()
        
        # Keep the service running
        while service.is_running():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"❌ Service error: {e}")
    finally:
        service.stop()
        print("🔚 Background service terminated")


if __name__ == "__main__":
    run_background_service()
