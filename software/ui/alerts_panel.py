from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel

class AlertsPanel(QWidget):
    """
    Panel to display historical and active fire/smoke alerts.
    """
    def __init__(self, alert_controller):
        super().__init__()
        self.alert_controller = alert_controller
        self.setup_ui()
        
        if self.alert_controller:
            self.alert_controller.alert_triggered.connect(self.on_alert_triggered)
            
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.title = QLabel("System Alerts")
        
        # Style title
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.title)
        
        self.alert_list = QListWidget()
        self.layout.addWidget(self.alert_list)
        
    def on_alert_triggered(self, camera_id, alert_type, confidence):
        item_text = f"🚨 {alert_type.upper()} detected on Camera {camera_id} (Confidence: {confidence:.1f}%)"
        self.alert_list.insertItem(0, item_text)
