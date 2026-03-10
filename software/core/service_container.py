from config.settings import settings
from utils.logger import logger

class ServiceContainer:
    """
    Centralized Dependency Injection container for the application.
    """
    def __init__(self):
        self.logger = logger
        self.settings = settings
        
        # Services will be registered here
        self.camera_service = None
        self.detection_service = None
        self.recording_service = None
        self.voice_command_service = None
        self.notification_service = None
        
    def initialize_services(self, main_window=None):
        """
        Initialize the services required by the application.
        """
        self.logger.info("Initializing Service Container...")
        # Details will be populated as modules are migrated
        pass

# Global singleton container
container = ServiceContainer()
