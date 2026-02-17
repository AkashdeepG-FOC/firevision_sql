#!/usr/bin/env python3
"""
Test script to verify header visibility improvements
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from alerts_manager import AlertsManager, AlertsWidget
    
    def test_header_visibility():
        """Test the header visibility improvements"""
        app = QApplication(sys.argv)
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("🚨 Header Visibility Test - Fire Vision Pro")
        window.setGeometry(100, 100, 1400, 900)
        
        # Set dark theme
        window.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
        """)
        
        # Create alerts manager and widget
        alerts_manager = AlertsManager()
        alerts_widget = AlertsWidget(alerts_manager)
        
        # Set up test camera list
        test_cameras = [
            ("cam_001", "Front Door Camera"),
            ("cam_002", "Kitchen Camera"),
            ("cam_003", "Backyard Camera"),
            ("cam_004", "Garage Camera"),
            ("cam_005", "Living Room Camera"),
            ("cam_006", "Office Camera")
        ]
        alerts_widget.set_camera_list(test_cameras)
        
        # Set central widget
        window.setCentralWidget(alerts_widget)
        
        # Show window
        window.show()
        
        print("🎯 Header Visibility Test Started!")
        print("✅ Improvements made:")
        print("   - Increased header height from 100px to 140px")
        print("   - Added more padding and margins (25px, 20px)")
        print("   - Increased font sizes (labels: 14px, title: 22px)")
        print("   - Better spacing between elements (18px vertical, 20px horizontal)")
        print("   - Larger input controls (min-width: 140px, min-height: 25px)")
        print("   - More padding in buttons and inputs")
        print("")
        print("🔍 Check the header visibility:")
        print("   - Title should be clearly visible")
        print("   - Filter labels should have proper spacing")
        print("   - Dropdown menus should be easy to read")
        print("   - Action buttons should be well-spaced")
        
        # Auto-close after 10 seconds for automated testing
        QTimer.singleShot(10000, app.quit)
        
        return app.exec_()
    
    if __name__ == "__main__":
        test_header_visibility()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyQt5 and all required modules are installed")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()