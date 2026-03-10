from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import logger

class CameraController(QObject):
    """
    Controller responsible for handling camera business logic,
    mediating between the UI, stream manager, and detection services.
    """
    camera_added = pyqtSignal(str, dict)
    camera_removed = pyqtSignal(str)
    camera_error = pyqtSignal(str, str)
    camera_status_changed = pyqtSignal(str, str)

    def __init__(self, service_container):
        super().__init__()
        self.container = service_container
        # Assume these services are populated in container
        self.config_manager = getattr(service_container, 'config_manager', None)
        self.stream_manager = getattr(service_container, 'stream_manager', None)
        self.camera_manager = getattr(service_container, 'camera_manager', None)
        
    def add_camera(self, camera_data):
        """Add a camera to the system and save it."""
        try:
            if self.config_manager:
                camera_id = self.config_manager.save_camera(camera_data)
                self.camera_added.emit(camera_id, camera_data)
                logger.info(f"Camera added successfully: {camera_id}")
                return camera_id
        except Exception as e:
            logger.error(f"Failed to add camera: {e}")
            self.camera_error.emit(camera_data.get('id', 'unknown'), str(e))
            return None

    def remove_camera(self, camera_id):
        """Remove camera from system."""
        try:
            if self.camera_manager:
                self.camera_manager.stop_camera(camera_id)
                self.camera_manager.remove_camera(camera_id)
                
            if self.config_manager:
                self.config_manager.remove_camera(camera_id)
            
            self.camera_removed.emit(camera_id)
            logger.info(f"Camera removed: {camera_id}")
        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}")

    def load_cameras(self):
        """Load cameras from configuration."""
        if self.config_manager:
            return self.config_manager.load_cameras()
        return {}

    def start_camera_stream(self, camera_id):
        if self.stream_manager:
            self.stream_manager.start_stream(camera_id)
            self.camera_status_changed.emit(camera_id, "Connected")
