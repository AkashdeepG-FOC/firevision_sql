# 🔥 FireVision Pro - Technical Implementation Guide

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation & Setup](#installation--setup)
3. [YOLO Model Training](#yolo-model-training)
4. [IoT Device Configuration](#iot-device-configuration)
5. [API Endpoints](#api-endpoints)
6. [Configuration Files](#configuration-files)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 10.15+
- **CPU**: Intel i5-8th gen or AMD Ryzen 5 2600+
- **RAM**: 8GB DDR4
- **Storage**: 50GB SSD
- **GPU**: NVIDIA GTX 1060 6GB or equivalent (optional)
- **Network**: 100 Mbps Ethernet or WiFi 5

### Recommended Requirements
- **OS**: Windows 11, Ubuntu 22.04+, macOS 12+
- **CPU**: Intel i7-10th gen or AMD Ryzen 7 3700X+
- **RAM**: 16GB DDR4
- **Storage**: 100GB NVMe SSD
- **GPU**: NVIDIA RTX 3060 12GB or equivalent
- **Network**: 1 Gbps Ethernet or WiFi 6

---

## 🚀 Installation & Setup

### 1. Python Environment Setup

```bash
# Create virtual environment
python -m venv firevision_env
source firevision_env/bin/activate  # Linux/macOS
firevision_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Core Dependencies Installation

```bash
# AI and Computer Vision
pip install ultralytics torch torchvision opencv-python

# GUI Framework
pip install PyQt5 PyQtWebEngine

# IoT and Communication
pip install paho-mqtt requests websockets

# Voice Commands
pip install SpeechRecognition pyttsx3 pyaudio openai-whisper

# Data Processing
pip install numpy pandas openpyxl

# Cloud Integration
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. System Configuration

```python
# config/app_config.json
{
  "system": {
    "name": "FireVision Pro",
    "version": "2.0.0",
    "debug_mode": false,
    "log_level": "INFO"
  },
  "cameras": {
    "max_cameras": 16,
    "default_fps": 30,
    "recording_quality": "HD",
    "storage_path": "./recordings"
  },
  "ai_detection": {
    "model_path": "./models/best_m.pt",
    "confidence_threshold": 0.5,
    "detection_interval": 2,
    "enable_night_mode": true
  },
  "iot": {
    "esp32_base_url": "http://192.168.1.54/",
    "sensor_update_interval": 1000,
    "auto_control_enabled": true,
    "emergency_thresholds": {
      "temperature": 60,
      "gas_level": 500,
      "flame_detected": true
    }
  }
}
```

---

## 🎯 YOLO Model Training

### 1. Dataset Preparation

```python
# data_preparation.py
import os
import cv2
from ultralytics import YOLO

def prepare_dataset():
    """Prepare dataset for YOLO training"""
    
    # Dataset structure
    dataset_path = "./dataset"
    train_path = f"{dataset_path}/train"
    val_path = f"{dataset_path}/val"
    
    # Create directories
    os.makedirs(f"{train_path}/images", exist_ok=True)
    os.makedirs(f"{train_path}/labels", exist_ok=True)
    os.makedirs(f"{val_path}/images", exist_ok=True)
    os.makedirs(f"{val_path}/labels", exist_ok=True)
    
    # Data augmentation
    augment_config = {
        'hsv_h': 0.015,  # HSV-Hue augmentation
        'hsv_s': 0.7,    # HSV-Saturation augmentation
        'hsv_v': 0.4,    # HSV-Value augmentation
        'degrees': 0.0,   # Image rotation
        'translate': 0.1, # Image translation
        'scale': 0.5,    # Image scaling
        'shear': 0.0,    # Image shear
        'perspective': 0.0, # Image perspective
        'flipud': 0.0,   # Flip up-down
        'fliplr': 0.5,   # Flip left-right
        'mosaic': 1.0,   # Mosaic augmentation
        'mixup': 0.0     # Mixup augmentation
    }
    
    return dataset_path, augment_config
```

### 2. Training Configuration

```yaml
# models/train_config.yaml
# YOLOv8 training configuration

# Model parameters
model: yolov8n.pt  # or yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
epochs: 100
patience: 50
batch: 16
imgsz: 640

# Data parameters
data: dataset.yaml
cache: false

# Training parameters
lr0: 0.01
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3.0
warmup_momentum: 0.8
warmup_bias_lr: 0.1

# Augmentation parameters
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 0.0
translate: 0.1
scale: 0.5
shear: 0.0
perspective: 0.0
flipud: 0.0
fliplr: 0.5
mosaic: 1.0
mixup: 0.0

# Save parameters
save: true
save_period: -1
project: runs/train
name: fire_detection
```

### 3. Training Script

```python
# train_model.py
from ultralytics import YOLO
import os

def train_fire_detection_model():
    """Train YOLO model for fire detection"""
    
    # Load base model
    model = YOLO('yolov8n.pt')
    
    # Training parameters
    training_args = {
        'data': 'dataset.yaml',
        'epochs': 100,
        'imgsz': 640,
        'batch': 16,
        'device': '0',  # GPU device
        'workers': 8,
        'patience': 50,
        'save': True,
        'save_period': 10,
        'cache': False,
        'project': 'runs/train',
        'name': 'fire_detection_v2',
        'exist_ok': True
    }
    
    # Start training
    results = model.train(**training_args)
    
    # Validate model
    metrics = model.val()
    
    # Export model
    model.export(format='onnx', dynamic=True)
    model.export(format='torchscript')
    
    return results, metrics

if __name__ == "__main__":
    results, metrics = train_fire_detection_model()
    print(f"Training completed. mAP50: {metrics.box.map50:.3f}")
```

---

## 🔌 IoT Device Configuration

### 1. ESP32 Arduino Code

```cpp
// esp32_fire_detection.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// Pin definitions
#define FLAME_SENSOR_PIN 2
#define GAS_SENSOR_PIN 34
#define DHT_PIN 4
#define SPRINKLER_PIN 26
#define EXHAUST_FAN_PIN 27
#define ALARM_PIN 25

// WiFi credentials
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";

// Server configuration
const char* serverUrl = "http://192.168.1.100:5000";
const char* endpoint = "/data";

// Sensor objects
DHT dht(DHT_PIN, DHT22);

// Control variables
bool sprinklerActive = false;
bool exhaustFanActive = false;
bool alarmActive = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(FLAME_SENSOR_PIN, INPUT);
  pinMode(GAS_SENSOR_PIN, INPUT);
  pinMode(SPRINKLER_PIN, OUTPUT);
  pinMode(EXHAUST_FAN_PIN, OUTPUT);
  pinMode(ALARM_PIN, OUTPUT);
  
  // Initialize sensors
  dht.begin();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("WiFi connected");
}

void loop() {
  // Read sensor data
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int gasLevel = analogRead(GAS_SENSOR_PIN);
  bool flameDetected = digitalRead(FLAME_SENSOR_PIN) == LOW;
  
  // Convert gas level to PPM (calibrate based on your sensor)
  int gasPPM = map(gasLevel, 0, 4095, 0, 1000);
  
  // Check emergency conditions
  bool emergency = false;
  if (temperature > 60 || gasPPM > 500 || flameDetected) {
    emergency = true;
    activateEmergencySystems();
  }
  
  // Send data to server
  sendSensorData(temperature, humidity, gasPPM, flameDetected);
  
  // Check for server commands
  checkServerCommands();
  
  delay(1000); // Update every second
}

void activateEmergencySystems() {
  // Activate sprinklers
  digitalWrite(SPRINKLER_PIN, HIGH);
  sprinklerActive = true;
  
  // Activate exhaust fan
  digitalWrite(EXHAUST_FAN_PIN, HIGH);
  exhaustFanActive = true;
  
  // Activate alarm
  digitalWrite(ALARM_PIN, HIGH);
  alarmActive = true;
  
  Serial.println("EMERGENCY: All systems activated!");
}

void sendSensorData(float temp, float hum, int gas, bool flame) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl + String(endpoint));
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    StaticJsonDocument<200> doc;
    doc["temperature"] = temp;
    doc["humidity"] = hum;
    doc["gas_level"] = gas;
    doc["flame_detected"] = flame ? "yes" : "no";
    doc["timestamp"] = millis();
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Send POST request
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
      Serial.println("Data sent successfully");
    } else {
      Serial.println("Error sending data");
    }
    
    http.end();
  }
}

void checkServerCommands() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl + "/control");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      String payload = http.getStream().readString();
      
      // Parse JSON response
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, payload);
      
      if (!error) {
        if (doc.containsKey("sprinkler")) {
          bool command = doc["sprinkler"];
          digitalWrite(SPRINKLER_PIN, command ? HIGH : LOW);
          sprinklerActive = command;
        }
        
        if (doc.containsKey("exhaust_fan")) {
          bool command = doc["exhaust_fan"];
          digitalWrite(EXHAUST_FAN_PIN, command ? HIGH : LOW);
          exhaustFanActive = command;
        }
        
        if (doc.containsKey("alarm")) {
          bool command = doc["alarm"];
          digitalWrite(ALARM_PIN, command ? HIGH : LOW);
          alarmActive = command;
        }
      }
    }
    
    http.end();
  }
}
```

### 2. Backend Server Configuration

```javascript
// backend_server/server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/firevision', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// Sensor data schema
const sensorDataSchema = new mongoose.Schema({
  temperature: Number,
  humidity: Number,
  gas_level: Number,
  flame_detected: String,
  timestamp: { type: Date, default: Date.now }
});

const SensorData = mongoose.model('SensorData', sensorDataSchema);

// Routes
app.post('/data', async (req, res) => {
  try {
    const sensorData = new SensorData(req.body);
    await sensorData.save();
    res.status(200).json({ message: 'Data saved successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/data', async (req, res) => {
  try {
    const data = await SensorData.find()
      .sort({ timestamp: -1 })
      .limit(20);
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/control', async (req, res) => {
  try {
    const { device, action } = req.body;
    
    // Send command to ESP32
    const response = await fetch(`http://192.168.1.54/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device, action })
    });
    
    res.json({ message: 'Command sent successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

---

## 🌐 API Endpoints

### 1. Core API Endpoints

```python
# api_endpoints.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Camera Management
@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    return jsonify({
        'cameras': camera_manager.get_all_cameras(),
        'status': 'success'
    })

@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """Add new camera"""
    data = request.json
    camera_id = camera_manager.add_camera(
        name=data['name'],
        source=data['source'],
        camera_type=data['type']
    )
    return jsonify({
        'camera_id': camera_id,
        'status': 'success'
    })

# Detection Results
@app.route('/api/detections', methods=['GET'])
def get_detections():
    """Get recent detections"""
    camera_id = request.args.get('camera_id')
    limit = request.args.get('limit', 50)
    
    detections = detection_manager.get_recent_detections(
        camera_id=camera_id,
        limit=int(limit)
    )
    
    return jsonify({
        'detections': detections,
        'status': 'success'
    })

# IoT Control
@app.route('/api/iot/control', methods=['POST'])
def control_iot_device():
    """Control IoT devices"""
    data = request.json
    device = data['device']
    action = data['action']
    
    result = iot_manager.execute_command(device, action)
    
    return jsonify({
        'result': result,
        'status': 'success'
    })

# System Status
@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get system status"""
    status = {
        'cameras': camera_manager.get_status(),
        'detection': detection_manager.get_status(),
        'iot': iot_manager.get_status(),
        'storage': storage_manager.get_status(),
        'system': system_manager.get_status()
    }
    
    return jsonify(status)

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## ⚙️ Configuration Files

### 1. Main Configuration

```python
# config_manager.py
import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    def __init__(self, config_file: str = "config/app_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.get_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def update_config(self, key: str, value: Any) -> None:
        """Update configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "system": {
                "name": "FireVision Pro",
                "version": "2.0.0",
                "debug_mode": False,
                "log_level": "INFO"
            },
            "cameras": {
                "max_cameras": 16,
                "default_fps": 30,
                "recording_quality": "HD",
                "storage_path": "./recordings"
            },
            "ai_detection": {
                "model_path": "./models/best_m.pt",
                "confidence_threshold": 0.5,
                "detection_interval": 2,
                "enable_night_mode": True
            },
            "iot": {
                "esp32_base_url": "http://192.168.1.54/",
                "sensor_update_interval": 1000,
                "auto_control_enabled": True,
                "emergency_thresholds": {
                    "temperature": 60,
                    "gas_level": 500,
                    "flame_detected": True
                }
            }
        }
```

---

## 🚀 Performance Optimization

### 1. Detection Optimization

```python
# detection_optimization.py
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import queue
import time

class OptimizedDetectionEngine:
    def __init__(self, model_path: str, max_workers: int = 4):
        self.model = YOLO(model_path)
        self.max_workers = max_workers
        self.detection_queue = queue.Queue(maxsize=10)
        self.result_queue = queue.Queue()
        self.workers = []
        self.start_workers()
    
    def start_workers(self):
        """Start worker threads for parallel processing"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        """Worker thread loop for processing detections"""
        while True:
            try:
                frame_data = self.detection_queue.get(timeout=1)
                if frame_data is None:
                    break
                
                camera_id, frame, timestamp = frame_data
                results = self.process_frame(frame)
                
                self.result_queue.put({
                    'camera_id': camera_id,
                    'results': results,
                    'timestamp': timestamp
                })
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def process_frame(self, frame: np.ndarray) -> list:
        """Process single frame with optimization"""
        # Resize frame for faster processing
        height, width = frame.shape[:2]
        if width > 640:
            scale = 640 / width
            new_width = 640
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Run detection
        results = self.model(frame, verbose=False)
        
        # Process results
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    detection = {
                        'bbox': box.xyxy[0].cpu().numpy().tolist(),
                        'confidence': float(box.conf[0]),
                        'class_id': int(box.cls[0]),
                        'class_name': result.names[int(box.cls[0])]
                    }
                    detections.append(detection)
        
        return detections
    
    def add_frame(self, camera_id: str, frame: np.ndarray):
        """Add frame to detection queue"""
        try:
            self.detection_queue.put_nowait((camera_id, frame, time.time()))
        except queue.Full:
            # Skip frame if queue is full
            pass
    
    def get_results(self) -> list:
        """Get all available detection results"""
        results = []
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        return results
```

### 2. Memory Management

```python
# memory_manager.py
import psutil
import gc
import threading
import time
from typing import Dict, List

class MemoryManager:
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Memory monitoring loop"""
        while self.monitoring:
            memory_percent = psutil.virtual_memory().percent
            
            if memory_percent > self.max_memory_percent:
                self.cleanup_memory()
            
            time.sleep(30)  # Check every 30 seconds
    
    def cleanup_memory(self):
        """Clean up memory when usage is high"""
        print(f"High memory usage detected: {psutil.virtual_memory().percent}%")
        
        # Force garbage collection
        gc.collect()
        
        # Clear caches if available
        if hasattr(cv2, 'destroyAllWindows'):
            cv2.destroyAllWindows()
        
        print("Memory cleanup completed")
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get current memory information"""
        memory = psutil.virtual_memory()
        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent': memory.percent
        }
    
    def optimize_for_detection(self, frame_count: int):
        """Optimize memory for detection processing"""
        if frame_count > 100:
            # Clear old frames from memory
            gc.collect()
            
            # Reduce frame buffer size
            if hasattr(self, 'frame_buffer'):
                self.frame_buffer.clear()
```

---

## 🔧 Troubleshooting

### 1. Common Issues & Solutions

```python
# troubleshooting.py
import logging
import traceback
from typing import Dict, Any

class TroubleshootingGuide:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.solutions = self.load_solutions()
    
    def load_solutions(self) -> Dict[str, Dict[str, Any]]:
        """Load troubleshooting solutions"""
        return {
            "camera_connection_failed": {
                "description": "Camera connection failed",
                "causes": [
                    "Invalid camera URL or IP address",
                    "Network connectivity issues",
                    "Camera credentials incorrect",
                    "Camera offline or powered off"
                ],
                "solutions": [
                    "Verify camera IP address and port",
                    "Check network connectivity",
                    "Verify username and password",
                    "Power cycle the camera",
                    "Check camera firmware version"
                ]
            },
            "detection_not_working": {
                "description": "AI detection not working",
                "causes": [
                    "Model file not found",
                    "Insufficient GPU memory",
                    "Model loading failed",
                    "Input frame format incorrect"
                ],
                "solutions": [
                    "Verify model file path",
                    "Check GPU memory usage",
                    "Reinstall model dependencies",
                    "Verify input frame format",
                    "Check model compatibility"
                ]
            },
            "iot_devices_offline": {
                "description": "IoT devices not responding",
                "causes": [
                    "ESP32 not connected to WiFi",
                    "Incorrect IP address",
                    "Network firewall blocking",
                    "ESP32 code error"
                ],
                "solutions": [
                    "Check ESP32 WiFi connection",
                    "Verify IP address in config",
                    "Check network firewall settings",
                    "Upload updated ESP32 code",
                    "Check serial monitor for errors"
                ]
            },
            "high_cpu_usage": {
                "description": "High CPU usage",
                "causes": [
                    "Too many cameras active",
                    "Detection processing overload",
                    "Memory leaks",
                    "Background processes"
                ],
                "solutions": [
                    "Reduce number of active cameras",
                    "Increase detection interval",
                    "Restart application",
                    "Check for memory leaks",
                    "Optimize detection settings"
                ]
            }
        }
    
    def diagnose_issue(self, issue_type: str, error_details: str = "") -> Dict[str, Any]:
        """Diagnose specific issue"""
        if issue_type not in self.solutions:
            return {"error": "Unknown issue type"}
        
        solution = self.solutions[issue_type].copy()
        solution["error_details"] = error_details
        solution["timestamp"] = time.time()
        
        # Log the issue
        self.logger.warning(f"Issue diagnosed: {issue_type}")
        if error_details:
            self.logger.error(f"Error details: {error_details}")
        
        return solution
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        import psutil
        
        health = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_status": self.check_network_status(),
            "camera_status": self.check_camera_status(),
            "detection_status": self.check_detection_status(),
            "iot_status": self.check_iot_status()
        }
        
        # Determine overall health
        if (health["cpu_usage"] > 90 or 
            health["memory_usage"] > 90 or 
            health["disk_usage"] > 90):
            health["overall_status"] = "CRITICAL"
        elif (health["cpu_usage"] > 70 or 
              health["memory_usage"] > 70 or 
              health["disk_usage"] > 70):
            health["overall_status"] = "WARNING"
        else:
            health["overall_status"] = "HEALTHY"
        
        return health
    
    def check_network_status(self) -> str:
        """Check network connectivity"""
        try:
            import requests
            response = requests.get("http://www.google.com", timeout=5)
            return "ONLINE" if response.status_code == 200 else "OFFLINE"
        except:
            return "OFFLINE"
    
    def check_camera_status(self) -> str:
        """Check camera system status"""
        # Implementation depends on camera manager
        return "UNKNOWN"
    
    def check_detection_status(self) -> str:
        """Check AI detection system status"""
        # Implementation depends on detection manager
        return "UNKNOWN"
    
    def check_iot_status(self) -> str:
        """Check IoT system status"""
        # Implementation depends on IoT manager
        return "UNKNOWN"
```

This technical implementation guide provides the essential technical details, code examples, and configuration needed to implement and deploy the FireVision Pro system. The guide covers all major components from YOLO model training to IoT device configuration and system optimization.

