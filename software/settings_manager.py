import os
import json
import shutil
from PyQt5.QtCore import QObject, pyqtSignal


class SettingsManager(QObject):
    settings_changed = pyqtSignal(dict)  # settings dict

    def __init__(self, settings_file="settings.json"):
        super().__init__()
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self):
        """
        Load settings from file

        Returns:
            dict: Settings dictionary
        """
        default_settings = {
            "cameras": {},
            
            # General Settings
            "general": {
                "language": "English",
                "theme_mode": "Dark",
                "auto_start_boot": False,
                "start_minimized": False,
                "show_notifications": True,
                "default_save_location": "./logs"
            },
            
            # Fire Detection Settings
            "fire_detection": {
                "model_selection": "YOLOv8n",
                "model_path": "best_m.pt",
                "detection_confidence": 0.5,
                "nms_threshold": 0.45,
                "fire_sensitivity": "Medium",
                "smoke_sensitivity": "Medium",
                "roi_enabled": False,
                "roi_regions": [],
                "performance_mode": "Balanced"
            },
            
            # Controller Settings
            "controller": {
                "esp32_ip": "",
                "is_connected": False
            },
            
            # Camera Settings
            "camera": {
                "source_type": "Laptop Cam",
                "ip_camera_url": "",
                "frame_size": "720p",
                "frame_rate": 30,
                "brightness": 50,
                "contrast": 50,
                "saturation": 50,
                "ai_processing_mode": "Full Frame"
            },
            
            # Alert & Notification Settings
            "alerts": {
                "sound_alert": True,
                "email_alert": False,
                "desktop_notification": True,
                "alert_sound_file": "assests/audio/alarm.mp3",
                "cooldown_time": 10,
                "repeated_alerts": True,
                "alert_message_template": "🔥 Fire detected at {location} on {date} at {time}"
            },
            
            # Data & Logging Settings
            "logging": {
                "enable_logging": True,
                "log_text": True,
                "log_images": True,
                "log_videos": False,
                "auto_cleanup_enabled": True,
                "keep_logs_days": 30,
                "max_storage_mb": 1000
            },
            
            # Cloud Settings
            "cloud": {
                "cloud_enabled": False,
                "api_key": "",
                "sync_events": False,
                "cloud_dashboard_url": ""
            },
            
            # Security Settings
            "security": {
                "password_protection": False,
                "password_hash": "",
                "user_role": "Admin",
                "encrypt_logs": False
            },
            
            "storage": {
                "path": "./recordings",
                "limit": 500,  # GB
                "auto_delete": True,
                "compression": "medium"
            },
            "detection": {
                "motion_sensitivity": 0.5,
                "object_confidence": 0.7,
                "notifications": True,
                "sound_alerts": False,
                "email_alerts": False,
                "email_settings": {
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                }
            },
            "recording": {
                "auto_record": True,
                "record_on_motion": True,
                "pre_record_seconds": 5,
                "post_record_seconds": 10,
                "quality": "high",
                "fps": 20
            },
            "system": {
                "startup": False,
                "minimize_to_tray": False,
                "dark_theme": True,
                "language": "en",
                "log_level": "info",
                "use_gpu": True,
                "hardware_acceleration": True,
                "auto_update": True,
                "check_updates_on_start": True,
                "auto_mode_optimizer": True,
                "nvr_mode_enabled": False,
                "optimization_mode": None,
                "hardware_specs": {}
            },
            "network": {
                "web_interface_enabled": False,
                "web_interface_port": 8080,
                "remote_access": False,
                "stream_quality": "medium"
            },
            "ui": {
                "grid_columns": 2,
                "show_timestamps": True,
                "show_camera_names": True,
                "fullscreen_on_doubleclick": True
            },
            
            # Email Configuration
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "",
                "smtp_password": "",
                "from_email": "",
                "to_emails": []
            },
            
            # About
            "about": {
                "version": "1.0.0",
                "build_date": "2025-12-09",
                "developer": "FireVision Team",
                "support_email": "support@firevision.com"
            }
        }

        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)

                # Merge with default settings to ensure all keys exist
                merged_settings = self._merge_settings(default_settings, loaded_settings)
                return merged_settings
        except Exception as e:
            print(f"Error loading settings: {e}")

        # Save default settings if file doesn't exist or loading failed
        self._save_settings(default_settings)
        return default_settings

    def _merge_settings(self, default, loaded):
        """
        Recursively merge loaded settings with default settings

        Args:
            default (dict): Default settings
            loaded (dict): Loaded settings

        Returns:
            dict: Merged settings
        """
        result = default.copy()

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value

        return result

    def _save_settings(self, settings=None):
        """
        Save settings to file

        Args:
            settings (dict, optional): Settings dictionary, uses self.settings if None

        Returns:
            bool: True if settings saved successfully, False otherwise
        """
        if settings is None:
            settings = self.settings

        try:
            # Create backup of existing settings
            if os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.bak"
                shutil.copy2(self.settings_file, backup_file)

            # Save settings
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False, default=str)

            return True

        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_settings(self):
        """
        Get all settings

        Returns:
            dict: Settings dictionary
        """
        return self.settings.copy()

    def get_setting(self, key, default=None):
        """
        Get a specific setting value

        Args:
            key (str): Setting key (supports dot notation, e.g., 'storage.path')
            default: Default value if key not found

        Returns:
            Any: Setting value or default
        """
        try:
            keys = key.split('.')
            value = self.settings

            for k in keys:
                value = value[k]

            return value

        except (KeyError, TypeError):
            return default

    def set_setting(self, key, value):
        """
        Set a specific setting value

        Args:
            key (str): Setting key (supports dot notation, e.g., 'storage.path')
            value: Value to set

        Returns:
            bool: True if setting was set successfully, False otherwise
        """
        try:
            keys = key.split('.')
            settings_ref = self.settings

            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in settings_ref:
                    settings_ref[k] = {}
                settings_ref = settings_ref[k]

            # Set the value
            settings_ref[keys[-1]] = value

            return True

        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False

    def save_settings(self, settings=None):
        """
        Save settings and emit signal

        Args:
            settings (dict, optional): Settings to save, uses current settings if None

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if settings is not None:
            self.settings = settings

        success = self._save_settings()

        if success:
            self.settings_changed.emit(self.settings.copy())

        return success

    def reset_settings(self):
        """
        Reset settings to default values

        Returns:
            bool: True if reset successfully, False otherwise
        """
        try:
            # Remove existing settings file
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)

            # Reload default settings
            self.settings = self._load_settings()

            # Emit signal
            self.settings_changed.emit(self.settings.copy())

            return True

        except Exception as e:
            print(f"Error resetting settings: {e}")
            return False

    def export_settings(self, file_path):
        """
        Export settings to a file

        Args:
            file_path (str): Path to export file

        Returns:
            bool: True if exported successfully, False otherwise
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False, default=str)

            return True

        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path):
        """
        Import settings from a file

        Args:
            file_path (str): Path to import file

        Returns:
            bool: True if imported successfully, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_settings = json.load(f)

            # Merge with current settings
            self.settings = self._merge_settings(self.settings, imported_settings)

            # Save merged settings
            success = self._save_settings()

            if success:
                self.settings_changed.emit(self.settings.copy())

            return success

        except Exception as e:
            print(f"Error importing settings: {e}")
            return False

    def get_camera_settings(self, camera_id):
        """
        Get settings for a specific camera

        Args:
            camera_id (str): Camera ID

        Returns:
            dict: Camera settings
        """
        cameras = self.settings.get("cameras", {})
        return cameras.get(camera_id, {})

    def set_camera_settings(self, camera_id, settings):
        """
        Set settings for a specific camera

        Args:
            camera_id (str): Camera ID
            settings (dict): Camera settings

        Returns:
            bool: True if set successfully, False otherwise
        """
        try:
            if "cameras" not in self.settings:
                self.settings["cameras"] = {}

            self.settings["cameras"][camera_id] = settings
            return True

        except Exception as e:
            print(f"Error setting camera settings for {camera_id}: {e}")
            return False

    def remove_camera_settings(self, camera_id):
        """
        Remove settings for a specific camera

        Args:
            camera_id (str): Camera ID

        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            cameras = self.settings.get("cameras", {})
            if camera_id in cameras:
                del cameras[camera_id]
                return True

            return False

        except Exception as e:
            print(f"Error removing camera settings for {camera_id}: {e}")
            return False

    def validate_settings(self):
        """
        Validate current settings

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []

        try:
            # Validate storage settings
            storage = self.settings.get("storage", {})
            storage_path = storage.get("path", "")

            if not storage_path:
                errors.append("Storage path is empty")
            elif not os.path.isabs(storage_path):
                # Try to create relative path
                try:
                    os.makedirs(storage_path, exist_ok=True)
                except:
                    errors.append(f"Cannot create storage directory: {storage_path}")

            storage_limit = storage.get("limit", 0)
            if not isinstance(storage_limit, (int, float)) or storage_limit <= 0:
                errors.append("Storage limit must be a positive number")

            # Validate detection settings
            detection = self.settings.get("detection", {})
            motion_sensitivity = detection.get("motion_sensitivity", 0.5)
            if not 0 <= motion_sensitivity <= 1:
                errors.append("Motion sensitivity must be between 0 and 1")

            object_confidence = detection.get("object_confidence", 0.7)
            if not 0 <= object_confidence <= 1:
                errors.append("Object confidence must be between 0 and 1")

            # Validate recording settings
            recording = self.settings.get("recording", {})
            fps = recording.get("fps", 20)
            if not isinstance(fps, (int, float)) or fps <= 0 or fps > 60:
                errors.append("FPS must be between 1 and 60")

            pre_record = recording.get("pre_record_seconds", 5)
            if not isinstance(pre_record, (int, float)) or pre_record < 0:
                errors.append("Pre-record seconds must be non-negative")

            post_record = recording.get("post_record_seconds", 10)
            if not isinstance(post_record, (int, float)) or post_record < 0:
                errors.append("Post-record seconds must be non-negative")

            # Validate network settings
            network = self.settings.get("network", {})
            web_port = network.get("web_interface_port", 8080)
            if not isinstance(web_port, int) or not 1024 <= web_port <= 65535:
                errors.append("Web interface port must be between 1024 and 65535")

        except Exception as e:
            errors.append(f"Settings validation error: {e}")

        return len(errors) == 0, errors

    def get_default_settings(self):
        """
        Get default settings

        Returns:
            dict: Default settings dictionary
        """
        # Create a new instance to get fresh defaults
        temp_manager = SettingsManager("temp_settings.json")
        defaults = temp_manager._load_settings()

        # Clean up temp file
        if os.path.exists("temp_settings.json"):
            try:
                os.remove("temp_settings.json")
            except:
                pass

        return defaults