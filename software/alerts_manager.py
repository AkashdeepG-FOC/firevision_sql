import json
import os
import time
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QDateEdit, QLineEdit, QHeaderView,
                             QDialog, QTextEdit, QCheckBox, QMessageBox,
                             QProgressBar, QTabWidget, QScrollArea, QFrame,
                             QMenu, QAction)
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt, QDate
import sys
from backend_client import backend_client

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    camera_id: str
    camera_name: str
    alert_type: str  # 'fire', 'smoke', 'people', 'motion', 'system'
    severity: str    # 'low', 'medium', 'high', 'critical'
    timestamp: float
    confidence: float
    description: str
    status: str      # 'active', 'acknowledged', 'resolved', 'false_alarm'
    footage_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata: Optional[Dict] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[float] = None
    backend_id: Optional[int] = None

class AlertsManager(QObject):
    """Manager for handling all types of alerts and detections"""
    
    alert_created = pyqtSignal(Alert)
    alert_updated = pyqtSignal(Alert)
    alert_deleted = pyqtSignal(str)  # alert_id
    
    def __init__(self):
        super().__init__()
        self.alerts_file = "data/alerts.json"
        self.footage_dir = "footage/alerts"
        self.thumbnails_dir = "thumbnails/alerts"
        
        # Create directories
        os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
        os.makedirs(self.footage_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        
        # Alert retention settings
        self.retention_days = 30
        
        # In-memory alerts list
        self.alerts: List[Alert] = []
        self.load_alerts_from_file()
        
        # Start cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_alerts)
        self.cleanup_timer.start(24 * 60 * 60 * 1000)  # Daily cleanup
    
    def load_alerts_from_file(self):
        """Load alerts from JSON file"""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                
                self.alerts = []
                for data in alerts_data:
                    # Convert dict back to Alert object
                    # Handle optional fields
                    self.alerts.append(Alert(
                        id=data['id'],
                        camera_id=data['camera_id'],
                        camera_name=data['camera_name'],
                        alert_type=data['alert_type'],
                        severity=data['severity'],
                        timestamp=data['timestamp'],
                        confidence=data['confidence'],
                        description=data['description'],
                        status=data['status'],
                        footage_path=data.get('footage_path'),
                        thumbnail_path=data.get('thumbnail_path'),
                        metadata=data.get('metadata'),
                        acknowledged_by=data.get('acknowledged_by'),
                        acknowledged_at=data.get('acknowledged_at'),
                        resolved_by=data.get('resolved_by'),
                        resolved_at=data.get('resolved_at'),
                        backend_id=data.get('backend_id')
                    ))
                print(f"✅ Loaded {len(self.alerts)} alerts")
            else:
                self.alerts = []
                print("ℹ️ No existing alerts file found")
                
        except Exception as e:
            print(f"❌ Error loading alerts from file: {e}")
            self.alerts = []

    def save_alerts_to_file(self):
        """Save alerts to JSON file"""
        try:
            alerts_data = []
            for alert in self.alerts:
                alerts_data.append(asdict(alert))
            
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving alerts to file: {e}")

    def create_alert(self, camera_id: str, camera_name: str, alert_type: str,
                    severity: str, confidence: float, description: str,
                    footage_path: str = None, metadata: Dict = None) -> str:
        """Create a new alert"""
        try:
            alert_id = f"{alert_type}_{camera_id}_{int(time.time())}"
            
            alert = Alert(
                id=alert_id,
                camera_id=camera_id,
                camera_name=camera_name,
                alert_type=alert_type,
                severity=severity,
                timestamp=time.time(),
                confidence=confidence,
                description=description,
                status='active',
                footage_path=footage_path,
                metadata=metadata
            )
            
            # Add to list
            self.alerts.append(alert)
            
            # Save to file
            self.save_alerts_to_file()
            
            # Sync to backend
            try:
                # Need integer camera ID for backend
                # If camera_id is not an int, we might need a mapping or try to cast
                b_camera_id = int(camera_id) if camera_id.isdigit() else 1 # Fallback to 1 if not digit
                
                backend_alert = backend_client.create_alert(
                    camera_id=b_camera_id,
                    alert_type=alert_type,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    footage_path=footage_path
                )
                if backend_alert and 'id' in backend_alert:
                    alert.backend_id = backend_alert['id']
                    self.save_alerts_to_file() # Save again with backend_id
                    print(f"🔗 Alert synced to backend with ID: {alert.backend_id}")
            except Exception as be:
                print(f"⚠️ Failed to sync alert to backend: {be}")

            # Emit signal
            self.alert_created.emit(alert)
            
            print(f"🚨 Alert created: {alert_id}")
            return alert_id
            
        except Exception as e:
            print(f"❌ Error creating alert: {e}")
            return None
    
    def save_alert(self, alert: Alert):
        """Update an existing alert"""
        try:
            # Find and update in list
            for i, a in enumerate(self.alerts):
                if a.id == alert.id:
                    self.alerts[i] = alert
                    break
            else:
                # If not found, append (should rely on create_alert mostly)
                self.alerts.append(alert)
            
            self.save_alerts_to_file()
            
        except Exception as e:
            print(f"❌ Error saving alert: {e}")
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id:
                return alert
        return None
    
    def get_alerts(self, camera_id: str = None, alert_type: str = None,
                  status: str = None, start_date: datetime = None,
                  end_date: datetime = None, limit: int = 100) -> List[Alert]:
        """Get alerts with filters"""
        filtered_alerts = self.alerts
        
        # Apply filters
        if camera_id:
            filtered_alerts = [a for a in filtered_alerts if a.camera_id == camera_id]
            
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a.alert_type == alert_type]
            
        if status:
            filtered_alerts = [a for a in filtered_alerts if a.status == status]
            
        if start_date:
            ts = start_date.timestamp()
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= ts]
            
        if end_date:
            ts = end_date.timestamp()
            filtered_alerts = [a for a in filtered_alerts if a.timestamp <= ts]
            
        # Sort by timestamp descending
        filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return False
            
            alert.status = 'acknowledged'
            alert.acknowledged_by = user
            alert.acknowledged_at = time.time()
            
            self.save_alert(alert)
            self.alert_updated.emit(alert)
            
            # Sync to backend
            if alert.backend_id:
                backend_client.update_alert(alert.backend_id, status='acknowledged')
            
            print(f"✅ Alert {alert_id} acknowledged by {user}")
            return True
            
        except Exception as e:
            print(f"❌ Error acknowledging alert: {e}")
            return False
    
    def resolve_alert(self, alert_id: str, user: str) -> bool:
        """Resolve an alert"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return False
            
            alert.status = 'resolved'
            alert.resolved_by = user
            alert.resolved_at = time.time()
            
            self.save_alert(alert)
            self.alert_updated.emit(alert)
            
            # Sync to backend
            if alert.backend_id:
                backend_client.update_alert(alert.backend_id, status='resolved')
            
            print(f"✅ Alert {alert_id} resolved by {user}")
            return True
            
        except Exception as e:
            print(f"❌ Error resolving alert: {e}")
            return False
    
    def mark_false_alarm(self, alert_id: str, user: str) -> bool:
        """Mark alert as false alarm"""
        try:
            alert = self.get_alert(alert_id)
            if not alert:
                return False
            
            alert.status = 'false_alarm'
            alert.resolved_by = user
            alert.resolved_at = time.time()
            
            self.save_alert(alert)
            self.alert_updated.emit(alert)
            
            print(f"✅ Alert {alert_id} marked as false alarm by {user}")
            return True
            
        except Exception as e:
            print(f"❌ Error marking false alarm: {e}")
            return False
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert"""
        try:
            original_len = len(self.alerts)
            self.alerts = [a for a in self.alerts if a.id != alert_id]
            
            if len(self.alerts) < original_len:
                self.save_alerts_to_file()
                self.alert_deleted.emit(alert_id)
                print(f"🗑️ Alert {alert_id} deleted")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error deleting alert: {e}")
            return False
    
    def cleanup_old_alerts(self):
        """Clean up old alerts based on retention policy"""
        try:
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            original_len = len(self.alerts)
            
            # Keep only new alerts
            self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
            
            if len(self.alerts) < original_len:
                deleted_count = original_len - len(self.alerts)
                self.save_alerts_to_file()
                print(f"🧹 Cleaned up {deleted_count} old alerts")
            
        except Exception as e:
            print(f"❌ Error cleaning up old alerts: {e}")
    
    def get_alert_statistics(self) -> Dict:
        """Get alert statistics"""
        total_alerts = len(self.alerts)
        active_alerts = sum(1 for a in self.alerts if a.status == 'active')
        
        alerts_by_type = {}
        alerts_by_severity = {}
        recent_alerts = 0
        
        yesterday = time.time() - (24 * 60 * 60)
        
        for alert in self.alerts:
            # Type stats
            alerts_by_type[alert.alert_type] = alerts_by_type.get(alert.alert_type, 0) + 1
            
            # Severity stats
            alerts_by_severity[alert.severity] = alerts_by_severity.get(alert.severity, 0) + 1
            
            # Recent stats
            if alert.timestamp > yesterday:
                recent_alerts += 1
                
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_severity': alerts_by_severity,
            'recent_alerts': recent_alerts
        }

class AlertsWidget(QWidget):
    """Modern widget for displaying and managing alerts"""
    
    def __init__(self, alerts_manager: AlertsManager):
        super().__init__()
        self.alerts_manager = alerts_manager
        self.current_alerts = []
        self.camera_id_map = {}  # name -> id
        self.setup_modern_ui()
        self.connect_signals()
        self.load_alerts()
    
    def set_camera_list(self, camera_list):
        """camera_list: list of (camera_id, camera_name)"""
        self.camera_filter.blockSignals(True)
        self.camera_filter.clear()
        self.camera_filter.addItem("All Cameras", None)
        self.camera_id_map = {}
        for cid, name in camera_list:
            self.camera_filter.addItem(name, cid)
            self.camera_id_map[name] = cid
        self.camera_filter.blockSignals(False)
    
    def setup_modern_ui(self):
        """Setup the modern alerts interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Set dark theme for the entire widget with better contrast
        self.setStyleSheet("""
            QWidget {
                background-color: #0d0d12;
                color: #f0f0f5;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLabel {
                color: #e0e0e0;
                background: transparent;
            }
        """)
        
        # Header with filters and controls
        header_widget = self.create_modern_header()
        layout.addWidget(header_widget)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1f1f25;
                background-color: #0d0d12;
                border-radius: 8px;
                margin-top: 10px;
            }
            QTabBar::tab {
                background-color: #1a1a1f;
                color: #94a3b8;
                padding: 10px 24px;
                margin-right: 8px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid #1f1f25;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff4b4b, stop:1 #e14a4a);
                color: #ffffff;
                border: 1px solid #ff4b4b;
            }
            QTabBar::tab:hover:!selected {
                background-color: #25252b;
                color: #f1f5f9;
            }
            QTabBar {
                background-color: transparent;
            }
        """)
        
        # Alerts table tab
        self.alerts_tab = self.create_modern_alerts_table()
        self.tab_widget.addTab(self.alerts_tab, "🚨 All Alerts")
        
        # Statistics tab
        self.stats_tab = self.create_modern_statistics_tab()
        self.tab_widget.addTab(self.stats_tab, "📊 Statistics")
        
        layout.addWidget(self.tab_widget)
    
    def create_modern_header(self) -> QWidget:
        """Create modern header with filters and controls"""
        header = QWidget()
        header.setFixedHeight(120)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1a1f, stop:1 #121217);
                border-radius: 12px;
                border: 1px solid #1f1f25;
            }
            QLabel {
                color: #f1f5f9;
                font-weight: 600;
            }
            QComboBox, QDateEdit {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 8px 16px;
                color: #f8fafc;
                font-size: 13px;
                font-weight: 500;
                min-width: 140px;
            }
            QComboBox:hover, QDateEdit:hover {
                border-color: #ef4444;
                background-color: #1e293b;
            }
            QComboBox:focus, QDateEdit:focus {
                border-color: #f87171;
                background-color: #1e293b;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #94a3b8;
                margin-right: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                color: #f8fafc;
                selection-background-color: #ef4444;
                padding: 4px;
                outline: none;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff4b4b, stop:1 #ef4444);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff6b6b, stop:1 #f87171);
            }
            QPushButton:pressed {
                background: #dc2626;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Top row - Title and action buttons
        top_row = QHBoxLayout()
        
        title = QLabel("🚨 Alerts & Detections")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: 800;
                color: #ffffff;
                background: transparent;
                padding: 0px;
                letter-spacing: 0.5px;
            }
        """)
        
        # Action buttons
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent; border: none;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_alerts)
        
        export_btn = QPushButton("📤 Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QPushButton:hover {
                background-color: #363636;
                border-color: #606060;
            }
        """)
        export_btn.clicked.connect(self.export_alerts)
        
        cleanup_btn = QPushButton("🧹 Cleanup")
        cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QPushButton:hover {
                background-color: #363636;
                border-color: #606060;
            }
        """)
        cleanup_btn.clicked.connect(self.cleanup_alerts)
        
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(cleanup_btn)
        
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(actions_widget)
        
        # Bottom row - Filters
        filters_row = QHBoxLayout()
        filters_row.setSpacing(15)
        
        # Camera filter
        self.camera_filter = QComboBox()
        self.camera_filter.setPlaceholderText("Select Camera")
        self.camera_filter.addItem("All Cameras")
        self.camera_filter.currentTextChanged.connect(self.filter_alerts)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Fire", "Smoke", "People", "Motion", "System"])
        self.type_filter.currentTextChanged.connect(self.filter_alerts)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "Acknowledged", "Resolved", "False Alarm"])
        self.status_filter.currentTextChanged.connect(self.filter_alerts)
        
        # Date range
        date_widget = QWidget()
        date_widget.setStyleSheet("background: transparent; border: none;")
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0,0,0,0)
        date_layout.setSpacing(8)

        from_label = QLabel("From")
        from_label.setStyleSheet("color: #808080; font-size: 12px;")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setDisplayFormat("MMM d, yyyy")
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.filter_alerts)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("color: #808080; font-size: 12px;")
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("MMM d, yyyy")
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.filter_alerts)
        
        date_layout.addWidget(from_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.end_date)
        
        filters_row.addWidget(self.camera_filter)
        filters_row.addWidget(self.type_filter)
        filters_row.addWidget(self.status_filter)
        filters_row.addStretch()
        filters_row.addWidget(date_widget)
        
        layout.addLayout(top_row)
        layout.addLayout(filters_row)
        
        return header
    
    def create_modern_alerts_table(self) -> QWidget:
        """Create modern alerts table widget"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border: none;
                border-radius: 0px;
                margin: 0px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(9)
        self.alerts_table.setHorizontalHeaderLabels([
            "Time", "Camera", "Type", "Severity", "Description", 
            "Status", "Confidence", "Actions", "Footage"
        ])
        
        # Set column widths for better visibility
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Time
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Camera
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Type
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Severity
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Description
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Status
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Confidence
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Actions
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # Footage
        
        # Set specific column widths
        self.alerts_table.setColumnWidth(0, 140)  # Time
        self.alerts_table.setColumnWidth(1, 120)  # Camera
        self.alerts_table.setColumnWidth(2, 90)   # Type
        self.alerts_table.setColumnWidth(3, 100)  # Severity
        self.alerts_table.setColumnWidth(5, 110)  # Status
        self.alerts_table.setColumnWidth(6, 90)   # Confidence
        self.alerts_table.setColumnWidth(7, 150)  # Actions (Increased for clarity)
        self.alerts_table.setColumnWidth(8, 150)  # Footage (Increased for clarity)
        
        # Modern table styling with better visibility
        self.alerts_table.setStyleSheet("""
            QTableWidget {
                background-color: #0d0d12;
                color: #f1f5f9;
                border: none;
                gridline-color: transparent;
                selection-background-color: rgba(239, 68, 68, 0.1);
                selection-color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                outline: none;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #1f1f25;
                color: #e2e8f0;
            }
            QTableWidget::item:selected {
                background-color: rgba(239, 68, 68, 0.1);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #1e1e26;
            }
            QHeaderView::section {
                background-color: #0a0a0f;
                color: #64748b;
                padding: 14px 16px;
                border: none;
                border-bottom: 2px solid #1f1f25;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QScrollBar:vertical {
                background-color: #0d0d12;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #334155;
                border-radius: 6px;
                min-height: 30px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTableCornerButton::section {
                background-color: #0d0d12;
                border: none;
            }
        """)
        
        # Set table properties
        self.alerts_table.setAlternatingRowColors(False)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alerts_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.alerts_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.alerts_table.setShowGrid(False)
        self.alerts_table.setFrameShape(QFrame.NoFrame)
        self.alerts_table.verticalHeader().hide() # Remove row numbers for a cleaner look
        
        layout.addWidget(self.alerts_table)
        
        return widget
    
    def create_modern_statistics_tab(self) -> QWidget:
        """Create modern statistics tab"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Statistics cards container
        stats_container = QWidget()
        stats_container.setStyleSheet("background: transparent;")
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(0,0,0,0)
        
        # Total alerts card
        self.total_alerts_card = self.create_modern_stat_card("Total Alerts", "0", "#3498db", "📊")
        stats_layout.addWidget(self.total_alerts_card)
        
        # Active alerts card
        self.active_alerts_card = self.create_modern_stat_card("Active Alerts", "0", "#e74c3c", "🚨")
        stats_layout.addWidget(self.active_alerts_card)
        
        # Recent alerts card
        self.recent_alerts_card = self.create_modern_stat_card("Last 24h", "0", "#f39c12", "⏰")
        stats_layout.addWidget(self.recent_alerts_card)
        
        # False alarms card
        self.false_alarms_card = self.create_modern_stat_card("False Alarms", "0", "#95a5a6", "❌")
        stats_layout.addWidget(self.false_alarms_card)
        
        layout.addWidget(stats_container)
        
        # Alert breakdown section
        breakdown_widget = QWidget()
        breakdown_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-radius: 8px;
                border: 1px solid #333333;
            }
        """)
        breakdown_layout = QVBoxLayout(breakdown_widget)
        breakdown_layout.setContentsMargins(20, 20, 20, 20)
        
        breakdown_title = QLabel("📈 Alert Breakdown")
        breakdown_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 700;
                color: #ffffff;
                padding-bottom: 12px;
                background: transparent;
                border: none;
                letter-spacing: 0.5px;
            }
        """)
        breakdown_layout.addWidget(breakdown_title)
        
        # Alert type breakdown
        self.breakdown_container = QWidget()
        self.breakdown_container.setStyleSheet("background: transparent; border: none;")
        self.breakdown_layout = QHBoxLayout(self.breakdown_container)
        self.breakdown_layout.setSpacing(10)
        breakdown_layout.addWidget(self.breakdown_container)
        
        # Recent activity section
        activity_widget = QWidget()
        activity_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1f;
                border-radius: 12px;
                border: 1px solid #1f1f25;
            }
        """)
        activity_layout = QVBoxLayout(activity_widget)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        
        activity_title = QLabel("🕒 Recent Activity")
        activity_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 700;
                color: #ffffff;
                padding-bottom: 12px;
                background: transparent;
                border: none;
                letter-spacing: 0.5px;
            }
        """)
        activity_layout.addWidget(activity_title)
        
        # Recent alerts list
        self.recent_alerts_list = QWidget()
        self.recent_alerts_list.setStyleSheet("background: transparent; border: none;")
        self.recent_alerts_layout = QVBoxLayout(self.recent_alerts_list)
        self.recent_alerts_layout.setSpacing(5)
        
        # Scroll area for recent alerts
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.recent_alerts_list)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #333333;
                border-radius: 4px;
            }
        """)
        activity_layout.addWidget(scroll_area)
        
        layout.addWidget(breakdown_widget)
        layout.addWidget(activity_widget)
        layout.addStretch()
        
        return widget
    
    def create_modern_stat_card(self, title: str, value: str, color: str, icon: str) -> QWidget:
        """Create a modern statistics card with premium aesthetics"""
        card = QWidget()
        card.setFixedSize(220, 130)
        card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a1f, stop:1 #121217);
                border-radius: 16px;
                border: 1px solid #1f1f25;
            }}
            QWidget:hover {{
                border: 1px solid {color};
                background-color: #1e1e26;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Top row with icon and value
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0,0,0,0)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background: transparent;
                border: none;
            }
        """)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignRight)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 32px;
                font-weight: 800;
                background: transparent;
                border: none;
                font-family: 'Inter', 'Segoe UI', Arial;
            }}
        """)
        
        top_row.addWidget(icon_label)
        top_row.addStretch()
        top_row.addWidget(value_label)
        
        # Title
        title_label = QLabel(title.upper())
        title_label.setStyleSheet("""
            QLabel {
                color: #808080;
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                border: none;
                letter-spacing: 0.5px;
            }
        """)
        
        layout.addLayout(top_row)
        layout.addSpacing(5)
        layout.addWidget(title_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
    
    def darken_color(self, color: str) -> str:
        """Darken a hex color for gradient effect"""
        if color.startswith('#'):
            color = color[1:]
        
        # Convert hex to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Darken by 20%
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def connect_signals(self):
        """Connect signals"""
        self.alerts_manager.alert_created.connect(self.on_alert_created)
        self.alerts_manager.alert_updated.connect(self.on_alert_updated)
        self.alerts_manager.alert_deleted.connect(self.on_alert_deleted)
    
    def load_alerts(self):
        """Load alerts from database"""
        try:
            # Get filter values
            camera_id = self.camera_filter.currentData()
            type_filter = self.type_filter.currentText()
            status_filter = self.status_filter.currentText()
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            # Convert to datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            # Apply filters
            alert_type = None if type_filter == "All Types" else type_filter.lower()
            status = None if status_filter == "All Status" else status_filter.lower().replace(" ", "_")
            # Get alerts
            self.current_alerts = self.alerts_manager.get_alerts(
                camera_id=camera_id,
                alert_type=alert_type,
                status=status,
                start_date=start_datetime,
                end_date=end_datetime,
                limit=1000
            )
            self.update_alerts_table()
            self.update_statistics()
        except Exception as e:
            print(f"❌ Error loading alerts: {e}")
    
    def update_alerts_table(self):
        """Update the modern alerts table with improved row visibility"""
        self.alerts_table.setRowCount(len(self.current_alerts))
        self.alerts_table.verticalHeader().setDefaultSectionSize(60) # Taller rows
        
        for row, alert in enumerate(self.current_alerts):
            # Time
            time_str = datetime.fromtimestamp(alert.timestamp).strftime("%m/%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            time_item.setToolTip(datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S"))
            self.alerts_table.setItem(row, 0, time_item)
            
            # Camera
            camera_item = QTableWidgetItem(alert.camera_name)
            self.alerts_table.setItem(row, 1, camera_item)
            
            # Type with emoji
            type_emoji = self.get_type_emoji(alert.alert_type)
            type_item = QTableWidgetItem(f"{type_emoji} {alert.alert_type.title()}")
            type_item.setToolTip(f"Alert Type: {alert.alert_type}")
            self.alerts_table.setItem(row, 2, type_item)
            
            # Severity badge
            severity_widget = self.create_badge_widget(alert.severity.upper(), self.get_severity_color(alert.severity))
            self.alerts_table.setCellWidget(row, 3, severity_widget)
            
            # Description (truncated for better display)
            description = alert.description
            if len(description) > 50:
                description = description[:47] + "..."
            desc_item = QTableWidgetItem(description)
            desc_item.setToolTip(alert.description)
            self.alerts_table.setItem(row, 4, desc_item)
            
            # Status badge
            status_display = alert.status.replace('_', ' ').upper()
            status_widget = self.create_badge_widget(status_display, self.get_status_color(alert.status))
            self.alerts_table.setCellWidget(row, 5, status_widget)
            
            # Confidence with percentage
            confidence_text = f"{alert.confidence:.1%}"
            confidence_item = QTableWidgetItem(confidence_text)
            confidence_item.setToolTip(f"Detection Confidence: {alert.confidence:.3f}")
            self.alerts_table.setItem(row, 6, confidence_item)
            
            # Actions with modern buttons
            actions_widget = self.create_action_buttons(alert)
            self.alerts_table.setCellWidget(row, 7, actions_widget)
            
            # Footage with modern buttons
            footage_widget = self.create_footage_buttons(alert)
            self.alerts_table.setCellWidget(row, 8, footage_widget)

    def create_badge_widget(self, text: str, color: str) -> QWidget:
        """Create a pill-shaped badge for status or severity"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        
        # Darken the background color for the badge but keep it vibrant
        bg_color = QColor(color)
        bg_style = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 50)"
        
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_style};
                color: {color};
                border: 1px solid {color};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }}
        """)
        
        layout.addWidget(label)
        return widget
    
    def get_type_emoji(self, alert_type: str) -> str:
        """Get emoji for alert type"""
        emoji_map = {
            'fire': '🔥',
            'smoke': '💨',
            'people': '👥',
            'motion': '🏃',
            'system': '⚙️'
        }
        return emoji_map.get(alert_type.lower(), '⚠️')
    
    def get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        color_map = {
            'critical': '#dc3545',  # Red
            'high': '#fd7e14',      # Orange
            'medium': '#ffc107',    # Yellow
            'low': '#28a745'        # Green
        }
        return color_map.get(severity.lower(), '#6c757d')
    
    def get_status_color(self, status: str) -> str:
        """Get color for status"""
        color_map = {
            'active': '#dc3545',        # Red
            'acknowledged': '#ffc107',  # Yellow
            'resolved': '#28a745',      # Green
            'false_alarm': '#6c757d'    # Gray
        }
        return color_map.get(status.lower(), '#6c757d')
    
    def create_action_buttons(self, alert) -> QWidget:
        """Create a clean dropdown menu for alert actions"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Actions Dropdown Button
        actions_btn = QPushButton("Actions ▾")
        actions_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3b4252;
                border-color: #616e88;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)
        
        # Create the menu
        menu = QMenu(actions_btn)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f1f5f9;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #334155;
                margin: 4px 8px;
            }
        """)
        
        if alert.status == 'active':
            # Acknowledge Action
            ack_action = QAction("✓  Acknowledge", self)
            ack_action.triggered.connect(lambda: self.acknowledge_alert(alert.id))
            menu.addAction(ack_action)
            
            # Resolve Action
            resolve_action = QAction("✅  Resolve", self)
            resolve_action.triggered.connect(lambda: self.resolve_alert(alert.id))
            menu.addAction(resolve_action)
            
            # False Alarm Action
            false_action = QAction("❌  False Alarm", self)
            false_action.triggered.connect(lambda: self.mark_false_alarm(alert.id))
            menu.addAction(false_action)
            
            menu.addSeparator()
            
        # Delete Action (Red highlight)
        delete_action = QAction("🗑️  Delete", self)
        delete_action.triggered.connect(lambda: self.delete_alert(alert.id))
        menu.addAction(delete_action)
        
        actions_btn.setMenu(menu)
        layout.addWidget(actions_btn)
        
        return widget
    
    def create_footage_buttons(self, alert) -> QWidget:
        """Create modern footage buttons for an alert"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        button_style = """
            QPushButton {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                padding: 6px 10px;
                min-width: 40px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
        """
        
        if alert.footage_path and os.path.exists(alert.footage_path):
            # View button
            view_btn = QPushButton("👁️")
            view_btn.setStyleSheet(button_style)
            view_btn.setToolTip("View Footage")
            view_btn.clicked.connect(lambda: self.view_footage(alert.footage_path))
            layout.addWidget(view_btn)
            
            # Download button
            download_btn = QPushButton("⬇️")
            download_btn.setStyleSheet(button_style)
            download_btn.setToolTip("Download Footage")
            download_btn.clicked.connect(lambda: self.download_footage(alert.footage_path))
            layout.addWidget(download_btn)
        else:
            # No footage label
            no_footage = QLabel("No footage")
            no_footage.setStyleSheet("""
                QLabel {
                    color: #bbbbbb;
                    font-size: 11px;
                    font-weight: 500;
                    background: transparent;
                    padding: 8px;
                }
            """)
            layout.addWidget(no_footage)
        
        return widget
    
    def update_statistics(self):
        """Update modern statistics display"""
        try:
            stats = self.alerts_manager.get_alert_statistics()
            
            # Update stat cards
            self.total_alerts_card.value_label.setText(str(stats.get('total_alerts', 0)))
            self.active_alerts_card.value_label.setText(str(stats.get('active_alerts', 0)))
            self.recent_alerts_card.value_label.setText(str(stats.get('recent_alerts', 0)))
            
            # Calculate false alarms
            false_alarms = sum(1 for alert in self.current_alerts if alert.status == 'false_alarm')
            self.false_alarms_card.value_label.setText(str(false_alarms))
            
            # Update breakdown charts
            self.update_breakdown_display(stats)
            
            # Update recent activity
            self.update_recent_activity()
            
        except Exception as e:
            print(f"❌ Error updating statistics: {e}")
    
    def update_breakdown_display(self, stats):
        """Update the alert breakdown display"""
        # Clear existing breakdown widgets
        for i in reversed(range(self.breakdown_layout.count())):
            child = self.breakdown_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add breakdown by type
        alerts_by_type = stats.get('alerts_by_type', {})
        for alert_type, count in alerts_by_type.items():
            if count > 0:
                breakdown_card = self.create_breakdown_card(alert_type, count)
                self.breakdown_layout.addWidget(breakdown_card)
        
        if not alerts_by_type:
            no_data_label = QLabel("No alert data available")
            no_data_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 14px;
                    padding: 20px;
                    background: transparent;
                }
            """)
            self.breakdown_layout.addWidget(no_data_label)
    
    def create_breakdown_card(self, alert_type: str, count: int) -> QWidget:
        """Create a breakdown card for alert types"""
        card = QWidget()
        card.setFixedSize(120, 80)
        card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a1f, stop:1 #121217);
                border-radius: 12px;
                border: 1px solid #1f1f25;
            }
            QWidget:hover {
                background-color: #1e1e26;
                border-color: #334155;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Type with emoji
        type_emoji = self.get_type_emoji(alert_type)
        type_label = QLabel(f"{type_emoji} {alert_type.title()}")
        type_label.setAlignment(Qt.AlignCenter)
        type_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: 500;
                background: transparent;
            }
        """)
        
        # Count
        count_label = QLabel(str(count))
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("""
            QLabel {
                color: #ff3333;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        layout.addWidget(type_label)
        layout.addWidget(count_label)
        
        return card
    
    def update_recent_activity(self):
        """Update the recent activity display"""
        # Clear existing activity widgets
        for i in reversed(range(self.recent_alerts_layout.count())):
            child = self.recent_alerts_layout.takeAt(i).widget()
            if child:
                child.deleteLater()
        
        # Get recent alerts (last 10)
        recent_alerts = sorted(self.current_alerts, key=lambda x: x.timestamp, reverse=True)[:10]
        
        if recent_alerts:
            for alert in recent_alerts:
                activity_item = self.create_activity_item(alert)
                self.recent_alerts_layout.addWidget(activity_item)
        else:
            no_activity_label = QLabel("No recent activity")
            no_activity_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 12px;
                    padding: 10px;
                    background: transparent;
                }
            """)
            self.recent_alerts_layout.addWidget(no_activity_label)
    
    def create_activity_item(self, alert) -> QWidget:
        """Create an activity item for recent alerts"""
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background-color: #1a1a1f;
                border-radius: 8px;
                margin: 2px;
                padding: 8px;
                border: 1px solid #1f1f25;
            }
            QWidget:hover {
                background-color: #1e1e26;
                border-color: #334155;
            }
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Type emoji
        type_emoji = self.get_type_emoji(alert.alert_type)
        emoji_label = QLabel(type_emoji)
        emoji_label.setFixedSize(20, 20)
        emoji_label.setStyleSheet("background: transparent; font-size: 14px;")
        
        # Alert info
        time_str = datetime.fromtimestamp(alert.timestamp).strftime("%H:%M")
        info_text = f"{alert.camera_name} - {alert.alert_type.title()}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                background: transparent;
            }
        """)
        
        # Time
        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                background: transparent;
            }
        """)
        
        layout.addWidget(emoji_label)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(time_label)
        
        return item
    
    def filter_alerts(self):
        """Filter alerts based on current filter settings"""
        self.load_alerts()
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        success = self.alerts_manager.acknowledge_alert(alert_id, "current_user")
        if success:
            self.load_alerts()
        else:
            QMessageBox.warning(self, "Error", "Failed to acknowledge alert")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        success = self.alerts_manager.resolve_alert(alert_id, "current_user")
        if success:
            self.load_alerts()
        else:
            QMessageBox.warning(self, "Error", "Failed to resolve alert")
    
    def mark_false_alarm(self, alert_id: str):
        """Mark alert as false alarm"""
        success = self.alerts_manager.mark_false_alarm(alert_id, "current_user")
        if success:
            self.load_alerts()
        else:
            QMessageBox.warning(self, "Error", "Failed to mark as false alarm")
    
    def delete_alert(self, alert_id: str):
        """Delete an alert"""
        reply = QMessageBox.question(
            self, 'Delete Alert',
            'Are you sure you want to delete this alert?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.alerts_manager.delete_alert(alert_id)
            if success:
                self.load_alerts()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete alert")
    
    def view_footage(self, footage_path: str):
        """View footage for an alert"""
        try:
            # Open footage in default video player
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                subprocess.run(['start', footage_path], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', footage_path])
            else:  # Linux
                subprocess.run(['xdg-open', footage_path])
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open footage: {str(e)}")
    
    def download_footage(self, footage_path: str):
        """Download footage for an alert"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Footage", 
                os.path.basename(footage_path),
                "Video Files (*.mp4 *.avi *.mov)"
            )
            
            if save_path:
                import shutil
                shutil.copy2(footage_path, save_path)
                QMessageBox.information(self, "Success", f"Footage saved to: {save_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to download footage: {str(e)}")
    
    def export_alerts(self):
        """Export alerts to CSV"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Alerts", 
                f"alerts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([
                        'ID', 'Timestamp', 'Camera ID', 'Camera Name', 'Alert Type',
                        'Severity', 'Confidence', 'Description', 'Status',
                        'Acknowledged By', 'Acknowledged At', 'Resolved By', 'Resolved At'
                    ])
                    
                    # Write data
                    for alert in self.current_alerts:
                        writer.writerow([
                            alert.id,
                            datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                            alert.camera_id,
                            alert.camera_name,
                            alert.alert_type,
                            alert.severity,
                            alert.confidence,
                            alert.description,
                            alert.status,
                            alert.acknowledged_by or '',
                            datetime.fromtimestamp(alert.acknowledged_at).strftime('%Y-%m-%d %H:%M:%S') if alert.acknowledged_at else '',
                            alert.resolved_by or '',
                            datetime.fromtimestamp(alert.resolved_at).strftime('%Y-%m-%d %H:%M:%S') if alert.resolved_at else ''
                        ])
                
                QMessageBox.information(self, "Success", f"Alerts exported to: {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export alerts: {str(e)}")
    
    def cleanup_alerts(self):
        """Cleanup old alerts"""
        reply = QMessageBox.question(
            self, 'Cleanup Alerts',
            'This will delete old alerts based on retention policy. Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.alerts_manager.cleanup_old_alerts()
            self.load_alerts()
            QMessageBox.information(self, "Success", "Old alerts cleaned up successfully")
    
    def on_alert_created(self, alert: Alert):
        """Handle new alert created"""
        self.load_alerts()
    
    def on_alert_updated(self, alert: Alert):
        """Handle alert updated"""
        self.load_alerts()
    
    def on_alert_deleted(self, alert_id: str):
        """Handle alert deleted"""
        self.load_alerts()
