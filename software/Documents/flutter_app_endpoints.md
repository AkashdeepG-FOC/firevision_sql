# Flutter App Endpoints Specification

## Overview

This document specifies the HTTP endpoints that need to be implemented in your Flutter mobile application to receive fire detection notifications from the FireVision Pro system.

## Required Endpoints

### 1. Fire Alert Notification Endpoint

**Endpoint**: `POST /fire_alert`

**Purpose**: Receive fire detection alerts with screenshots and metadata

**Request Format**: `multipart/form-data`

**Parameters**:
- `screenshot` (file): Image file (JPEG/PNG) containing the fire detection screenshot
- `alert_data` (string): JSON string containing alert metadata

**Alert Data Structure**:
```json
{
  "alert_id": "unique_alert_id",
  "camera_id": "camera_001",
  "camera_name": "Main Camera",
  "alert_type": "fire",
  "confidence": 0.85,
  "fire_count": 2,
  "smoke_count": 0,
  "timestamp": "2024-01-01T12:00:00",
  "location": {
    "building": "Main Building",
    "floor": "1st Floor",
    "room": "Office Area"
  },
  "detections": [
    {
      "bbox": [200, 150, 300, 250],
      "confidence": 0.85,
      "type": "fire",
      "center": [250, 200],
      "area": 10000
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Alert received successfully",
  "alert_id": "unique_alert_id"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### 2. Health Check Endpoint

**Endpoint**: `GET /health`

**Purpose**: Verify that the Flutter app is running and accessible

**Response**:
```json
{
  "status": "OK",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### 3. Test Endpoint (Optional)

**Endpoint**: `GET /test`

**Purpose**: Test endpoint for debugging and verification

**Response**:
```json
{
  "message": "Flutter app is running",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Implementation Guidelines

### Flutter HTTP Server Setup

```dart
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

class FireAlertServer {
  late HttpServer _server;
  int port = 58766;
  
  Future<void> start() async {
    _server = await HttpServer.bind(InternetAddress.anyIPv4, port);
    print('Fire alert server started on port $port');
    
    await for (HttpRequest request in _server) {
      _handleRequest(request);
    }
  }
  
  void _handleRequest(HttpRequest request) {
    switch (request.method) {
      case 'GET':
        _handleGet(request);
        break;
      case 'POST':
        _handlePost(request);
        break;
      default:
        _sendResponse(request, 405, {'error': 'Method not allowed'});
    }
  }
  
  void _handleGet(HttpRequest request) {
    String path = request.uri.path;
    
    switch (path) {
      case '/health':
        _handleHealthCheck(request);
        break;
      case '/test':
        _handleTest(request);
        break;
      default:
        _sendResponse(request, 404, {'error': 'Not found'});
    }
  }
  
  void _handlePost(HttpRequest request) {
    String path = request.uri.path;
    
    switch (path) {
      case '/fire_alert':
        _handleFireAlert(request);
        break;
      default:
        _sendResponse(request, 404, {'error': 'Not found'});
    }
  }
  
  void _handleHealthCheck(HttpRequest request) {
    Map<String, dynamic> response = {
      'status': 'OK',
      'timestamp': DateTime.now().toIso8601String(),
      'version': '1.0.0'
    };
    _sendResponse(request, 200, response);
  }
  
  void _handleTest(HttpRequest request) {
    Map<String, dynamic> response = {
      'message': 'Flutter app is running',
      'timestamp': DateTime.now().toIso8601String()
    };
    _sendResponse(request, 200, response);
  }
  
  void _handleFireAlert(HttpRequest request) async {
    try {
      // Parse multipart form data
      var boundary = request.headers.contentType?.parameters['boundary'];
      var transformer = MimeMultipartTransformer(boundary!);
      var bodyStream = request.cast<List<int>>();
      var parts = await transformer.bind(bodyStream).toList();
      
      String? alertDataJson;
      List<int>? screenshotData;
      
      for (var part in parts) {
        var header = part.headers;
        var contentDisposition = header['content-disposition'];
        
        if (contentDisposition != null) {
          if (contentDisposition.contains('name="alert_data"')) {
            alertDataJson = utf8.decode(part);
          } else if (contentDisposition.contains('name="screenshot"')) {
            screenshotData = part;
          }
        }
      }
      
      if (alertDataJson == null || screenshotData == null) {
        _sendResponse(request, 400, {'error': 'Missing required data'});
        return;
      }
      
      // Parse alert data
      Map<String, dynamic> alertData = json.decode(alertDataJson);
      
      // Process the fire alert
      await _processFireAlert(alertData, screenshotData);
      
      // Send success response
      Map<String, dynamic> response = {
        'success': true,
        'message': 'Alert received successfully',
        'alert_id': alertData['alert_id']
      };
      _sendResponse(request, 200, response);
      
    } catch (e) {
      print('Error handling fire alert: $e');
      _sendResponse(request, 500, {'error': 'Internal server error'});
    }
  }
  
  Future<void> _processFireAlert(Map<String, dynamic> alertData, List<int> screenshotData) async {
    // Save screenshot
    String filename = 'fire_alert_${alertData['alert_id']}.jpg';
    File file = File(filename);
    await file.writeAsBytes(screenshotData);
    
    // Process alert data
    print('Fire Alert Received:');
    print('Alert ID: ${alertData['alert_id']}');
    print('Camera: ${alertData['camera_name']} (${alertData['camera_id']})');
    print('Type: ${alertData['alert_type']}');
    print('Confidence: ${alertData['confidence']}');
    print('Fire Count: ${alertData['fire_count']}');
    print('Smoke Count: ${alertData['smoke_count']}');
    print('Timestamp: ${alertData['timestamp']}');
    print('Screenshot saved: $filename');
    
    // Show notification to user
    await _showFireAlertNotification(alertData);
    
    // You can add more processing here:
    // - Save to local database
    // - Send push notification
    // - Update UI
    // - Log to analytics
  }
  
  Future<void> _showFireAlertNotification(Map<String, dynamic> alertData) async {
    // Implement your notification logic here
    // This could be:
    // - Local notification
    // - In-app notification
    // - Sound/vibration
    // - UI update
    
    print('Showing fire alert notification to user');
  }
  
  void _sendResponse(HttpRequest request, int statusCode, Map<String, dynamic> data) {
    request.response.statusCode = statusCode;
    request.response.headers.contentType = ContentType.json;
    request.response.write(json.encode(data));
    request.response.close();
  }
  
  void stop() {
    _server.close();
  }
}
```

### Usage in Flutter App

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Start the fire alert server
  FireAlertServer server = FireAlertServer();
  await server.start();
  
  runApp(MyApp());
}
```

## Configuration

### Network Configuration

1. **Port**: Default port is 58766, but can be configured
2. **IP Address**: Bind to `InternetAddress.anyIPv4` to accept connections from any IP
3. **Firewall**: Ensure the port is open in your firewall settings

### Security Considerations

1. **Authentication**: Consider adding API key authentication for production use
2. **HTTPS**: Use HTTPS in production environments
3. **Input Validation**: Validate all incoming data
4. **Rate Limiting**: Implement rate limiting to prevent abuse

## Testing

### Test with curl

```bash
# Test health endpoint
curl http://192.168.1.4:58766/health

# Test fire alert endpoint
curl -X POST http://192.168.1.4:58766/fire_alert \
  -F "screenshot=@test_image.jpg" \
  -F 'alert_data={"alert_id":"test123","camera_id":"cam001","camera_name":"Test Camera","alert_type":"fire","confidence":0.85,"fire_count":1,"smoke_count":0,"timestamp":"2024-01-01T12:00:00","location":{"building":"Test Building","floor":"1st Floor","room":"Test Room"},"detections":[{"bbox":[100,100,200,200],"confidence":0.85,"type":"fire","center":[150,150],"area":10000}]}'
```

### Test with Python

```python
import requests
import json

# Test health endpoint
response = requests.get('http://192.168.1.4:58766/health')
print(response.json())

# Test fire alert endpoint
alert_data = {
    "alert_id": "test123",
    "camera_id": "cam001",
    "camera_name": "Test Camera",
    "alert_type": "fire",
    "confidence": 0.85,
    "fire_count": 1,
    "smoke_count": 0,
    "timestamp": "2024-01-01T12:00:00",
    "location": {
        "building": "Test Building",
        "floor": "1st Floor",
        "room": "Test Room"
    },
    "detections": [{
        "bbox": [100, 100, 200, 200],
        "confidence": 0.85,
        "type": "fire",
        "center": [150, 150],
        "area": 10000
    }]
}

with open('test_image.jpg', 'rb') as f:
    files = {'screenshot': f}
    data = {'alert_data': json.dumps(alert_data)}
    response = requests.post('http://192.168.1.4:58766/fire_alert', files=files, data=data)
    print(response.json())
```

## Integration Notes

1. **Network Discovery**: The FireVision Pro system will attempt to connect to the configured mobile app URL
2. **Error Handling**: Implement proper error handling for network issues
3. **Background Processing**: Consider running the server in the background
4. **Battery Optimization**: Be mindful of battery usage when running HTTP servers
5. **Platform Differences**: Test on both iOS and Android platforms

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the Flutter app is running and the port is correct
2. **Firewall Issues**: Ensure the port is open in firewall settings
3. **Network Issues**: Verify both devices are on the same network
4. **CORS Issues**: Not applicable for HTTP servers, but consider for web-based implementations

### Debug Tips

1. Enable debug logging in your Flutter app
2. Use network monitoring tools to check connections
3. Test with curl or Postman first
4. Check device logs for errors
