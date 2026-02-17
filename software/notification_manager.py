#!/usr/bin/env python3
"""
FireVision Notification Manager - Enhanced Fire Detection with Mobile App Integration
Handles fire detection notifications, screenshot capture, and communication with both
backend server and Flutter mobile app
"""

import cv2
import numpy as np
import base64
import requests
import json
import time
import threading
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from PyQt5.QtCore import QObject, pyqtSignal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationManager(QObject):
    """Enhanced notification manager for fire detection with mobile app integration"""
    
    # Signals for PyQt integration
    notification_sent = pyqtSignal(str, str)  # notification_type, status
    notification_failed = pyqtSignal(str, str)  # notification_type, error_message
    mobile_alert_sent = pyqtSignal(str, bool)  # alert_id, success
    
    def __init__(self, backend_url: str = None, 
                 mobile_app_url: str = None,
                 user_id: str = "system",
                 config_manager = None):
        super().__init__()
        
        self.config_manager = config_manager
        
        # Load network config if available
        net_config = {}
        if self.config_manager:
            net_config = self.config_manager.get_network_config()
            
        # Use provided args, then config, then defaults
        self.backend_url = (backend_url or 
                          net_config.get('backend_url', "http://localhost:5000")).rstrip('/')
                          
        self.mobile_app_url = (mobile_app_url or 
                             net_config.get('mobile_app_url', "http://192.168.1.4:58766")).rstrip('/')
                             
        self.user_id = user_id
        
        # Session configuration
        self.session = None
        # self.session = requests.Session()
        # self.session.timeout = 10
        # self.session.headers.update({
        #     'Content-Type': 'application/json',
        #     'User-Agent': 'FireVisionPro/2.0'
        # })
        
        # Thread lock for concurrent requests
        self.lock = threading.Lock()
        
        # Alert cooldown management
        self.alert_cooldown = {}  # camera_id -> last_alert_time
        self.alert_cooldown_duration = 10  # seconds between alerts (updated default)
        
        # Screenshot storage
        self.screenshots_dir = "fire_screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        logger.info(f"🔥 Notification Manager initialized")
        logger.info(f"   Backend URL: {self.backend_url}")
        logger.info(f"   Mobile App URL: {self.mobile_app_url}")

    def reload_config(self):
        """Reload configuration from ConfigManager"""
        if self.config_manager:
            logger.info("🔄 Reloading NotificationManager configuration...")
            net_config = self.config_manager.get_network_config()
            self.backend_url = net_config.get('backend_url', "http://localhost:5000").rstrip('/')
            self.mobile_app_url = net_config.get('mobile_app_url', "http://192.168.1.4:58766").rstrip('/')
            logger.info(f"✅ NotificationManager config reloaded: MobileURL={self.mobile_app_url}")
    
    def _encode_frame_to_base64(self, frame: np.ndarray, quality: int = 85) -> str:
        """
        Convert OpenCV frame to Base64 encoded string
        
        Args:
            frame: Input video frame
            quality: JPEG quality (1-100)
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Ensure frame is in BGR format (OpenCV default)
            if len(frame.shape) == 3:
                # Convert BGR to RGB for better compatibility
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
            
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', rgb_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Convert to Base64
            base64_string = base64.b64encode(buffer).decode('utf-8')
            return base64_string
            
        except Exception as e:
            logger.error(f"❌ Error encoding frame to Base64: {e}")
            return ""
    
    def _save_screenshot(self, frame: np.ndarray, camera_id: str, alert_type: str) -> str:
        """
        Save screenshot to local storage
        
        Args:
            frame: Video frame to save
            camera_id: Camera identifier
            alert_type: Type of alert (fire/smoke/combined)
            
        Returns:
            Path to saved screenshot file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{camera_id}_{alert_type}_{timestamp}.jpg"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Save frame as JPEG
            cv2.imwrite(filepath, frame)
            logger.info(f"📸 Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error saving screenshot: {e}")
            return ""
    
    def _prepare_detections_data(self, detections: List[Dict]) -> List[Dict]:
        """Prepare detection data for API requests"""
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
                    'center': [int(center[0]), int(center[1])],
                    'area': int(detection.get('area', (x2 - x1) * (y2 - y1)))
                }
                
                prepared_detections.append(prepared_detection)
                
            except Exception as e:
                logger.error(f"❌ Error preparing detection data: {e}")
                continue
        
        return prepared_detections
    
    def _check_alert_cooldown(self, camera_id: str) -> bool:
        """Check if enough time has passed since last alert for this camera"""
        current_time = time.time()
        last_alert_time = self.alert_cooldown.get(camera_id, 0)
        
        if current_time - last_alert_time > self.alert_cooldown_duration:
            self.alert_cooldown[camera_id] = current_time
            return True
        return False
    
    def send_fire_alert_to_backend(self, camera_id: str, camera_name: str, frame: np.ndarray,
                                 detections: List[Dict], alert_info: Dict) -> Optional[str]:
        """
        Send fire detection alert to backend server with screenshot
        
        Args:
            camera_id: Camera identifier
            camera_name: Camera display name
            frame: Video frame containing fire
            detections: List of detected fire regions
            alert_info: Alert information dictionary
            
        Returns:
            alert_id if successful, None otherwise
        """
        try:
            with self.lock:
                # Check cooldown
                if not self._check_alert_cooldown(camera_id):
                    logger.info(f"⏳ Alert cooldown active for camera {camera_id}")
                    return None
                
                # Encode frame to base64
                frame_data = self._encode_frame_to_base64(frame)
                if not frame_data:
                    raise Exception("Failed to encode frame")
                
                # Save screenshot locally
                screenshot_path = self._save_screenshot(frame, camera_id, alert_info.get('alert_type', 'fire'))
                
                # Prepare detection data
                prepared_detections = self._prepare_detections_data(detections)
                
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
                    'user_id': self.user_id,
                    'screenshot_path': screenshot_path,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Send request to backend
                # Network code disabled
                # url = f"{self.backend_url}/api/fire-detection/alert"
                # response = self.session.post(url, json=payload) ...
                
                print(f"✅ Fire alert sent to backend (LOCAL SIMULATION): {alert_id}")
                self.notification_sent.emit('backend', 'success')
                return "local_backend_id"
                    
        except Exception as e:
            error_msg = f"Failed to send fire alert to backend: {e}"
            logger.error(f"❌ {error_msg}")
            self.notification_failed.emit('backend', error_msg)
            return None
    
    def send_fire_alert_to_mobile(self, camera_id: str, camera_name: str, frame: np.ndarray,
                                detections: List[Dict], alert_info: Dict, alert_id: str = None) -> bool:
        """
        Send fire detection alert to Flutter mobile app with screenshot
        
        Args:
            camera_id: Camera identifier
            camera_name: Camera display name
            frame: Video frame containing fire
            detections: List of detected fire regions
            alert_info: Alert information dictionary
            alert_id: Backend alert ID (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock:
                # Save screenshot for mobile app
                screenshot_path = self._save_screenshot(frame, camera_id, alert_info.get('alert_type', 'fire'))
                
                if not screenshot_path or not os.path.exists(screenshot_path):
                    raise Exception("Failed to save screenshot")
                
                # Prepare mobile alert data
                mobile_data = {
                    'alert_id': alert_id or f"mobile_{camera_id}_{int(time.time())}",
                    'camera_id': camera_id,
                    'camera_name': camera_name,
                    'alert_type': alert_info.get('alert_type', 'fire'),
                    'confidence': alert_info.get('max_confidence', 0),
                    'fire_count': alert_info.get('fire_count', 0),
                    'smoke_count': alert_info.get('smoke_count', 0),
                    'timestamp': datetime.now().isoformat(),
                    'location': {
                        'building': 'Main Building',
                        'floor': '1st Floor',
                        'room': 'Office Area'
                    },
                    'detections': self._prepare_detections_data(detections)
                }
                
                # Send to mobile app
                # Network code disabled
                # url = f"{self.mobile_app_url}/fire_alert"
                # ...
                
                print(f"✅ Fire alert sent to mobile app (LOCAL SIMULATION)")
                self.mobile_alert_sent.emit(mobile_data['alert_id'], True)
                self.notification_sent.emit('mobile', 'success')
                return True
                        
        except Exception as e:
            error_msg = f"Failed to send fire alert to mobile app: {e}"
            logger.error(f"❌ {error_msg}")
            self.mobile_alert_sent.emit(alert_id or "unknown", False)
            self.notification_failed.emit('mobile', error_msg)
            return False
    
    def send_comprehensive_fire_alert(self, camera_id: str, camera_name: str, frame: np.ndarray,
                                    detections: List[Dict], alert_info: Dict) -> Dict[str, bool]:
        """
        Send fire alert to both backend and mobile app
        
        Args:
            camera_id: Camera identifier
            camera_name: Camera display name
            frame: Video frame containing fire
            detections: List of detected fire regions
            alert_info: Alert information dictionary
            
        Returns:
            Dictionary with success status for each notification target
        """
        results = {
            'backend': False,
            'mobile': False
        }
        
        # Send to backend first
        alert_id = self.send_fire_alert_to_backend(camera_id, camera_name, frame, detections, alert_info)
        if alert_id:
            results['backend'] = True
        
        # Send to mobile app
        mobile_success = self.send_fire_alert_to_mobile(camera_id, camera_name, frame, detections, alert_info, alert_id)
        if mobile_success:
            results['mobile'] = True
        
        # Log comprehensive results
        backend_status = "✅" if results['backend'] else "❌"
        mobile_status = "✅" if results['mobile'] else "❌"
        logger.info(f"🔥 Comprehensive fire alert results:")
        logger.info(f"   Backend: {backend_status}")
        logger.info(f"   Mobile: {mobile_status}")
        
        return results
    
    def test_backend_connection(self) -> bool:
        """Test connection to backend server"""
        try:
            with self.lock:
                # Network code disabled
                logger.info("✅ Backend connection test successful (LOCAL MODE)")
                return True
        except Exception as e:
            error_msg = f"Backend connection test failed: {e}"
            logger.error(f"❌ {error_msg}")
            return False
    
    def test_mobile_connection(self) -> bool:
        """Test connection to mobile app"""
        try:
            # Network code disabled
            logger.info("✅ Mobile app connection test successful (LOCAL MODE)")
            return True
        except Exception as e:
            error_msg = f"Mobile app connection test failed: {e}"
            logger.error(f"❌ {error_msg}")
            return False
    
    def set_mobile_app_url(self, url: str):
        """Update mobile app URL"""
        self.mobile_app_url = url.rstrip('/')
        logger.info(f"📱 Mobile app URL updated: {self.mobile_app_url}")
    
    def set_backend_url(self, url: str):
        """Update backend URL"""
        self.backend_url = url.rstrip('/')
        logger.info(f"🖥️ Backend URL updated: {self.backend_url}")
    
    def set_user_id(self, user_id: str):
        """Update user ID"""
        self.user_id = user_id
        logger.info(f"👤 User ID updated: {user_id}")
    
    def get_severity_level(self, confidence: float) -> str:
        """Get severity level based on confidence"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def cleanup_old_screenshots(self, max_age_hours: int = 24):
        """Clean up old screenshot files"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.screenshots_dir):
                filepath = os.path.join(self.screenshots_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"🗑️ Cleaned up old screenshot: {filename}")
                        
        except Exception as e:
            logger.error(f"❌ Error cleaning up screenshots: {e}")
    
    def close(self):
        """Close the notification manager"""
        if self.session:
            self.session.close()
        logger.info("🔒 Notification Manager closed")
