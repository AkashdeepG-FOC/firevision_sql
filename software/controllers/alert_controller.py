from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import logger

class AlertController(QObject):
    """
    Manages alert logic, filtering, and communication
    with notification manager and alert panel.
    """
    alert_triggered = pyqtSignal(str, str, float) # camera_id, type, confidence
    
    def __init__(self, service_container):
        super().__init__()
        self.container = service_container
        self.notification_manager = getattr(service_container, 'notification_manager', None)
        self.alerts_manager = getattr(service_container, 'alerts_manager', None)

    def process_alert(self, camera_id, alert_type, confidence, extra_info=None):
        logger.warning(f"Alert triggered: {alert_type} on camera {camera_id} ({confidence}%)")
        self.alert_triggered.emit(camera_id, alert_type, confidence)
        
        if self.notification_manager:
            self.notification_manager.show_fire_alert(camera_id, alert_type)
            
        if self.alerts_manager:
            self.alerts_manager.add_alert(camera_id, alert_type, confidence)
