import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from ui.camera_view import CameraView
from ui.alerts_panel import AlertsPanel
from ui.map_widget import LightweightMapWebView

class MainWindow(QMainWindow):
    """
    Refactored Main Window for FireVision.
    Initializes the UI layout and delegates business logic to controllers.
    """
    def __init__(self, service_container):
        super().__init__()
        self.container = service_container
        
        # Initialize Controllers
        self.camera_controller = getattr(service_container, 'camera_controller', None)
        self.alert_controller = getattr(service_container, 'alert_controller', None)
        self.detection_controller = getattr(service_container, 'detection_controller', None)
        
        self.setWindowTitle("FireVision AI Surveillance System")
        self.setGeometry(100, 100, 1280, 720)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        
        # 1. Camera View Tab
        self.camera_view = CameraView(self.camera_controller, self.detection_controller)
        self.tabs.addTab(self.camera_view, "Live Cameras")
        
        # 2. Alerts Panel Tab
        self.alerts_panel = AlertsPanel(self.alert_controller)
        self.tabs.addTab(self.alerts_panel, "Alerts")
        
        # 3. Map View Tab
        self.map_view = LightweightMapWebView()
        self.map_view.load_minimal_leaflet()
        self.tabs.addTab(self.map_view, "Camera Locations")
        
        self.main_layout.addWidget(self.tabs)
