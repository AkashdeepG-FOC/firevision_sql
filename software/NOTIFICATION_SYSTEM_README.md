# FireVision Notification System

## Overview

The FireVision Notification System is an enhanced fire detection alert system that integrates with both backend servers and Flutter mobile applications. It provides real-time fire detection notifications with screenshot capture, Base64 encoding, and comprehensive alert management.

## Features

### 🔥 Fire Detection Integration
- Real-time fire and smoke detection
- Automatic screenshot capture when fire is detected
- Base64 encoding for efficient data transmission
- Multiple detection confidence levels
- Alert cooldown management to prevent spam

### 📱 Mobile App Integration
- Direct communication with Flutter mobile applications
- HTTP POST requests with image files and metadata
- Configurable mobile app endpoints
- Connection testing and health checks
- Automatic retry mechanisms

### 🖥️ Backend Server Integration
- RESTful API communication
- Fire detection alert storage
- Alert status management (pending, dispatched, false_alarm, resolved)
- Emergency services dispatch functionality
- Comprehensive alert metadata

### 📸 Screenshot Management
- Automatic screenshot capture on fire detection
- Local storage with timestamped filenames
- Configurable image quality settings
- Automatic cleanup of old screenshots
- Support for multiple image formats

## Installation

### Prerequisites
- Python 3.7+
- OpenCV (cv2)
- PyQt5
- requests
- numpy

### Dependencies
```bash
pip install opencv-python PyQt5 requests numpy
```

## Configuration

### Mobile App Settings
Edit `config/mobile_settings.json`:

```json
{
  "mobile_settings": {
    "app_url": "http://192.168.1.4:58766",
    "timeout": 5,
    "retry_attempts": 3,
    "notification_enabled": true,
    "screenshot_quality": 85,
    "alert_cooldown_seconds": 5
  }
}
```

### Backend Server Settings
Configure your backend server URL in the main application configuration.

## Usage

### Basic Integration

```python
from notification_manager import NotificationManager

# Initialize notification manager
notification_manager = NotificationManager(
    backend_url="http://localhost:5000",
    mobile_app_url="http://192.168.1.4:58766",
    user_id="system"
)

# Send comprehensive fire alert
results = notification_manager.send_comprehensive_fire_alert(
    camera_id="camera_001",
    camera_name="Main Camera",
    frame=fire_detected_frame,
    detections=detection_data,
    alert_info=alert_information
)
```

### Individual Notifications

```python
# Send to backend only
alert_id = notification_manager.send_fire_alert_to_backend(
    camera_id="camera_001",
    camera_name="Main Camera",
    frame=frame,
    detections=detections,
    alert_info=alert_info
)

# Send to mobile app only
success = notification_manager.send_fire_alert_to_mobile(
    camera_id="camera_001",
    camera_name="Main Camera",
    frame=frame,
    detections=detections,
    alert_info=alert_info,
    alert_id=alert_id
)
```

### Connection Testing

```python
# Test backend connection
backend_ok = notification_manager.test_backend_connection()

# Test mobile app connection
mobile_ok = notification_manager.test_mobile_connection()

# Test all connections
notification_manager.test_all_connections()
```

## API Endpoints

### Backend Server Endpoints

#### Create Fire Alert
```
POST /api/fire-detection/alert
Content-Type: application/json

{
  "camera_id": "camera_001",
  "camera_name": "Main Camera",
  "detection_type": "fire",
  "confidence": 0.85,
  "frame_data": "base64_encoded_image",
  "detections": [...],
  "alert_info": {...},
  "user_id": "system"
}
```

#### Dispatch Emergency Services
```
PUT /api/fire-detection/alerts/{alert_id}/dispatch
Content-Type: application/json

{
  "dispatched_by": "user",
  "dispatch_notes": "Emergency services dispatched"
}
```

#### Mark False Alarm
```
PUT /api/fire-detection/alerts/{alert_id}/false-alarm
Content-Type: application/json

{
  "resolved_by": "user",
  "resolution_notes": "Marked as false alarm"
}
```

### Flutter Mobile App Endpoints

#### Fire Alert Notification
```
POST /fire_alert
Content-Type: multipart/form-data

Files:
- screenshot: image_file.jpg

Data:
- alert_data: JSON string with alert information
```

#### Health Check
```
GET /health
Response: {"status": "OK"}
```

## Data Structures

### Detection Data
```python
detection = {
    'bbox': [x1, y1, x2, y2],  # Bounding box coordinates
    'confidence': 0.85,         # Detection confidence (0-1)
    'type': 'fire',            # Detection type ('fire' or 'smoke')
    'center': [center_x, center_y],  # Center coordinates
    'area': 10000              # Detection area in pixels
}
```

### Alert Information
```python
alert_info = {
    'fire_count': 2,           # Number of fire detections
    'smoke_count': 0,          # Number of smoke detections
    'max_confidence': 0.85,    # Highest confidence score
    'alert_type': 'fire',      # Primary alert type
    'severity': 'high'         # Severity level
}
```

### Mobile Alert Data
```python
mobile_data = {
    'alert_id': 'unique_alert_id',
    'camera_id': 'camera_001',
    'camera_name': 'Main Camera',
    'alert_type': 'fire',
    'confidence': 0.85,
    'fire_count': 2,
    'smoke_count': 0,
    'timestamp': '2024-01-01T12:00:00',
    'location': {
        'building': 'Main Building',
        'floor': '1st Floor',
        'room': 'Office Area'
    },
    'detections': [...]
}
```

## Testing

### Run Test Script
```bash
python test_notification_system.py
```

The test script will:
1. Initialize the notification manager
2. Test backend and mobile app connections
3. Create simulated fire detection data
4. Send comprehensive alerts
5. Test individual notification methods
6. Verify screenshot functionality
7. Test Base64 encoding
8. Clean up test files

### Test with Real Camera
The test script includes an option to test with a real camera if available.

## Integration with FireVision Pro

### Main Application Integration
The notification system is automatically integrated into the main FireVision Pro application:

1. **Initialization**: The notification manager is initialized in the main window
2. **Fire Detection**: Automatically triggered when fire is detected
3. **Fullscreen Mode**: Enhanced fire detection side panel with notification controls
4. **Emergency Dispatch**: Integrated with emergency services dispatch functionality

### Configuration Integration
- Mobile app URL configurable through the main application settings
- Backend server URL integration with existing configuration system
- User ID management through the authentication system

## Error Handling

### Connection Failures
- Automatic retry mechanisms for failed connections
- Graceful degradation when services are unavailable
- Comprehensive error logging and reporting

### Data Validation
- Input validation for all API requests
- Frame validation before encoding
- Detection data validation and sanitization

### Network Issues
- Timeout handling for network requests
- Connection pooling for better performance
- Automatic reconnection attempts

## Performance Considerations

### Screenshot Management
- Configurable image quality settings
- Automatic cleanup of old screenshots
- Efficient Base64 encoding

### Network Optimization
- Connection pooling and session management
- Request timeout configuration
- Retry mechanisms with exponential backoff

### Memory Management
- Efficient frame processing
- Automatic cleanup of temporary data
- Memory-conscious image encoding

## Security Considerations

### Data Transmission
- HTTPS support for secure communication
- Input validation and sanitization
- User authentication and authorization

### File Management
- Secure screenshot storage
- Automatic cleanup of sensitive data
- Access control for stored files

## Troubleshooting

### Common Issues

#### Connection Failures
- Verify backend server is running
- Check mobile app URL and port
- Ensure network connectivity
- Review firewall settings

#### Screenshot Issues
- Check disk space availability
- Verify write permissions
- Review image format support
- Check OpenCV installation

#### Mobile App Integration
- Verify Flutter app is running
- Check endpoint URLs
- Review mobile app logs
- Test with curl or Postman

### Debug Mode
Enable debug logging by setting the logging level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies
3. Configure mobile app settings
4. Run test script
5. Test with real camera

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters
- Include comprehensive docstrings
- Add unit tests for new features

## License

This notification system is part of the FireVision Pro project and follows the same licensing terms.

## Support

For support and questions:
1. Check the troubleshooting section
2. Review the test script output
3. Check application logs
4. Contact the development team

---

**Note**: This notification system requires both the backend server and Flutter mobile app to be running for full functionality. The system will gracefully handle cases where either service is unavailable.
