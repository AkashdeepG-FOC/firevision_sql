import sys
import os
import time
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# Add software directory to path
sys.path.append('d:/giit\firevision_sql/software')

# Mock backend_client
from backend_client import backend_client

class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data
        
    def json(self):
        return self.json_data

def delayed_post(url, json=None, data=None, headers=None):
    print(f"[Mock] POST to {url} - Simulating 2s delay...")
    time.sleep(2)
    return MockResponse(200, {"id": 123, "status": "active"})

backend_client.session.post = delayed_post

from alerts_manager import AlertsManager
from fire_smoke_detector import FireSmokeDetector

# Mock ConfidenceEngine for FireSmokeDetector
class MockConfidenceEngine:
    def get_detection_summary(self, camera_id):
        return {'detections_in_window': 5, 'window_size': 10}

def test_async_all():
    app = QApplication(sys.argv)
    
    # 1. Test AlertsManager
    manager = AlertsManager()
    start_time = time.time()
    print("\n--- Testing AlertsManager Asynchronicity ---")
    alert_id = manager.create_alert(
        camera_id="1",
        camera_name="Test Camera",
        alert_type="fire",
        severity="critical",
        confidence=0.95,
        description="Test fire detection"
    )
    duration = time.time() - start_time
    print(f"Alert creation call took: {duration:.4f} seconds")
    
    if duration < 0.5:
        print("✅ SUCCESS: AlertsManager is asynchronous!")
    else:
        print("❌ FAILURE: AlertsManager took too long.")

    # 2. Test FireSmokeDetector Snapshot
    print("\n--- Testing FireSmokeDetector Snapshot Asynchronicity ---")
    detector = FireSmokeDetector()
    detector.confidence_engine = MockConfidenceEngine()
    
    # Mock frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    detections = []
    
    # Mock cv2.imwrite to simulate delay
    import cv2
    original_imwrite = cv2.imwrite
    def delayed_imwrite(path, img):
        print(f"[Mock] Writing image to {path} - Simulating 1s delay...")
        time.sleep(1)
        # Return True without actually writing to save space in temp
        return True
    
    cv2.imwrite = delayed_imwrite
    
    start_time = time.time()
    detector._capture_evidence_snapshot(
        camera_id="test_cam",
        frame=frame,
        detections=detections,
        alert_level="CRITICAL",
        confidence=0.99,
        is_night=False
    )
    duration = time.time() - start_time
    print(f"Snapshot initiation call took: {duration:.4f} seconds")
    
    if duration < 0.2:
        print("✅ SUCCESS: FireSmokeDetector snapshot is asynchronous!")
    else:
        print("❌ FAILURE: FireSmokeDetector snapshot call took too long.")

    print("\nWaiting for background tasks to complete...")
    # Give it some time to finish background tasks
    for _ in range(40):
        QCoreApplication.processEvents()
        time.sleep(0.1)
        
    print("✅ Finished waiting. Check console for background completion logs.")
    # Restore cv2.imwrite
    cv2.imwrite = original_imwrite

if __name__ == "__main__":
    test_async_all()
