from utils.logger import logger

class RecordingService:
    """
    Service wrapper for Recording Manager.
    Separates the UI from direct instantiation of the legacy recording tools.
    """
    def __init__(self, rm_instance=None):
        self._manager = rm_instance
    
    def start_recording(self, camera_id):
        if self._manager:
            self._manager.start_recording(camera_id)
            logger.info(f"Started recording for {camera_id}")

    def stop_recording(self, camera_id):
        if self._manager:
            self._manager.stop_recording(camera_id)
            logger.info(f"Stopped recording for {camera_id}")
