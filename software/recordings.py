from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class RecordingPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Recording Page")
        layout.addWidget(label)
        self.setLayout(layout)