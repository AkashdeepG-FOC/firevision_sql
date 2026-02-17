#!/usr/bin/env python3
"""
Test script for FireVision Notification System
Demonstrates fire detection notification with screenshot capture and mobile app integration
"""

import cv2
import numpy as np
import time
import os
from notification_manager import NotificationManager

def create_test_fire_frame():
    """Create a test frame with simulated fire detection"""
    # Create a test frame (640x480)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some background
    frame[:] = (50, 50, 50)  # Dark gray background
    
    # Simulate fire regions (red/orange areas)
    cv2.rectangle(frame, (200, 150), (300, 250), (0, 0, 255), -1)  # Red fire
    cv2.rectangle(frame, (400, 200), (500, 300), (0, 100, 255), -1)  # Orange fire
    
    # Add some text
    cv2.putText(frame, "TEST FIRE DETECTION", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Simulated Fire Alert", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return frame

def create_test_detections():
    """Create test detection data"""
    detections = [
        {
            'bbox': [200, 150, 300, 250],
            'confidence': 0.85,
            'type': 'fire',
            'center': [250, 200],
            'area': 10000
        },
        {
            'bbox': [400, 200, 500, 300],
            'confidence': 0.78,
            'type': 'fire',
            'center': [450, 250],
            'area': 10000
        }
    ]
    return detections

def create_test_alert_info():
    """Create test alert information"""
    alert_info = {
        'fire_count': 2,
        'smoke_count': 0,
        'max_confidence': 0.85,
        'alert_type': 'fire',
        'severity': 'high'
    }
    return alert_info

def test_notification_manager():
    """Test the notification manager functionality"""
    print("🔥 FireVision Notification System Test")
    print("=" * 50)
    
    # Initialize notification manager
    notification_manager = NotificationManager(
        backend_url="http://localhost:5000",
        mobile_app_url="http://192.168.1.4:58766",
        user_id="test_user"
    )
    
    # Test connections
    print("\n🔗 Testing connections...")
    backend_ok = notification_manager.test_backend_connection()
    mobile_ok = notification_manager.test_mobile_connection()
    
    print(f"Backend connection: {'✅ OK' if backend_ok else '❌ Failed'}")
    print(f"Mobile app connection: {'✅ OK' if mobile_ok else '❌ Failed'}")
    
    # Create test data
    print("\n📸 Creating test fire detection data...")
    test_frame = create_test_fire_frame()
    test_detections = create_test_detections()
    test_alert_info = create_test_alert_info()
    
    # Save test frame for verification
    cv2.imwrite("test_fire_frame.jpg", test_frame)
    print("✅ Test frame saved as 'test_fire_frame.jpg'")
    
    # Test comprehensive notification
    print("\n🚨 Sending comprehensive fire alert...")
    results = notification_manager.send_comprehensive_fire_alert(
        camera_id="test_camera_001",
        camera_name="Test Camera",
        frame=test_frame,
        detections=test_detections,
        alert_info=test_alert_info
    )
    
    # Display results
    print("\n📊 Notification Results:")
    print(f"Backend: {'✅ Success' if results['backend'] else '❌ Failed'}")
    print(f"Mobile App: {'✅ Success' if results['mobile'] else '❌ Failed'}")
    
    # Test individual methods
    print("\n🔧 Testing individual notification methods...")
    
    # Test backend only
    print("Testing backend notification...")
    alert_id = notification_manager.send_fire_alert_to_backend(
        camera_id="test_camera_002",
        camera_name="Test Camera 2",
        frame=test_frame,
        detections=test_detections,
        alert_info=test_alert_info
    )
    print(f"Backend alert ID: {alert_id if alert_id else 'Failed'}")
    
    # Test mobile only
    print("Testing mobile app notification...")
    mobile_success = notification_manager.send_fire_alert_to_mobile(
        camera_id="test_camera_003",
        camera_name="Test Camera 3",
        frame=test_frame,
        detections=test_detections,
        alert_info=test_alert_info,
        alert_id=alert_id
    )
    print(f"Mobile notification: {'✅ Success' if mobile_success else '❌ Failed'}")
    
    # Test screenshot functionality
    print("\n📸 Testing screenshot functionality...")
    screenshot_path = notification_manager._save_screenshot(
        test_frame, "test_camera", "fire"
    )
    print(f"Screenshot saved: {screenshot_path}")
    
    # Test Base64 encoding
    print("\n🔤 Testing Base64 encoding...")
    base64_data = notification_manager._encode_frame_to_base64(test_frame)
    print(f"Base64 data length: {len(base64_data)} characters")
    print(f"Base64 preview: {base64_data[:50]}...")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    notification_manager.cleanup_old_screenshots(max_age_hours=0)  # Clean all
    notification_manager.close()
    
    print("\n✅ Test completed!")
    print("\n📋 Summary:")
    print("- Notification manager initialized")
    print("- Connections tested")
    print("- Test fire frame created")
    print("- Comprehensive alert sent")
    print("- Individual methods tested")
    print("- Screenshot functionality verified")
    print("- Base64 encoding tested")
    print("- Cleanup performed")

def test_with_real_camera():
    """Test with real camera if available"""
    print("\n📹 Testing with real camera...")
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No camera available for testing")
        return
    
    print("✅ Camera opened successfully")
    
    # Initialize notification manager
    notification_manager = NotificationManager(
        backend_url="http://localhost:5000",
        mobile_app_url="http://192.168.1.4:58766",
        user_id="camera_test_user"
    )
    
    print("📸 Capturing frame from camera...")
    ret, frame = cap.read()
    if ret:
        # Create mock detection data
        detections = [{
            'bbox': [100, 100, 200, 200],
            'confidence': 0.75,
            'type': 'fire',
            'center': [150, 150],
            'area': 10000
        }]
        
        alert_info = {
            'fire_count': 1,
            'smoke_count': 0,
            'max_confidence': 0.75,
            'alert_type': 'fire',
            'severity': 'medium'
        }
        
        # Send notification
        results = notification_manager.send_comprehensive_fire_alert(
            camera_id="real_camera_001",
            camera_name="Real Camera Test",
            frame=frame,
            detections=detections,
            alert_info=alert_info
        )
        
        print(f"Real camera test results: Backend={results['backend']}, Mobile={results['mobile']}")
    else:
        print("❌ Failed to capture frame from camera")
    
    cap.release()
    notification_manager.close()

if __name__ == "__main__":
    try:
        # Run main test
        test_notification_manager()
        
        # Ask user if they want to test with real camera
        print("\n" + "=" * 50)
        response = input("Do you want to test with a real camera? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            test_with_real_camera()
        
        print("\n🎉 All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
