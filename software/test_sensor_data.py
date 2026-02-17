#!/usr/bin/env python3
"""
Test script to verify sensor data fetching from backend
"""

import requests
import json
from datetime import datetime

def test_sensor_data_fetch():
    """Test fetching sensor data from backend"""
    backend_url = "http://localhost:5000"
    
    try:
        print("🔍 Testing sensor data fetch from backend...")
        print(f"📡 Backend URL: {backend_url}/data")
        
        # Test the /data endpoint
        response = requests.get(f"{backend_url}/data", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Received {len(data)} sensor readings")
            
            if data and len(data) > 0:
                latest = data[0]  # Most recent reading
                print("\n📊 Latest Sensor Data:")
                print(f"   Flame: {latest.get('flame', 'N/A')}")
                print(f"   MHB: {latest.get('mhb', 'N/A')}")
                print(f"   Gas: {latest.get('gas', 'N/A')} ppm")
                print(f"   Temperature: {latest.get('temp', 'N/A')}°C")
                print(f"   Humidity: {latest.get('humidity', 'N/A')}%")
                print(f"   Timestamp: {latest.get('timestamp', 'N/A')}")
                
                # Format timestamp for display
                if latest.get('timestamp'):
                    try:
                        if isinstance(latest['timestamp'], str):
                            dt = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00'))
                        else:
                            dt = latest['timestamp']
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"   Formatted Time: {formatted_time}")
                    except Exception as e:
                        print(f"   Time parsing error: {e}")
            else:
                print("⚠️  No sensor data available in database")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to backend server")
        print("   Make sure the backend server is running on http://localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request timed out")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_backend_health():
    """Test backend health endpoint"""
    backend_url = "http://localhost:5000"
    
    try:
        print("\n🏥 Testing backend health...")
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is healthy!")
            print(f"   Status: {health_data.get('status', 'N/A')}")
            print(f"   MongoDB: {health_data.get('mongodb', 'N/A')}")
            print(f"   Timestamp: {health_data.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Sensor Data Test Script")
    print("=" * 50)
    
    test_backend_health()
    test_sensor_data_fetch()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 