import os
import json
import time
import tempfile
import webbrowser
import folium

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QComboBox,
    QLineEdit, QMessageBox, QDialog
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, pyqtSlot

# Resource path helper
def resource_path(relative_path):
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CameraLocationManager(QWidget):
    """Camera location management widget for adding/editing camera coordinates"""
    location_updated = pyqtSignal(str, float, float)  # camera_id, lat, lng
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.camera_locations = {}
        self.setup_ui()
        self.load_camera_locations()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("📍 Camera Location Manager")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                padding: 10px 0px;
            }
        """)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_camera_list)
        
        view_map_btn = QPushButton("🗺️ View All Locations")
        view_map_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        view_map_btn.clicked.connect(self.show_all_locations_map)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(view_map_btn)
        
        # Camera locations table
        self.setup_camera_table()
        # Add location form
        self.setup_add_location_form()
        
        layout.addWidget(header)
        layout.addWidget(self.camera_table_group)
        layout.addWidget(self.add_location_group)
        
    def setup_camera_table(self):
        self.camera_table_group = QGroupBox("Camera Locations")
        self.camera_table_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        table_layout = QVBoxLayout(self.camera_table_group)
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(7)
        self.camera_table.setHorizontalHeaderLabels([
            "Camera Name", "Camera ID", "Latitude", "Longitude", "Floor", "Common", "Actions"
        ])
        
        self.camera_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                gridline-color: #505050;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505050;
            }
            QTableWidget::item:selected {
                background-color: #ff3333;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                border: 1px solid #505050;
                font-weight: bold;
            }
        """)
        
        header = self.camera_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        table_layout.addWidget(self.camera_table)
        
    def setup_add_location_form(self):
        self.add_location_group = QGroupBox("Add/Edit Camera Location")
        self.add_location_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: white;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        form_layout = QVBoxLayout(self.add_location_group)
        
        form_widget = QWidget()
        from PyQt5.QtWidgets import QFormLayout
        form_grid = QFormLayout(form_widget)
        
        self.camera_combo = QPushButton("Select Camera")
        self.camera_combo.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        self.camera_combo.clicked.connect(self.show_camera_selection)
        
        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90.0, 90.0)
        self.latitude_input.setDecimals(8)
        self.latitude_input.setValue(0.0)
        self.latitude_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        
        self.longitude_input = QDoubleSpinBox()
        self.longitude_input.setRange(-360.0, 360.0)
        self.longitude_input.setDecimals(8)
        self.longitude_input.setValue(0.0)
        self.longitude_input.setStyleSheet(self.latitude_input.styleSheet())
        
        self.floor_combo = QComboBox()
        self.floor_combo.addItems(["Ground", "1", "2", "3", "4", "Roof", "Other"])
        self.floor_combo.setEditable(True)
        self.floor_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        
        self.common_combo = QComboBox()
        self.common_combo.setEditable(True)
        self.common_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        self.common_combo.setInsertPolicy(QComboBox.InsertAtTop)
        
        self.location_description = QLineEdit()
        self.location_description.setPlaceholderText("e.g., Main Entrance, Parking Lot, etc.")
        self.location_description.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ff3333;
            }
        """)
        
        form_grid.addRow("Camera:", self.camera_combo)
        form_grid.addRow("Latitude:", self.latitude_input)
        form_grid.addRow("Longitude:", self.longitude_input)
        form_grid.addRow("Floor:", self.floor_combo)
        form_grid.addRow("Common:", self.common_combo)
        form_grid.addRow("Description:", self.location_description)
        
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        save_btn = QPushButton("💾 Save Location")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_camera_location)
        
        clear_btn = QPushButton("🗑️ Clear Form")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)
        
        get_location_btn = QPushButton("📍 Get Current Location")
        get_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        get_location_btn.clicked.connect(self.get_current_location)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(get_location_btn)
        buttons_layout.addStretch()
        
        form_layout.addWidget(form_widget)
        form_layout.addWidget(buttons_widget)
        
        self.selected_camera_id = None
        self.selected_camera_name = None
        
    def show_camera_selection(self):
        cameras = self.config_manager.load_cameras()
        if not cameras:
            QMessageBox.information(self, "No Cameras", "No cameras found. Please add cameras first.")
            return
            
        dialog = CameraSelectionDialog(cameras, self)
        if dialog.exec_() == QDialog.Accepted:
            camera_id, camera_name = dialog.get_selected_camera()
            if camera_id:
                self.selected_camera_id = camera_id
                self.selected_camera_name = camera_name
                self.camera_combo.setText(f"📹 {camera_name}")
                
                if camera_id in self.camera_locations:
                    location = self.camera_locations[camera_id]
                    self.latitude_input.setValue(location['latitude'])
                    self.longitude_input.setValue(location['longitude'])
                    self.location_description.setText(location.get('description', ''))
                    self.floor_combo.setCurrentText(location.get('floor', ''))
                    self.common_combo.setCurrentText(location.get('common', ''))
                    
    def save_camera_location(self):
        if not self.selected_camera_id:
            QMessageBox.warning(self, "No Camera Selected", "Please select a camera first.")
            return
            
        latitude = self.latitude_input.value()
        longitude = self.longitude_input.value()
        description = self.location_description.text().strip()
        floor = self.floor_combo.currentText().strip()
        common = self.common_combo.currentText().strip()
        
        if common and self.common_combo.findText(common) == -1:
            self.common_combo.addItem(common)
        
        if latitude == 0.0 and longitude == 0.0:
            reply = QMessageBox.question(self, "Confirm Location", 
                                       "Latitude and Longitude are both 0.0. Are you sure this is correct?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        self.camera_locations[self.selected_camera_id] = {
            'camera_name': self.selected_camera_name,
            'latitude': latitude,
            'longitude': longitude,
            'floor': floor,
            'common': common,
            'description': description,
            'timestamp': time.time()
        }
        
        self.save_camera_locations()
        self.refresh_camera_table()
        self.clear_form()
        
        self.location_updated.emit(self.selected_camera_id, latitude, longitude)
        QMessageBox.information(self, "Location Saved", 
                              f"Location saved for camera '{self.selected_camera_name}'")
    
    def clear_form(self):
        self.selected_camera_id = None
        self.selected_camera_name = None
        self.camera_combo.setText("Select Camera")
        self.latitude_input.setValue(0.0)
        self.longitude_input.setValue(0.0)
        self.location_description.clear()
        self.floor_combo.setCurrentText('')
        self.common_combo.setCurrentText('')
        
    def get_current_location(self):
        QMessageBox.information(self, "Get Location", 
                              "This feature would integrate with geolocation services.\n"
                              "For now, please enter coordinates manually.\n\n"
                              "You can use Google Maps to find coordinates:\n"
                              "1. Right-click on location in Google Maps\n"
                              "2. Click on coordinates to copy them")
        
    def refresh_camera_list(self):
        self.load_camera_locations()
        self.refresh_camera_table()
        
    def refresh_camera_table(self):
        self.camera_table.setRowCount(len(self.camera_locations))
        
        for row, (camera_id, location) in enumerate(self.camera_locations.items()):
            name_item = QTableWidgetItem(location['camera_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 0, name_item)
            
            id_item = QTableWidgetItem(camera_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 1, id_item)
            
            lat_item = QTableWidgetItem(f"{location['latitude']:.6f}")
            lat_item.setFlags(lat_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 2, lat_item)
            
            lng_item = QTableWidgetItem(f"{location['longitude']:.6f}")
            lng_item.setFlags(lng_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 3, lng_item)
            
            floor_item = QTableWidgetItem(location.get('floor', ''))
            floor_item.setFlags(floor_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 4, floor_item)
            
            common_item = QTableWidgetItem(location.get('common', ''))
            common_item.setFlags(common_item.flags() & ~Qt.ItemIsEditable)
            self.camera_table.setItem(row, 5, common_item)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setToolTip("Edit Location")
            edit_btn.clicked.connect(lambda checked, cid=camera_id: self.edit_camera_location(cid))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setToolTip("Delete Location")
            delete_btn.clicked.connect(lambda checked, cid=camera_id: self.delete_camera_location(cid))
            
            map_btn = QPushButton("🗺️")
            map_btn.setFixedSize(30, 30)
            map_btn.setToolTip("Show on Map")
            map_btn.clicked.connect(lambda checked, cid=camera_id: self.show_camera_on_map(cid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(map_btn)
            actions_layout.addStretch()
            
            self.camera_table.setCellWidget(row, 6, actions_widget)
            
    def edit_camera_location(self, camera_id):
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            self.selected_camera_id = camera_id
            self.selected_camera_name = location['camera_name']
            self.camera_combo.setText(f"📹 {location['camera_name']}")
            self.latitude_input.setValue(location['latitude'])
            self.longitude_input.setValue(location['longitude'])
            self.location_description.setText(location.get('description', ''))
            self.floor_combo.setCurrentText(location.get('floor', ''))
            self.common_combo.setCurrentText(location.get('common', ''))
            
    def delete_camera_location(self, camera_id):
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            reply = QMessageBox.question(self, "Delete Location", 
                                       f"Are you sure you want to delete the location for camera '{location['camera_name']}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.camera_locations[camera_id]
                self.save_camera_locations()
                self.refresh_camera_table()
                QMessageBox.information(self, "Location Deleted", "Camera location deleted successfully.")
                
    def show_camera_on_map(self, camera_id):
        if camera_id in self.camera_locations:
            location = self.camera_locations[camera_id]
            self.show_map_with_cameras({camera_id: location})
            
    def show_all_locations_map(self):
        if not self.camera_locations:
            QMessageBox.information(self, "No Locations", "No camera locations found.")
            return
        self.show_map_with_cameras(self.camera_locations)
        
    def show_map_with_cameras(self, cameras_dict):
        try:
            if cameras_dict:
                first_location = list(cameras_dict.values())[0]
                center_lat = first_location['latitude']
                center_lng = first_location['longitude']
            else:
                center_lat, center_lng = 0.0, 0.0
                
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=15 if cameras_dict else 2,
                tiles='OpenStreetMap'
            )
            
            for camera_id, location in cameras_dict.items():
                popup_text = f"""
                <b>📹 {location['camera_name']}</b><br>
                <b>ID:</b> {camera_id}<br>
                <b>Location:</b> {location.get('description', 'No description')}<br>
                <b>Coordinates:</b> {location['latitude']:.6f}, {location['longitude']:.6f}
                """
                
                folium.Marker(
                    location=[location['latitude'], location['longitude']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=location['camera_name'],
                    icon=folium.Icon(color='blue', icon='video-camera', prefix='fa')
                ).add_to(m)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            m.save(temp_file.name)
            webbrowser.open(f'file://{temp_file.name}')
            
        except Exception as e:
            QMessageBox.critical(self, "Map Error", f"Error creating map: {str(e)}")
            
    def load_camera_locations(self):
        try:
            locations_file = resource_path("config/camera_locations.json")
            if os.path.exists(locations_file):
                with open(locations_file, 'r') as f:
                    self.camera_locations = json.load(f)
            else:
                self.camera_locations = {}
        except Exception as e:
            print(f"❌ Error loading camera locations: {e}")
            self.camera_locations = {}
            
    def save_camera_locations(self):
        try:
            locations_file = resource_path("config/camera_locations.json")
            os.makedirs(os.path.dirname(locations_file), exist_ok=True)
            with open(locations_file, 'w') as f:
                json.dump(self.camera_locations, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving camera locations: {e}")
            
    def get_camera_location(self, camera_id):
        return self.camera_locations.get(camera_id)


class CameraSelectionDialog(QDialog):
    """Dialog for selecting a camera"""
    def __init__(self, cameras, parent=None):
        super().__init__(parent)
        self.cameras = cameras
        self.selected_camera_id = None
        self.selected_camera_name = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Select Camera")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        title = QLabel("Select a Camera")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
            }
        """)
        
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(2)
        self.camera_table.setHorizontalHeaderLabels(["Camera Name", "Camera ID"])
        self.camera_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.camera_table.setRowCount(len(self.cameras))
        for row, (camera_id, camera_data) in enumerate(self.cameras.items()):
            name_item = QTableWidgetItem(camera_data.get('name', 'Unknown'))
            id_item = QTableWidgetItem(camera_id)
            self.camera_table.setItem(row, 0, name_item)
            self.camera_table.setItem(row, 1, id_item)
            
        self.camera_table.doubleClicked.connect(self.on_camera_double_clicked)
        
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(select_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.camera_table)
        layout.addWidget(buttons_widget)
        
    def on_camera_double_clicked(self):
        self.accept()
        
    def accept(self):
        current_row = self.camera_table.currentRow()
        if current_row >= 0:
            self.selected_camera_name = self.camera_table.item(current_row, 0).text()
            self.selected_camera_id = self.camera_table.item(current_row, 1).text()
        super().accept()
        
    def get_selected_camera(self):
        return self.selected_camera_id, self.selected_camera_name


class FireLocationMapWidget(QWidget):
    """Widget to show fire detection location on map"""
    def __init__(self, camera_location_manager):
        super().__init__()
        self.camera_location_manager = camera_location_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #ff0000;
                border-radius: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        title = QLabel("🚨 FIRE DETECTED - LOCATION MAP 🚨")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        close_btn = QPushButton("✖️ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        self.map_container = QLabel()
        self.map_container.setAlignment(Qt.AlignCenter)
        self.map_container.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #ff0000;
                border-radius: 8px;
                color: white;
                font-size: 16px;
            }
        """)
        self.map_container.setText("🗺️ Map will be displayed here")
        
        layout.addWidget(header)
        layout.addWidget(self.map_container)
        
    def show_fire_location(self, camera_id, camera_name):
        location = self.camera_location_manager.get_camera_location(camera_id)
        if not location:
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Camera ID: {camera_id}
            
            ⚠️ No location data available for this camera.
            Please add location coordinates in Camera Manager.
            """)
            return
            
        try:
            m = folium.Map(
                location=[location['latitude'], location['longitude']],
                zoom_start=18,
                tiles='OpenStreetMap'
            )
            
            popup_text = f"""
            <div style="text-align: center;">
                <h3 style="color: red;">🚨 FIRE ALERT 🚨</h3>
                <b>Camera:</b> {camera_name}<br>
                <b>Location:</b> {location.get('description', 'No description')}<br>
                <b>Coordinates:</b> {location['latitude']:.6f}, {location['longitude']:.6f}<br>
                <b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            """
            
            folium.Marker(
                location=[location['latitude'], location['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"🔥 FIRE: {camera_name}",
                icon=folium.Icon(color='red', icon='fire', prefix='fa')
            ).add_to(m)
            
            folium.Circle(
                location=[location['latitude'], location['longitude']],
                radius=100,
                color='red',
                fillColor='red',
                fillOpacity=0.3,
                popup='Fire Detection Area'
            ).add_to(m)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            m.save(temp_file.name)
            webbrowser.open(f'file://{temp_file.name}')
            
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Location: {location.get('description', 'No description')}
            Coordinates: {location['latitude']:.6f}, {location['longitude']:.6f}
            
            🗺️ Map opened in browser for fullscreen view
            """)
            
        except Exception as e:
            self.map_container.setText(f"""
            🚨 FIRE DETECTED 🚨
            
            Camera: {camera_name}
            Camera ID: {camera_id}
            
            ❌ Error loading map: {str(e)}
            """)
