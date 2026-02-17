#!/usr/bin/env python3
"""
Test script to verify camera sync with webcam type works correctly
"""

import requests
import json

def test_camera_sync():
    """Test camera sync with webcam type"""
    backend_url = "http://localhost:5000"
    
    # Test data with webcam type
    test_cameras = {
        "test_webcam_01": {
            "name": "Test Webcam Camera",
            "source": "0",
            "type": "webcam",  # This should now be accepted
            "user_id": "test_user",
            "added_date": "2025-09-25",
            "detection_enabled": True,
            "auto_start": True,
            "stream_enabled": True,
            "people_detection_enabled": False,
            "fire_smoke_detection_enabled": True,
            "recording_enabled": False,
            "status": "active"
        },
        "test_usb_01": {
            "name": "Test USB Camera",
            "source": "1",
            "type": "usb",
            "user_id": "test_user",
            "added_date": "2025-09-25",
            "detection_enabled": True,
            "auto_start": True,
            "stream_enabled": True,
            "people_detection_enabled": True,
            "fire_smoke_detection_enabled": True,
            "recording_enabled": False,
            "status": "active"
        }
    }
    
    try:
        print("🧪 Testing camera sync with webcam type...")
        
        # Send test data to backend
        response = requests.post(
            f"{backend_url}/api/config/cameras",
            json=test_cameras,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Camera sync successful!")
            print(f"   Synced: {result['synced_count']}/{result['total_count']}")
            print(f"   Errors: {len(result.get('errors', []))}")
            
            if result.get('errors'):
                print("❌ Errors found:")
                for error in result['errors']:
                    print(f"   - {error['camera_id']}: {error['error']}")
            else:
                print("✅ No errors - webcam type validation fixed!")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_backend_health():
    """Test backend health"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=3)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Backend health: {result['status']}")
            print(f"   MongoDB: {result['mongodb']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

if __name__ == "__main__":
    print("🔥 Fire Vision Pro - Camera Sync Test")
    print("=" * 50)
    
    # Test backend health first
    if test_backend_health():
        print()
        test_camera_sync()
    else:
        print("❌ Backend not available - skipping camera sync test")
    
    print("\n" + "=" * 50)
    print("✅ Test completed")