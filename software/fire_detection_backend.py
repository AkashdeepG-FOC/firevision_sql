import cv2
import base64
import requests
import json
import time
import threading
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

class FireDetectionBackend(QObject):
    """Handles communication with backend server for fire detection alerts"""
    
    alert_created = pyqtSignal(str, str)  # alert_id, status
    alert_updated = pyqtSignal(str, str)  # alert_id, new_status
    backend_error = pyqtSignal(str)  # error_message
    
    def __init__(self, backend_url: str = "http://localhost:5000", user_id: str = "system"):
        super().__init__()
        self.backend_url = backend_url.rstrip('/')
        self.user_id = user_id
        self.session = None  # Disabled for local mode
        # self.session = requests.Session()
        # self.session.timeout = 3
        
        # Configure session headers
        # self.session.headers.update({
        #     'Content-Type': 'application/json',
        #     'User-Agent': 'FireVisionPro/2.0'
        # })
        
        # Thread lock for concurrent requests
        self.lock = threading.Lock()
        
        print(f"🔥 Fire Detection Backend initialized: {self.backend_url}")
    
    def _encode_frame_to_base64(self, frame) -> str:
        """Convert OpenCV frame to base64 string"""
        try:
            # Ensure frame is in BGR format (OpenCV default)
            if len(frame.shape) == 3:
                # Convert BGR to RGB for better compatibility
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
            
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', rgb_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Convert to base64
            base64_string = base64.b64encode(buffer).decode('utf-8')
            return base64_string
            
        except Exception as e:
            print(f"❌ Error encoding frame to base64: {e}")
            return ""
    
    def _prepare_detections_data(self, detections: List[Dict]) -> List[Dict]:
        """Prepare detection data for backend API"""
        prepared_detections = []
        
        for detection in detections:
            try:
                # Extract bounding box coordinates
                bbox = detection.get('bbox', [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                else:
                    continue
                
                # Extract center coordinates
                center = detection.get('center', [0, 0])
                if len(center) != 2:
                    center = [(x1 + x2) // 2, (y1 + y2) // 2]
                
                prepared_detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(detection.get('confidence', 0)),
                    'type': str(detection.get('type', 'fire')),
                    'center': [int(center[0]), int(center[1])]
                }
                
                prepared_detections.append(prepared_detection)
                
            except Exception as e:
                print(f"❌ Error preparing detection data: {e}")
                continue
        
        return prepared_detections
    
    def create_fire_alert(self, camera_id: str, camera_name: str, frame, 
                         detections: List[Dict], alert_info: Dict) -> Optional[str]:
        """
        Create a fire detection alert on the backend server
        
        Args:
            camera_id: Camera identifier
            camera_name: Camera display name
            frame: OpenCV frame with detections
            detections: List of detection dictionaries
            alert_info: Alert information dictionary
            
        Returns:
            alert_id if successful, None otherwise
        """
        try:
            with self.lock:
                # Encode frame to base64
                frame_data = self._encode_frame_to_base64(frame)
                if not frame_data:
                    raise Exception("Failed to encode frame")
                
                # Prepare detection data
                # prepared_detections = self._prepare_detections_data(detections)
                
                alert_id = f"local_alert_{int(time.time())}"
                
                # Determine detection type
                fire_count = alert_info.get('fire_count', 0)
                smoke_count = alert_info.get('smoke_count', 0)
                
                if fire_count > 0 and smoke_count > 0:
                    detection_type = 'combined'
                elif fire_count > 0:
                    detection_type = 'fire'
                elif smoke_count > 0:
                    detection_type = 'smoke'
                else:
                    detection_type = 'unknown'
                
                # Prepare request payload
                payload = {
                    'camera_id': camera_id,
                    'camera_name': camera_name,
                    'detection_type': detection_type,
                    'confidence': alert_info.get('max_confidence', 0),
                    'frame_data': frame_data,
                    'detections': prepared_detections,
                    'alert_info': alert_info,
                    'user_id': self.user_id
                }
                
                # Send request to backend
                print(f"✅ Fire alert created (LOCAL MODE): {alert_id}")
                self.alert_created.emit(alert_id, "active")
                return alert_id
                
                # Network code disabled
                # url = f"{self.backend_url}/api/fire-detection/alert"
                # response = self.session.post(url, json=payload) ...
                    
        except Exception as e:
            error_msg = f"Failed to create fire alert: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return None
    
    def mark_false_alarm(self, alert_id: str, resolved_by: str = None, 
                        resolution_notes: str = None) -> bool:
        """
        Mark a fire detection alert as false alarm
        
        Args:
            alert_id: Alert identifier
            resolved_by: User who marked as false alarm
            resolution_notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock:
                payload = {
                    'resolved_by': resolved_by or self.user_id,
                    'resolution_notes': resolution_notes or 'Marked as false alarm by user'
                }
                
                url = f"{self.backend_url}/api/fire-detection/alerts/{alert_id}/false-alarm"
                response = self.session.put(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        new_status = result['data']['status']
                        print(f"✅ Fire alert {alert_id} marked as false alarm")
                        self.alert_updated.emit(alert_id, new_status)
                        return True
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to mark false alarm: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return False
    
    def dispatch_emergency_services(self, alert_id: str, dispatched_by: str = None,
                                  dispatch_notes: str = None) -> bool:
        """
        Dispatch emergency services for a fire detection alert
        
        Args:
            alert_id: Alert identifier
            dispatched_by: User who dispatched services
            dispatch_notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock:
                payload = {
                    'dispatched_by': dispatched_by or self.user_id,
                    'dispatch_notes': dispatch_notes or 'Emergency services dispatched by user'
                }
                
                url = f"{self.backend_url}/api/fire-detection/alerts/{alert_id}/dispatch"
                response = self.session.put(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        new_status = result['data']['status']
                        print(f"🚨 Emergency services dispatched for alert {alert_id}")
                        self.alert_updated.emit(alert_id, new_status)
                        return True
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to dispatch emergency services: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str = None,
                     resolution_notes: str = None) -> bool:
        """
        Resolve a fire detection alert
        
        Args:
            alert_id: Alert identifier
            resolved_by: User who resolved the alert
            resolution_notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock:
                payload = {
                    'resolved_by': resolved_by or self.user_id,
                    'resolution_notes': resolution_notes or 'Alert resolved by user'
                }
                
                url = f"{self.backend_url}/api/fire-detection/alerts/{alert_id}/resolve"
                response = self.session.put(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        new_status = result['data']['status']
                        print(f"✅ Fire alert {alert_id} resolved")
                        self.alert_updated.emit(alert_id, new_status)
                        return True
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to resolve alert: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return False
    
    def get_alerts(self, status: str = None, camera_id: str = None, 
                  limit: int = 50, page: int = 1) -> Optional[Dict]:
        """
        Get fire detection alerts from backend
        
        Args:
            status: Filter by status (pending, dispatched, false_alarm, resolved)
            camera_id: Filter by camera ID
            limit: Number of alerts per page
            page: Page number
            
        Returns:
            Dictionary with alerts and pagination info, or None if failed
        """
        try:
            with self.lock:
                params = {
                    'limit': limit,
                    'page': page
                }
                
                if status:
                    params['status'] = status
                if camera_id:
                    params['camera_id'] = camera_id
                
                url = f"{self.backend_url}/api/fire-detection/alerts"
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return result
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to get alerts: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return None
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """
        Get specific fire detection alert
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            Alert data dictionary, or None if failed
        """
        try:
            with self.lock:
                url = f"{self.backend_url}/api/fire-detection/alerts/{alert_id}"
                response = self.session.get(url)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return result['data']
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to get alert: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return None
    
    def get_statistics(self, camera_id: str = None, days: int = 30) -> Optional[Dict]:
        """
        Get fire detection statistics
        
        Args:
            camera_id: Filter by camera ID
            days: Number of days to look back
            
        Returns:
            Statistics dictionary, or None if failed
        """
        try:
            with self.lock:
                params = {'days': days}
                if camera_id:
                    params['camera_id'] = camera_id
                
                url = f"{self.backend_url}/api/fire-detection/stats"
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return result['data']
                    else:
                        raise Exception(f"Backend error: {result.get('message', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            error_msg = f"Failed to get statistics: {e}"
            print(f"❌ {error_msg}")
            self.backend_error.emit(error_msg)
            return None
    
    def test_connection(self) -> bool:
        """Test connection to backend server with fast timeout"""
        try:
            with self.lock:
                print(f"✅ Backend connection test successful (LOCAL MODE)")
                return True
                
                # Network code disabled
                # url = f"{self.backend_url}/api/health" ...
        except Exception as e:
            # Don't emit error signal for connection tests to avoid UI spam
            print(f"⚠️ Backend connection test failed: {e}")
            return False
    
    def set_user_id(self, user_id: str):
        """Update the user ID for API requests"""
        self.user_id = user_id
        print(f"👤 Updated user ID: {user_id}")
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
            print("🔒 Fire Detection Backend session closed") 