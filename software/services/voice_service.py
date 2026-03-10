from utils.logger import logger

class VoiceService:
    """
    Service wrapper for Voice Command Manager.
    Separates the UI from direct instantiation of the legacy voice tools.
    """
    def __init__(self, voice_manager=None):
        self._manager = voice_manager

    def start_listening(self):
        if self._manager:
            self._manager.start_listening()
            logger.info("Voice listening started")

    def stop_listening(self):
        if self._manager:
            self._manager.stop_listening()
            logger.info("Voice listening stopped")
