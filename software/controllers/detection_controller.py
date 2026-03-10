from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import logger

class DetectionController(QObject):
    """
    Manages detection toggles, communicating with the detection microservice client.
    """
    detection_enabled = pyqtSignal(str, bool)

    def __init__(self, service_container):
        super().__init__()
        self.container = service_container
        self.detection_client = getattr(service_container, 'detection_service', None)

    def toggle_detection(self, camera_id, enabled):
        """Toggle AI detection for a specific camera."""
        if self.detection_client:
            if not enabled:
                self.detection_client.unregister_camera(camera_id)
        self.detection_enabled.emit(camera_id, enabled)
        logger.info(f"Detection on camera {camera_id} set to {enabled}")
