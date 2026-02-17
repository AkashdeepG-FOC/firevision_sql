#!/usr/bin/env python3
"""
Demo script to show the modern alerts UI
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from alerts_manager import AlertsManager, AlertsWidget
    
    class AlertsDemoWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("🚨 Fire Vision Pro - Modern Alerts Dashboard")
            self.setGeometry(100, 100, 1200, 800)
            
            # Set dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
            """)
            
            # Create alerts manager and widget
            self.alerts_manager = AlertsManager()
            self.alerts_widget = AlertsWidget(self.alerts_manager)
            
            # Set up demo camera list
            demo_cameras = [
                ("cam_001", "Front Door Camera"),
                ("cam_002", "Kitchen Camera"),
                ("cam_003", "Backyard Camera"),
                ("cam_004", "Garage Camera"),
                ("cam_005", "Living Room Camera")
            ]
            self.alerts_widget.set_camera_list(demo_cameras)
            
            # Set central widget
            self.setCentralWidget(self.alerts_widget)
            
            # Create some demo alerts if none exist
            self.create_demo_alerts()
        
        def create_demo_alerts(self):
            """Create demo alerts for testing"""
            import time
            from datetime import datetime, timedelta
            
            # Check if we already have alerts
            existing_alerts = self.alerts_manager.get_alerts(limit=10)
            if len(existing_alerts) >= 5:
                print("✅ Demo alerts already exist")
                return
            
            print("📝 Creating demo alerts...")
            
            # Create various types of alerts with different timestamps
            demo_alerts = [
                {
                    'camera_id': 'cam_001',
                    'camera_name': 'Front Door Camera',
                    'alert_type': 'fire',
                    'severity': 'critical',
                    'confidence': 0.95,
                    'description': 'Fire detected near entrance with high confidence',
                    'timestamp_offset': -3600  # 1 hour ago
                },
                {
                    'camera_id': 'cam_002',
                    'camera_name': 'Kitchen Camera',
                    'alert_type': 'smoke',
                    'severity': 'high',
                    'confidence': 0.87,
                    'description': 'Smoke detected in kitchen area',
                    'timestamp_offset': -1800  # 30 minutes ago
                },
                {
                    'camera_id': 'cam_003',
                    'camera_name': 'Backyard Camera',
                    'alert_type': 'people',
                    'severity': 'medium',
                    'confidence': 0.78,
                    'description': '2 people detected in restricted area',
                    'timestamp_offset': -900   # 15 minutes ago
                },
                {
                    'camera_id': 'cam_004',
                    'camera_name': 'Garage Camera',
                    'alert_type': 'motion',
                    'severity': 'low',
                    'confidence': 0.65,
                    'description': 'Motion detected in garage',
                    'timestamp_offset': -300   # 5 minutes ago
                },
                {
                    'camera_id': 'cam_005',
                    'camera_name': 'Living Room Camera',
                    'alert_type': 'people',
                    'severity': 'high',
                    'confidence': 0.92,
                    'description': '3 people detected during off-hours',
                    'timestamp_offset': -60    # 1 minute ago
                }
            ]
            
            for alert_data in demo_alerts:
                # Create alert with custom timestamp
                alert = self.alerts_manager.create_alert(
                    camera_id=alert_data['camera_id'],
                    camera_name=alert_data['camera_name'],
                    alert_type=alert_data['alert_type'],
                    severity=alert_data['severity'],
                    confidence=alert_data['confidence'],
                    description=alert_data['description'],
                    metadata={
                        'detection_time': (datetime.now() + timedelta(seconds=alert_data['timestamp_offset'])).isoformat(),
                        'camera_location': alert_data['camera_name'],
                        'alert_source': 'demo_system'
                    }
                )
                
                # Manually adjust timestamp for demo
                if alert:
                    for stored_alert in self.alerts_manager.alerts:
                        if stored_alert.id == alert:
                            stored_alert.timestamp = time.time() + alert_data['timestamp_offset']
                            break
                    
                    print(f"✅ Created demo alert: {alert_data['alert_type']} on {alert_data['camera_name']}")
            
            # Save the modified alerts
            self.alerts_manager.save_alerts_to_file()
            
            # Refresh the widget
            self.alerts_widget.load_alerts()
            
            print("🎉 Demo alerts created successfully!")
    
    def main():
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Fire Vision Pro - Alerts Demo")
        app.setApplicationVersion("1.0")
        
        # Create and show the demo window
        window = AlertsDemoWindow()
        window.show()
        
        print("🚀 Modern Alerts Dashboard Demo Started!")
        print("   - View different alert types and severities")
        print("   - Test filtering by camera, type, and status")
        print("   - Check out the statistics tab")
        print("   - Try acknowledging, resolving, or marking alerts as false alarms")
        
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