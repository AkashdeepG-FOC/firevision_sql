from utils.logger import logger

class NotificationService:
    """
    Service wrapper for Notification Manager.
    Handles system level OS notifications.
    """
    def __init__(self, notif_manager=None):
        self._manager = notif_manager

    def show_alert(self, camera_id, alert_type):
        if self._manager:
            self._manager.show_fire_alert(camera_id, alert_type)
        logger.info(f"Notification triggered for {camera_id}: {alert_type}")
