#!/usr/bin/env python3
"""
Script to simulate ESP32 sensor data being sent to backend
This helps test the complete sensor data flow
"""

import requests
import time
import random
import json
from datetime import datetime

def simulate_sensor_data():
    """Simulate ESP32 sending sensor data to backend"""
    backend_url = "http://localhost:5000"
    
    print("🤖 ESP32 Sensor Data Simulator")
    print("=" * 50)
    print("📡 Sending simulated sensor data to backend...")
    print(f"🌐 Backend URL: {backend_url}/data")
    print("⏰ Sending data every 2 seconds...")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Generate realistic sensor data
            sensor_data = {
                "flame": random.choice(["yes", "no"]),
                "mhb": random.choice(["yes", "no"]),
                "gas": random.randint(0, 1000),  # Gas level in ppm
                "temp": round(random.uniform(20.0, 40.0), 1),  # Temperature in Celsius
                "humidity": random.randint(30, 80)  # Humidity percentage
            }
            
            try:
                # Send data to backend
                response = requests.post(f"{backend_url}/data", 
                                       json=sensor_data, 
                                       timeout=5)
                
                if response.status_code == 200:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] ✅ Data sent successfully:")
                    print(f"   🔥 Flame: {sensor_data['flame']}")
                    print(f"   ⚡ MHB: {sensor_data['mhb']}")
                    print(f"   💨 Gas: {sensor_data['gas']} ppm")
                    print(f"   🌡️  Temp: {sensor_data['temp']}°C")
                    print(f"   💧 Humidity: {sensor_data['humidity']}%")
                    print()
                else:
                    print(f"❌ Failed to send data: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Connection Error: Backend server not running")
                print("   Please start the backend server first")
                break
            except requests.exceptions.Timeout:
                print("⚠️  Timeout: Backend server not responding")
            except Exception as e:
                print(f"❌ Error sending data: {str(e)}")
            
            # Wait 2 seconds before next reading
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user")
        print("✅ Simulation completed!")

def send_single_reading():
    """Send a single sensor reading for testing"""
    backend_url = "http://localhost:5000"
    
    # Sample data matching your ESP32 format
    sensor_data = {
        "flame": "yes",
        "mhb": "yes", 
        "gas": 0,
        "temp": 37.3,
        "humidity": 43
    }
    
    try:
        print("📤 Sending single sensor reading...")
        response = requests.post(f"{backend_url}/data", 
                               json=sensor_data, 
                               timeout=5)
        
        if response.status_code == 200:
            print("✅ Single reading sent successfully!")
            print(f"Data: {json.dumps(sensor_data, indent=2)}")
        else:
            print(f"❌ Failed to send: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        send_single_reading()
    else:
        simulate_sensor_data() 