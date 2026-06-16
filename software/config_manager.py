import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import requests
from backend_client import backend_client

class ConfigManager:
    """Manages persistent configuration for the surveillance system"""
    
    # BACKEND_URL removed for local-only mode
    
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        import sys
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def get_user_config_dir(self):
        """Get the user configuration directory based on OS"""
        if os.name == 'nt':  # Windows
            app_data = os.getenv('APPDATA')
            return os.path.join(app_data, 'FireVision', 'config')
        else:  # Linux/Unix
            home = os.path.expanduser("~")
            return os.path.join(home, '.firevision', 'config')

    def __init__(self, config_dir=None):
        # Use user config dir by default for production persistence
        if config_dir is None:
            self.config_dir = self.get_user_config_dir()
        else:
            self.config_dir = config_dir

        self.config_file = os.path.join(self.config_dir, "app_config.json")
        self.cameras_file = os.path.join(self.config_dir, "cameras.json")
        self.users_file = os.path.join(self.config_dir, "users.json")
        self.streams_file = os.path.join(self.config_dir, "active_streams.json")
        self.sync_queue_file = os.path.join(self.config_dir, "sync_queue.json")
        self._current_user: Optional[str] = None
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Initialize default configurations
        self.init_default_configs()
        
        # Start sync queue processor - DISABLED for local mode
        # self.stop_sync = False
        # threading.Thread(target=self._process_sync_queue, daemon=True).start()

    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash"""
        return self.hash_password(password) == password_hash

    def init_default_configs(self):
        """Initialize default configuration files if they don't exist"""
        
        # Check if we have bundled config files (PyInstaller)
        bundled_config_dir = self.resource_path("config")
        
        # Helper to copy or create default
        def setup_file(filename, default_data):
            target_path = os.path.join(self.config_dir, filename)
            if not os.path.exists(target_path):
                # Try to copy from bundled config
                bundled_path = os.path.join(bundled_config_dir, filename)
                if os.path.exists(bundled_path):
                    try:
                        import shutil
                        shutil.copy2(bundled_path, target_path)
                        print(f"✅ Copied default {filename} from bundle.")
                        return
                    except Exception as e:
                        print(f"❌ Error copying bundled config {filename}: {e}")
                
                # Fallback to hardcoded default
                if filename == "app_config.json":
                    self.save_config(default_data)
                elif filename == "users.json":
                    self.save_users(default_data)
                elif filename == "cameras.json":
                    self.save_cameras(default_data)
                elif filename == "active_streams.json":
                    self.save_active_streams(default_data)

        # Default app config data
        default_config = {
            "app_settings": {
                "auto_start_cameras": True,
                "auto_start_streaming": True,
                "enable_gpu_acceleration": True,
                "dark_mode": True,
                "notification_sound": True,
                "tray_notification_shown": False,
                "check_updates_on_startup": True
            },
            "network": {
                "mobile_app_url": "http://192.168.1.4:58766",
                "backend_url": "http://localhost:5000",
                "rtsp_connection_type": "tcp",
                "rtsp_port_range": [8554, 8564]
            },
            "detection": {
                "fire_threshold": 0.5,
                "smoke_threshold": 0.6,
                "night_mode_enabled": True,
                "process_every_n_frames": 2,
                "temporal_check_enabled": True
            },
            "timeouts": {
                "camera_connect_timeout": 5,
                "frame_read_timeout": 2,
                "stream_max_latency": 0.5
            },
            "recording": {
                "default_segment_duration": 15,  # minutes
                "retention_days": 7,
                "auto_delete_oldest": True,
                "min_free_space_gb": 10
            },
            "confidence_engine": {
                # Temporal Analysis
                "temporal_window_size": 5,  # frames
                "min_detections_for_warning": 3,  # out of window
                "min_detections_for_critical": 5,  # out of window
                
                # Alert Thresholds
                "info_confidence_threshold": 0.4,
                "warning_confidence_threshold": 0.6,
                "critical_confidence_threshold": 0.75,
                
                # False Positive Suppression
                "min_bbox_area": 1000,  # pixels
                "min_bbox_width": 30,
                "min_bbox_height": 30,
                "max_bbox_movement": 50,  # pixels between frames
                "min_flicker_stability": 0.7,  # 0-1 score
                "enable_color_validation": True,
                "min_fire_color_ratio": 0.3,  # red/orange dominance
                
                # Day/Night Behavior
                "day_confidence_multiplier": 1.0,
                "night_confidence_multiplier": 0.85,
                "night_temporal_window_size": 7,
                
                # Alert Hysteresis
                "critical_cooldown_seconds": 30,
                "warning_cooldown_seconds": 15,
                "downgrade_stability_frames": 10,  # frames of low confidence before downgrade
                
                # Evidence Snapshots
                "enable_snapshots": True,
                "snapshot_on_warning": True,
                "snapshot_on_critical": True,
                "snapshot_retention_days": 30,
                "max_snapshots_per_camera": 1000
            }
        }
        
        # Check and create individual files
        setup_file("app_config.json", default_config)
        setup_file("cameras.json", [])
        setup_file("users.json", [])
        setup_file("active_streams.json", {})

    def get_network_config(self) -> Dict:
        """Get network configuration"""
        return self.get_config("network", {
            "mobile_app_url": "http://192.168.1.4:58766",
            "backend_url": "http://localhost:5000",
            "rtsp_connection_type": "tcp"
        })

    def get_detection_config(self) -> Dict:
        """Get detection configuration"""
        return self.get_config("detection", {
            "fire_threshold": 0.5,
            "smoke_threshold": 0.6,
            "night_mode_enabled": True
        })
        
    def get_timeout_config(self) -> Dict:
        """Get timeout configuration"""
        return self.get_config("timeouts", {
            "camera_connect_timeout": 5,
            "frame_read_timeout": 2
        })

    def _process_sync_queue(self):
        """Process queued sync items in background - DISABLED"""
        pass

    def sync_to_backend(self, file_type, data):
        """Send config data to backend Node.js server - DISABLED"""
        pass

    def _add_to_sync_queue(self, file_type, data):
        """Add item to sync queue file - DISABLED"""
        pass

    def load_config(self) -> Dict:
        """Load application configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config: Dict):
        """Save application configuration atomically"""
        try:
            temp_file = self.config_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(config, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename (replace)
            os.replace(temp_file, self.config_file)
            
            # self.sync_to_backend("app_config", config)
        except Exception as e:
            print(f"Error saving config: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def update_config(self, key: str, value):
        """Update a specific configuration value"""
        config = self.load_config()
        keys = key.split('.')
        current = config
        
        # Navigate to the nested key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        self.save_config(config)
    
    def get_config(self, key: str, default=None):
        """Get a specific configuration value"""
        config = self.load_config()
        keys = key.split('.')
        current = config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except KeyError:
            return default
    
    # User management
    def load_users(self) -> Dict:
        """Load users configuration - Deprecated, use backend API"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    def save_users(self, users: Dict):
        """Save users configuration"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=4)
            # self.sync_to_backend("users", users)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def sync_all_data_to_backend(self):
        """Disabled for local mode"""
        pass

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials via Local API"""
        try:
            response = requests.post(
                "http://127.0.0.1:8001/api/local/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                self._current_user = username
                return True
            return False
        except Exception as e:
            print(f"Error connecting to Local API: {e}")
            return False

    def set_current_user(self, username: Optional[str]):
        """Set the current authenticated user for per-user data filtering."""
        self._current_user = username
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> bool:
        """Create a new user via Backend API"""
        # Mapping arguments: username -> name (approx), email -> email
        return backend_client.create_user(email=email, password=password, name=username, role=role)
    
    def save_login_details(self, username: str, remember: bool = True):
        """Save login details for auto-login"""
        if remember:
            self.update_config("last_login.username", username)
            self.update_config("last_login.remember", True)
            self.update_config("last_login.login_time", datetime.now().isoformat())
        else:
            self.update_config("last_login.username", "")
            self.update_config("last_login.remember", False)
    
    def get_saved_login(self) -> Optional[str]:
        """Get saved login username if remember is enabled"""
        if self.get_config("last_login.remember", False):
            return self.get_config("last_login.username", "")
        return None
    
    # Camera management
    def load_cameras(self) -> Dict:
        """Load cameras from Backend API"""
        try:
            print("DEBUG: Calling backend_client.get_cameras()...")
            api_cameras = backend_client.get_cameras()
            print(f"DEBUG: backend_client returned {len(api_cameras)} cameras: {api_cameras}")
            
            # Convert list back to dict format expected by the app
            cameras_dict = {}
            for cam in api_cameras:
                # Map backend fields to frontend expected fields
                cam_id = str(cam.get("id"))
                
                # Determine source and type from ip_address
                source = cam.get("ip_address")
                cam_type = "ip_camera"
                
                if source == "local_webcam":
                    cam_type = "webcam"
                    source = "0"
                elif source and source.isdigit():
                    cam_type = "webcam"
                elif source and (source.endswith('.mp4') or source.endswith('.avi') or source.endswith('.mkv')):
                    cam_type = "video_file"
                    
                cameras_dict[cam_id] = {
                    "id": cam_id,
                    "name": cam.get("camera_name"),
                    "ip_address": cam.get("ip_address"),
                    "source": source, # Essential for frontend
                    "type": cam_type, # Essential for frontend
                    "location": cam.get("location"),
                    "status": cam.get("status", "inactive"),
                    "owner": self._current_user,
                    "auto_start": True, # Ensure auto-start
                    "stream_enabled": True # Ensure stream enabled
                }
            print(f"DEBUG: Processed {len(cameras_dict)} cameras for dict.")
            return cameras_dict
        except Exception as e:
            print(f"Error loading cameras from API: {e}")
            return {}
    
    def save_cameras(self, cameras: Dict):
        """Save cameras configuration - Not used when using API primarily, but kept for fallback"""
        try:
            with open(self.cameras_file, 'w') as f:
                json.dump(cameras, f, indent=4)
        except Exception as e:
            print(f"Error saving cameras: {e}")
    
    def add_camera(self, camera_id: str, camera_data: Dict):
        """Add a camera to Backend API"""
        if not self._current_user:
            print("⚠️ Cannot add camera without authenticated user context")
            return None
            
        result = backend_client.create_camera(
            name=camera_data.get("name"),
            ip_address=camera_data.get("ip_address") or camera_data.get("source"),
            location=camera_data.get("location", ""),
            status=camera_data.get("status", "active")
        )
        
        if result:
            print(f"✅ Camera created successfully in backend: {result}")
            return result
        else:
            print(f"❌ Failed to create camera in backend")
            return None

    
    def update_camera(self, camera_id: str, updates: Dict):
        """Update camera configuration"""
        if not self._current_user:
            return
        try:
            with open(self.cameras_file, 'r') as f:
                all_cameras = json.load(f)
                if isinstance(all_cameras, list):
                     import uuid
                     all_cameras = {c.get("id", str(uuid.uuid4())[:8]): c for c in all_cameras if isinstance(c, dict)}
        except Exception:
            all_cameras = {}
        cam = all_cameras.get(camera_id)
        if cam and cam.get("owner") == self._current_user:
            cam.update(updates)
            cam["last_modified"] = datetime.now().isoformat()
            all_cameras[camera_id] = cam
            self.save_cameras(all_cameras)
    
    def remove_camera(self, camera_id: str):
        """Remove camera from persistent storage"""
        if not self._current_user:
            return
        try:
            with open(self.cameras_file, 'r') as f:
                all_cameras = json.load(f)
                if isinstance(all_cameras, list):
                     import uuid
                     all_cameras = {c.get("id", str(uuid.uuid4())[:8]): c for c in all_cameras if isinstance(c, dict)}
        except Exception:
            all_cameras = {}
        cam = all_cameras.get(camera_id)
        if cam and cam.get("owner") == self._current_user:
            del all_cameras[camera_id]
            self.save_cameras(all_cameras)
    
    def get_camera(self, camera_id: str) -> Optional[Dict]:
        """Get camera configuration"""
        if not self._current_user:
            return None
        try:
            with open(self.cameras_file, 'r') as f:
                all_cameras = json.load(f)
                if isinstance(all_cameras, list):
                     import uuid
                     all_cameras = {c.get("id", str(uuid.uuid4())[:8]): c for c in all_cameras if isinstance(c, dict)}
        except Exception:
            all_cameras = {}
        cam = all_cameras.get(camera_id)
        if cam and cam.get("owner") == self._current_user:
            return cam
        return None
    
    def get_auto_start_cameras(self) -> List[Dict]:
        """Get cameras that should auto-start"""
        cameras = self.load_cameras()
        auto_start_cameras = []
        for camera_id, camera_data in cameras.items():
            if camera_data.get("auto_start", True):
                auto_start_cameras.append({
                    "id": camera_id,
                    **camera_data
                })
        return auto_start_cameras
    
    # Active streams management
    def load_active_streams(self) -> Dict:
        """Load active streams configuration"""
        try:
            with open(self.streams_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading active streams: {e}")
            return {}
    
    def save_active_streams(self, streams: Dict):
        """Save active streams configuration"""
        try:
            with open(self.streams_file, 'w') as f:
                json.dump(streams, f, indent=4)
            # self.sync_to_backend("active_streams", streams)
        except Exception as e:
            print(f"Error saving active streams: {e}")
    
    def add_active_stream(self, camera_id: str, stream_info: Dict):
        """Add an active stream"""
        streams = self.load_active_streams()
        streams[camera_id] = {
            **stream_info,
            "started_time": datetime.now().isoformat(),
            "status": "active"
        }
        self.save_active_streams(streams)
    
    def remove_active_stream(self, camera_id: str):
        """Remove an active stream"""
        streams = self.load_active_streams()
        if camera_id in streams:
            del streams[camera_id]
            self.save_active_streams(streams)
    
    def get_active_streams(self) -> Dict:
        """Get all active streams"""
        return self.load_active_streams()
    
    def should_auto_start_streams(self) -> bool:
        """Check if streams should auto-start"""
        return self.get_config("app_settings.auto_start_streaming", True)
    
    def should_auto_start_cameras(self) -> bool:
        """Check if cameras should auto-start"""
        return self.get_config("app_settings.auto_start_cameras", True)