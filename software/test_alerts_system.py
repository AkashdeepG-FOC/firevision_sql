#!/usr/bin/env python3
"""
Test script for the alerts system
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from alerts_manager import AlertsManager
    
    def test_alerts_system():
        """Test the alerts system functionality"""
        print("🧪 Testing Alerts System...")
        
        # Create alerts manager
        alerts_manager = AlertsManager()
        
        # Test creating alerts
        print("\n📝 Creating test alerts...")
        
        # Create fire alert
        fire_alert_id = alerts_manager.create_alert(
            camera_id="cam_001",
            camera_name="Front Door Camera",
            alert_type="fire",
            severity="critical",
            confidence=0.95,
            description="Fire detected with high confidence",
            metadata={
                'detection_time': datetime.now().isoformat(),
                'camera_location': 'Front entrance',
                'alert_source': 'ai_detection'
            }
        )
        print(f"✅ Fire alert created: {fire_alert_id}")
        
        # Create smoke alert
        smoke_alert_id = alerts_manager.create_alert(
            camera_id="cam_002",
            camera_name="Kitchen Camera",
            alert_type="smoke",
            severity="high",
            confidence=0.87,
            description="Smoke detected in kitchen area",
            metadata={
                'detection_time': datetime.now().isoformat(),
                'camera_location': 'Kitchen',
                'alert_source': 'ai_detection'
            }
        )
        print(f"✅ Smoke alert created: {smoke_alert_id}")
        
        # Create people alert
        people_alert_id = alerts_manager.create_alert(
            camera_id="cam_003",
            camera_name="Backyard Camera",
            alert_type="people",
            severity="medium",
            confidence=0.78,
            description="Person detected in restricted area",
            metadata={
                'detection_time': datetime.now().isoformat(),
                'camera_location': 'Backyard',
                'alert_source': 'ai_detection'
            }
        )
        print(f"✅ People alert created: {people_alert_id}")
        
        # Test retrieving alerts
        print("\n📋 Retrieving alerts...")
        all_alerts = alerts_manager.get_alerts()
        print(f"✅ Retrieved {len(all_alerts)} alerts")
        
        for alert in all_alerts:
            print(f"   - {alert.alert_type.upper()}: {alert.camera_name} ({alert.severity}) - {alert.description}")
        
        # Test statistics
        print("\n📊 Getting statistics...")
        stats = alerts_manager.get_alert_statistics()
        print(f"✅ Statistics:")
        print(f"   - Total alerts: {stats['total_alerts']}")
        print(f"   - Active alerts: {stats['active_alerts']}")
        print(f"   - Recent alerts: {stats['recent_alerts']}")
        print(f"   - Alerts by type: {stats['alerts_by_type']}")
        print(f"   - Alerts by severity: {stats['alerts_by_severity']}")
        
        # Test alert actions
        print("\n🔧 Testing alert actions...")
        if fire_alert_id:
            # Acknowledge alert
            success = alerts_manager.acknowledge_alert(fire_alert_id, "test_user")
            print(f"✅ Acknowledged fire alert: {success}")
            
            # Resolve alert
            success = alerts_manager.resolve_alert(fire_alert_id, "test_user")
            print(f"✅ Resolved fire alert: {success}")
        
        if smoke_alert_id:
            # Mark as false alarm
            success = alerts_manager.mark_false_alarm(smoke_alert_id, "test_user")
            print(f"✅ Marked smoke alert as false alarm: {success}")
        
        print("\n🎉 Alerts system test completed successfully!")
        return True
        
    if __name__ == "__main__":
        test_alerts_system()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()