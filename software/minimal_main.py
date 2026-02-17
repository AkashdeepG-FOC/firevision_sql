
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

class MinimalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Vision Pro - Minimal Build")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        label = QLabel("Fire Vision Pro - Minimal Build Successful!")
        label.setStyleSheet("font-size: 24px; color: #00BFAE;")
        layout.addWidget(label)
        
        status_label = QLabel("This is a minimal build to test PyInstaller compatibility")
        status_label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(status_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalApp()
    window.show()
    sys.exit(app.exec_())
