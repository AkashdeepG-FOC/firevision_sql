import cv2
import numpy as np
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFrame, QSplitter, QTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QWidget)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QSize

class FireAlertDialog(QDialog):
    """Dialog to display fire alert details"""
    
    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.setWindowTitle("Fire Alert Details")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ff3333;
            }
            QLabel#infoLabel {
                font-size: 14px;
                color: #ffffff;
            }
            QFrame#imageFrame {
                border: 2px solid #ff3333;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton#alertButton {
                background-color: #ff3333;
                color: white;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3d3d3d;
                selection-background-color: #ff3333;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Title section
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        
        event_type = self.event_data.get("subtype", "fire").title()
        title = QLabel(f"{event_type} Alert")
        title.setObjectName("titleLabel")
        
        timestamp = self.event_data.get("timestamp", "Unknown")
        if hasattr(timestamp, "strftime"):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        time_label = QLabel(timestamp_str)
        time_label.setObjectName("infoLabel")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(time_label)
        
        layout.addWidget(title_widget)
        
        # Main content
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Image section
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        image_frame = QFrame()
        image_frame.setObjectName("imageFrame")
        image_frame_layout = QVBoxLayout(image_frame)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        
        # Load image if available
        if "image_path" in self.event_data and os.path.exists(self.event_data["image_path"]):
            self.load_image(self.event_data["image_path"])
        else:
            self.image_label.setText("No image available")
        
        image_frame_layout.addWidget(self.image_label)
        image_layout.addWidget(image_frame)
        
        # Camera info
        camera_id = self.event_data.get("camera_id", "Unknown")
        camera_label = QLabel(f"Camera: {camera_id}")
        camera_label.setObjectName("infoLabel")
        image_layout.addWidget(camera_label)
        
        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # Alert details
        details_title = QLabel("Alert Details")
        details_title.setFont(QFont("Arial", 14, QFont.Bold))
        info_layout.addWidget(details_title)
        
        # Details table
        details_table = QTableWidget()
        details_table.setColumnCount(2)
        details_table.setHorizontalHeaderLabels(["Property", "Value"])
        details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Add rows
        details = [
            ("Type", self.event_data.get("subtype", "fire").title()),
            ("Confidence", f"{self.event_data.get('confidence', 0):.1f}%"),
            ("Camera", self.event_data.get("camera_id", "Unknown")),
            ("Time", timestamp_str),
        ]
        
        details_table.setRowCount(len(details))
        for i, (prop, value) in enumerate(details):
            details_table.setItem(i, 0, QTableWidgetItem(prop))
            value_item = QTableWidgetItem(value)
            if prop == "Confidence":
                confidence = float(value.replace("%", ""))
                if confidence > 80:
                    value_item.setForeground(QColor("#ff3333"))  # Red for high confidence
                elif confidence > 60:
                    value_item.setForeground(QColor("#ff9933"))  # Orange for medium confidence
            details_table.setItem(i, 1, value_item)
        
        info_layout.addWidget(details_table)
        
        # Detection details
        if "details" in self.event_data and "detections" in self.event_data["details"]:
            detections_title = QLabel("Detections")
            detections_title.setFont(QFont("Arial", 14, QFont.Bold))
            info_layout.addWidget(detections_title)
            
            detections_table = QTableWidget()
            detections_table.setColumnCount(3)
            detections_table.setHorizontalHeaderLabels(["Object", "Confidence", "Position"])
            
            detections = self.event_data["details"]["detections"]
            detections_table.setRowCount(len(detections))
            
            for i, detection in enumerate(detections):
                obj_class = detection.get("class", "Unknown")
                confidence = detection.get("confidence", 0) * 100
                bbox = detection.get("bbox", [0, 0, 0, 0])
                position = f"x={bbox[0]}, y={bbox[1]}, w={bbox[2]}, h={bbox[3]}"
                
                detections_table.setItem(i, 0, QTableWidgetItem(obj_class))
                
                conf_item = QTableWidgetItem(f"{confidence:.1f}%")
                if confidence > 80:
                    conf_item.setForeground(QColor("#ff3333"))  # Red for high confidence
                elif confidence > 60:
                    conf_item.setForeground(QColor("#ff9933"))  # Orange for medium confidence
                detections_table.setItem(i, 1, conf_item)
                
                detections_table.setItem(i, 2, QTableWidgetItem(position))
            
            info_layout.addWidget(detections_table)
        
        # Notes section
        notes_title = QLabel("Notes")
        notes_title.setFont(QFont("Arial", 14, QFont.Bold))
        info_layout.addWidget(notes_title)
        
        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Add notes about this alert...")
        info_layout.addWidget(notes_edit)
        
        # Add widgets to splitter
        content_splitter.addWidget(image_widget)
        content_splitter.addWidget(info_widget)
        content_splitter.setSizes([400, 400])
        
        layout.addWidget(content_splitter)
        
        # Buttons
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        alert_btn = QPushButton("Send Alert")
        alert_btn.setObjectName("alertButton")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(alert_btn)
        buttons_layout.addWidget(close_btn)
        
        layout.addWidget(buttons_widget)
    
    def load_image(self, image_path):
        """Load image from path"""
        try:
            # Load image with OpenCV to handle various formats
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                self.image_label.setText("Failed to load image")
                return
            
            # Convert to RGB for display
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            # Convert to QImage and QPixmap
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Scale to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(qt_img)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.image_label.setText(f"Error loading image: {e}")