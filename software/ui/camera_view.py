from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLabel

class CameraView(QWidget):
    """
    Grid view for displaying multiple IP camera streams.
    """
    def __init__(self, camera_controller, detection_controller):
        super().__init__()
        self.camera_controller = camera_controller
        self.detection_controller = detection_controller
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Controls
        self.controls_layout = QHBoxLayout()
        self.add_camera_btn = QPushButton("Add Camera")
        self.add_camera_btn.clicked.connect(self.on_add_camera_clicked)
        self.controls_layout.addWidget(self.add_camera_btn)
        self.controls_layout.addStretch()
        self.layout.addLayout(self.controls_layout)
        
        # Grid for cameras
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)
        
    def on_add_camera_clicked(self):
        # Triggered when button is clicked
        pass
