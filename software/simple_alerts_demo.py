#!/usr/bin/env python3
"""
Simple demo to show the improved alerts UI
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from alerts_manager import AlertsManager, AlertsWidget
    
    def main():
        app = QApplication(sys.argv)
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("🚨 Fire Vision Pro - Modern Alerts Dashboard")
        window.setGeometry(100, 100, 1400, 900)
        
        # Set dark theme for main window
        window.setStyleSheet("""
            QMainWindow {
                background-color: #2a2a2a;
                color: #ffffff;
            }
        """)
        
        # Create alerts manager and widget
        alerts_manager = AlertsManager()
        alerts_widget = AlertsWidget(alerts_manager)
        
        # Set up demo camera list
        demo_cameras = [
            ("cam_001", "Front Door Camera"),
            ("cam_002", "Kitchen Camera"),
            ("cam_003", "Backyard Camera"),
            ("cam_004", "Garage Camera"),
            ("cam_005", "Living Room Camera")
        ]
        alerts_widget.set_camera_list(demo_cameras)
        
        # Set central widget
        window.setCentralWidget(alerts_widget)
        
        # Show window
        window.show()
        
        print("🚀 Modern Alerts Dashboard Started!")
        print("✅ Improved text visibility and padding")
        print("✅ Better contrast and modern styling")
        print("✅ Enhanced button and table appearance")
        
        sys.exit(app.exec_())
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyQt5 and all required modules are installed")
except Exception as e:
    print(f"❌ Demo failed: {e}")
    import traceback
    traceback.print_exc()