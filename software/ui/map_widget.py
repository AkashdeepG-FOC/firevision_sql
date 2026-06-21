import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, QTimer, QUrl

class LightweightMapWebView(QWebEngineView):
    """
    A lightweight WebEngineView that avoids folium generation 
    and directly loads a minimal Leaflet HTML map to save memory.
    """
    location_picked = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page().titleChanged.connect(self._handle_title_change)

    def _handle_title_change(self, title):
        if title.startswith("LATLNG:"):
            parts = title.replace("LATLNG:", "").split(",")
            if len(parts) == 2:
                try:
                    lat, lng = float(parts[0]), float(parts[1])
                    self.location_picked.emit(lat, lng)
                except ValueError:
                    pass

    def load_minimal_leaflet(self, lat=0.0, lng=0.0, zoom=15, selectable=False, locations=None):
        zoom = 15 if lat != 0.0 else 2
        locations_json = json.dumps(locations or [])
        selectable_str = 'true' if selectable else 'false'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lightweight Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body {{ padding: 0; margin: 0; }}
                html, body, #map {{ height: 100vh; width: 100vw; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{lat}, {lng}], {zoom});
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }}).addTo(map);
                
                var currentMarker = null;
                var selectable = {selectable_str};
                
                if (selectable) {{
                    map.on('click', function(e) {{
                        if (currentMarker) {{
                            map.removeLayer(currentMarker);
                        }}
                        currentMarker = L.marker(e.latlng).addTo(map);
                        document.title = "LATLNG:" + e.latlng.lat + "," + e.latlng.lng;
                    }});
                }}
                
                var locations = {locations_json};
                locations.forEach(function(loc) {{
                    L.marker([loc.lat, loc.lng]).addTo(map)
                      .bindPopup("<b>" + loc.id + "</b><br>" + loc.name);
                }});
            </script>
        </body>
        </html>
        """
        self.setHtml(html)

    def load_cameras_map(self, camera_locations=None):
        """Load a compact read-only Leaflet map with camera markers."""
        locations = []
        for camera_id, loc in (camera_locations or {}).items():
            try:
                lat = float(loc.get('latitude', 0))
                lng = float(loc.get('longitude', 0))
            except (TypeError, ValueError):
                continue
            if lat == 0.0 and lng == 0.0:
                continue
            locations.append({
                'id': camera_id,
                'name': loc.get('camera_name', camera_id),
                'lat': lat,
                'lng': lng,
                'description': loc.get('description', ''),
                'common': loc.get('common', ''),
            })

        if locations:
            center_lat = sum(loc['lat'] for loc in locations) / len(locations)
            center_lng = sum(loc['lng'] for loc in locations) / len(locations)
            zoom = 16
        else:
            center_lat, center_lng, zoom = 0.0, 0.0, 2

        locations_json = json.dumps(locations)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body {{ padding: 0; margin: 0; background: #f5f5f5; }}
                html, body, #map {{ height: 100%; width: 100%; }}
                .camera-marker {{
                    background: #2563eb;
                    border: 2px solid #ffffff;
                    border-radius: 50%;
                    width: 26px;
                    height: 26px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ffffff;
                    font-size: 12px;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {{
                    zoomControl: false,
                    attributionControl: false,
                    dragging: true,
                    scrollWheelZoom: false,
                    doubleClickZoom: false,
                    boxZoom: false,
                    keyboard: false
                }}).setView([{center_lat}, {center_lng}], {zoom});

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19
                }}).addTo(map);

                var cameraIcon = L.divIcon({{
                    html: '<div class="camera-marker">📹</div>',
                    className: '',
                    iconSize: [26, 26],
                    iconAnchor: [13, 13],
                    popupAnchor: [0, -10]
                }});

                var locations = {locations_json};
                var markers = [];

                locations.forEach(function(loc) {{
                    var popup = '<b>' + loc.name + '</b><br>' +
                        (loc.description ? loc.description + '<br>' : '') +
                        (loc.common ? 'Common: ' + loc.common + '<br>' : '') +
                        'Lat: ' + loc.lat.toFixed(6) + ', Lng: ' + loc.lng.toFixed(6);
                    var marker = L.marker([loc.lat, loc.lng], {{ icon: cameraIcon }})
                        .addTo(map)
                        .bindPopup(popup);
                    markers.push(marker);
                }});

                if (markers.length === 1) {{
                    map.setView([locations[0].lat, locations[0].lng], 18);
                }} else if (markers.length > 1) {{
                    var group = L.featureGroup(markers);
                    map.fitBounds(group.getBounds().pad(0.15));
                }}
            </script>
        </body>
        </html>
        """
        self.setHtml(html)

class MapPickerWidget(QDialog):
    """Dialog to pick a location from a map using lightweight Leaflet."""
    location_picked = pyqtSignal(float, float)

    def __init__(self, parent=None, initial_lat=0.0, initial_lng=0.0):
        super().__init__(parent)
        self.setWindowTitle("Pick Location")
        self.setMinimumSize(800, 600)
        self.current_lat = initial_lat
        self.current_lng = initial_lng

        layout = QVBoxLayout(self)
        
        self.map_view = LightweightMapWebView()
        self.map_view.location_picked.connect(self._handle_location)
        self.map_view.load_minimal_leaflet(initial_lat, initial_lng, selectable=True)
        
        layout.addWidget(self.map_view)

        # Buttons
        btn_layout = QHBoxLayout()
        self.accept_btn = QPushButton("Select Current Location")
        self.accept_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.accept_btn.clicked.connect(self.accept_location)
        btn_layout.addWidget(self.accept_btn)
        layout.addLayout(btn_layout)

    def _handle_location(self, lat, lng):
        self.current_lat = lat
        self.current_lng = lng

    def accept_location(self):
        self.location_picked.emit(self.current_lat, self.current_lng)
        self.accept()
