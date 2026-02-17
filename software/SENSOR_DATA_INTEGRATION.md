# Sensor Data Integration Guide

This guide explains how the sensor data from ESP32 is integrated into the Fire Vision Pro application and displayed in real-time on the PB001 sensor card.

## 🏗️ Architecture Overview

```
ESP32 → Backend Server → Database → Frontend (Sensors Page)
   ↓         ↓            ↓           ↓
Sensor   POST /data    MongoDB    Real-time
Data     endpoint      Storage    Display
```

## 📊 Data Flow

1. **ESP32** sends sensor data to backend via `POST /data` endpoint
2. **Backend** stores data in MongoDB with TTL (1 hour expiration)
3. **Frontend** fetches latest data every second and displays in PB001 card
4. **Real-time updates** show current sensor values with timestamp

## 🔧 Backend Setup

### 1. Start the Backend Server

```bash
cd backend_server
npm install
npm start
```

The server will run on `http://localhost:5000`

### 2. Verify Backend is Running

```bash
python test_sensor_data.py
```

This will test the connection and show current sensor data.

## 📡 ESP32 Data Format

The ESP32 should send data in this JSON format:

```json
{
  "flame": "yes",
  "mhb": "yes", 
  "gas": 0,
  "temp": 37.3,
  "humidity": 43
}
```

### Field Descriptions:
- **flame**: "yes" or "no" - Flame detection status
- **mhb**: "yes" or "no" - MHB sensor status  
- **gas**: Number (0-1000) - Gas level in ppm
- **temp**: Number (20-40) - Temperature in Celsius
- **humidity**: Number (30-80) - Humidity percentage

## 🧪 Testing the Integration

### 1. Test Backend Connection

```bash
python test_sensor_data.py
```

### 2. Simulate ESP32 Data

```bash
# Send single reading
python simulate_esp32_data.py --single

# Continuous simulation (every 2 seconds)
python simulate_esp32_data.py
```

### 3. View Real-time Data

1. Start the main application
2. Navigate to Sensors page
3. Look at the PB001 card - it will show real-time sensor data
4. Data updates every second automatically

## 🎯 PB001 Card Features

The PB001 sensor card now displays:

- **Flame Status**: Current flame detection state
- **MHB Status**: MHB sensor reading
- **Gas Level**: Gas concentration in ppm
- **Temperature**: Current temperature in °C
- **Humidity**: Current humidity percentage
- **Last Update**: Timestamp of last data update

## 🔄 Real-time Updates

- Data is fetched every 1 second from the backend
- Only the latest reading is displayed
- Timestamp shows when data was last updated
- Connection errors are handled gracefully

## 🛠️ Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:5000/api/health

# Check MongoDB connection
curl http://localhost:5000/data
```

### No Data Displayed
1. Verify backend server is running
2. Check if ESP32 is sending data
3. Use test script to verify data flow
4. Check browser console for errors

### Data Not Updating
1. Verify network connection
2. Check backend logs for errors
3. Restart the application
4. Verify ESP32 is sending data regularly

## 📝 API Endpoints

### POST /data
Receives sensor data from ESP32
```bash
curl -X POST http://localhost:5000/data \
  -H "Content-Type: application/json" \
  -d '{"flame":"yes","mhb":"yes","gas":0,"temp":37.3,"humidity":43}'
```

### GET /data  
Retrieves last 20 sensor readings
```bash
curl http://localhost:5000/data
```

### GET /api/health
Backend health check
```bash
curl http://localhost:5000/api/health
```

## 🔧 Configuration

### Backend URL
The frontend connects to `http://localhost:5000` by default. To change this:

1. Edit `sensors_page.py`
2. Modify `self.backend_url` in `SensorDataFetcher` class
3. Restart the application

### Update Frequency
To change how often data is fetched:

1. Edit `sensors_page.py`
2. Modify `self.msleep(1000)` in `SensorDataFetcher.run()`
3. Value is in milliseconds (1000 = 1 second)

## 📊 Database Schema

```javascript
{
  flame: String,        // "yes" or "no"
  mhb: String,          // "yes" or "no"
  gas: Number,          // Gas level in ppm
  temp: Number,         // Temperature in Celsius
  humidity: Number,     // Humidity percentage
  timestamp: Date       // Auto-generated timestamp
}
```

Data automatically expires after 1 hour (TTL index).

## 🚀 Production Deployment

For production use:

1. **Backend**: Deploy to cloud server (AWS, Azure, etc.)
2. **Database**: Use MongoDB Atlas or cloud MongoDB
3. **ESP32**: Update backend URL to production server
4. **Frontend**: Update backend URL in application
5. **Security**: Add authentication and HTTPS

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all components are running
3. Check logs for error messages
4. Test with the provided test scripts
5. Ensure network connectivity between components 