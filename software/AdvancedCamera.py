import sys
import time
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QListWidget, QListWidgetItem, QTabWidget, QGroupBox, 
                           QCheckBox, QTimeEdit, QSpinBox, QSlider, QMessageBox,
                           QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QPainter


class ModernCard(QFrame):
    """Modern card widget with gradient background and shadow"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernCard")
        self.setStyleSheet("""
            QFrame#modernCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2a2d3e, stop:1 #1f2335);
                border: 1px solid #3a3f55;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        self.setGraphicsEffect(self.create_shadow_effect())
        
    def create_shadow_effect(self):
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        return shadow


class ModernButton(QPushButton):
    """Modern button with gradient and hover effects"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("modernButton")
        self.setStyleSheet("""
            QPushButton#modernButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                padding: 12px 24px;
                min-height: 20px;
            }
            QPushButton#modernButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4190);
                transform: translateY(-1px);
            }
            QPushButton#modernButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5fc8, stop:1 #5a3180);
            }
        """)


class ModernCheckBox(QCheckBox):
    """Modern checkbox with custom styling"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 500;
                spacing: 12px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #4a5568;
                border-radius: 6px;
                background: #2d3748;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)


class ModernSlider(QSlider):
    """Modern slider with custom styling"""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background: #2d3748;
                border-radius: 4px;
                margin: 0px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                border: 2px solid #667eea;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f7fafc, stop:1 #edf2f7);
            }
        """)


class AdvancedCameraManagementPage(QWidget):
    """Advanced camera management with time-based detection schedules"""
    
    def __init__(self, camera_manager, config_manager):
        super().__init__()
        self.camera_manager = camera_manager
        self.config_manager = config_manager
        self.setup_ui()
        self.load_camera_schedules()
        
    def setup_ui(self):
        # Set main widget background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1419, stop:1 #1a202c);
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Header with modern design
        self.create_modern_header(layout)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(25)
        
        # Left panel - Camera list
        self.create_camera_list_panel(content_layout)
        
        # Right panel - Schedule configuration
        self.create_schedule_config_panel(content_layout)
        
        layout.addWidget(content_widget)
        
    def create_modern_header(self, parent_layout):
        """Create modern header with gradient background"""
        header_card = ModernCard()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(25, 20, 25, 20)
        
        # Title with modern typography
        title = QLabel("🎥 Advanced Camera Management")
        title.setStyleSheet("""
            color: #f7fafc;
            font-size: 28px;
            font-weight: 700;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        """)
        
        subtitle = QLabel("Time-Based Detection Schedules")
        subtitle.setStyleSheet("""
            color: #a0aec0;
            font-size: 16px;
            font-weight: 400;
            margin-top: 5px;
        """)
        
        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        # Action buttons
        refresh_btn = ModernButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_schedules)
        
        save_all_btn = ModernButton("💾 Save All")
        save_all_btn.clicked.connect(self.save_all_schedules)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(save_all_btn)
        
        parent_layout.addWidget(header_card)
        
    def create_camera_list_panel(self, parent_layout):
        """Create the camera list panel with modern design"""
        panel = ModernCard()
        panel.setFixedWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title with icon
        title = QLabel("📹 Connected Cameras")
        title.setStyleSheet("""
            color: #f7fafc;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Camera list with modern styling
        self.camera_list = QListWidget()
        self.camera_list.setStyleSheet("""
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a202c, stop:1 #2d3748);
                border: 1px solid #4a5568;
                border-radius: 12px;
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 500;
                padding: 8px;
            }
            QListWidget::item {
                background: transparent;
                padding: 16px;
                margin: 4px 0px;
                border-radius: 8px;
                border: none;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
            }
        """)
        self.camera_list.itemClicked.connect(self.on_camera_selected)
        layout.addWidget(self.camera_list)
        
        parent_layout.addWidget(panel)
        
    def create_schedule_config_panel(self, parent_layout):
        """Create the schedule configuration panel with modern design"""
        panel = ModernCard()
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Title
        title = QLabel("⏰ Detection Schedule Configuration")
        title.setStyleSheet("""
            color: #f7fafc;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Camera info with modern styling
        self.camera_info_label = QLabel("Select a camera to configure its detection schedule")
        self.camera_info_label.setStyleSheet("""
            color: #667eea;
            font-size: 14px;
            font-weight: 600;
            padding: 16px;
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 12px;
            margin-bottom: 20px;
        """)
        layout.addWidget(self.camera_info_label)
        
        # Detection type tabs with modern styling
        self.create_detection_tabs(layout)
        
        parent_layout.addWidget(panel)
        
    def create_detection_tabs(self, parent_layout):
        """Create tabs for different detection types with modern styling"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4a5568;
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a202c, stop:1 #2d3748);
                padding: 20px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2d3748, stop:1 #4a5568);
                color: #a0aec0;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5568, stop:1 #2d3748);
                color: #e2e8f0;
            }
        """)
        
        # People Detection Tab
        self.people_detection_tab = self.create_people_detection_tab()
        self.tab_widget.addTab(self.people_detection_tab, "👥 People Detection")
        
        # Fire Detection Tab
        self.fire_detection_tab = self.create_fire_detection_tab()
        self.tab_widget.addTab(self.fire_detection_tab, "🔥 Fire/Smoke Detection")
        
        # Sensitivity Settings Tab
        self.sensitivity_tab = self.create_sensitivity_tab()
        self.tab_widget.addTab(self.sensitivity_tab, "🎛️ Sensitivity Settings")
        
        parent_layout.addWidget(self.tab_widget)
        
    def create_modern_group_box(self, title):
        """Create a modern group box with gradient styling"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: #f7fafc;
                font-size: 16px;
                font-weight: 700;
                border: 2px solid #4a5568;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(45, 55, 72, 0.5), stop:1 rgba(26, 32, 44, 0.5));
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 6px;
                color: #ffffff;
            }
        """)
        return group
        
    def create_people_detection_tab(self):
        """Create people detection configuration tab with modern design"""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2d3748;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #667eea;
            }
        """)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Enable/Disable
        enable_group = self.create_modern_group_box("People Detection Control")
        enable_layout = QHBoxLayout(enable_group)
        
        self.people_enabled_checkbox = ModernCheckBox("Enable People Detection")
        self.people_enabled_checkbox.stateChanged.connect(self.on_people_detection_toggled)
        
        enable_layout.addWidget(self.people_enabled_checkbox)
        enable_layout.addStretch()
        layout.addWidget(enable_group)
        
        # Time Schedule
        time_group = self.create_modern_group_box("Active Time Schedule")
        time_layout = QVBoxLayout(time_group)
        
        # 24/7 option
        self.people_24_7_checkbox = ModernCheckBox("24/7 Active (Always On)")
        self.people_24_7_checkbox.stateChanged.connect(self.on_people_24_7_toggled)
        time_layout.addWidget(self.people_24_7_checkbox)
        
        # Custom time range
        time_range_widget = QWidget()
        time_range_layout = QHBoxLayout(time_range_widget)
        time_range_layout.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("Start Time:")
        start_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        time_range_layout.addWidget(start_label)
        
        self.people_start_time = QTimeEdit()
        self.people_start_time.setStyleSheet("""
            QTimeEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QTimeEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        time_range_layout.addWidget(self.people_start_time)
        
        end_label = QLabel("End Time:")
        end_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        time_range_layout.addWidget(end_label)
        
        self.people_end_time = QTimeEdit()
        self.people_end_time.setStyleSheet("""
            QTimeEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QTimeEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        time_range_layout.addWidget(self.people_end_time)
        
        time_layout.addWidget(time_range_widget)
        layout.addWidget(time_group)
        
        # Alarm Settings
        alarm_group = self.create_modern_group_box("Alarm Configuration")
        alarm_layout = QVBoxLayout(alarm_group)
        
        self.people_alarm_enabled = ModernCheckBox("Enable Alarms")
        alarm_layout.addWidget(self.people_alarm_enabled)
        
        # Minimum people count for alarm
        people_count_widget = QWidget()
        people_count_layout = QHBoxLayout(people_count_widget)
        people_count_layout.setContentsMargins(0, 0, 0, 0)
        
        count_label = QLabel("Min People for Alarm:")
        count_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        people_count_layout.addWidget(count_label)
        
        self.people_min_count = QSpinBox()
        self.people_min_count.setRange(1, 10)
        self.people_min_count.setValue(1)
        self.people_min_count.setStyleSheet("""
            QSpinBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QSpinBox:focus {
                border: 2px solid #667eea;
            }
        """)
        people_count_layout.addWidget(self.people_min_count)
        
        alarm_layout.addWidget(people_count_widget)
        layout.addWidget(alarm_group)
        
        # Save button
        save_btn = ModernButton("💾 Save People Detection Settings")
        save_btn.clicked.connect(self.save_people_detection_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)
        return tab
        
    def create_fire_detection_tab(self):
        """Create fire detection configuration tab with modern design"""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2d3748;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #667eea;
            }
        """)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Enable/Disable
        enable_group = self.create_modern_group_box("Fire/Smoke Detection Control")
        enable_layout = QHBoxLayout(enable_group)
        
        self.fire_enabled_checkbox = ModernCheckBox("Enable Fire/Smoke Detection")
        self.fire_enabled_checkbox.stateChanged.connect(self.on_fire_detection_toggled)
        
        enable_layout.addWidget(self.fire_enabled_checkbox)
        enable_layout.addStretch()
        layout.addWidget(enable_group)
        
        # Time Schedule
        time_group = self.create_modern_group_box("Active Time Schedule")
        time_layout = QVBoxLayout(time_group)
        
        # 24/7 option
        self.fire_24_7_checkbox = ModernCheckBox("24/7 Active (Always On)")
        self.fire_24_7_checkbox.stateChanged.connect(self.on_fire_24_7_toggled)
        time_layout.addWidget(self.fire_24_7_checkbox)
        
        # Custom time range
        time_range_widget = QWidget()
        time_range_layout = QHBoxLayout(time_range_widget)
        time_range_layout.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("Start Time:")
        start_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        time_range_layout.addWidget(start_label)
        
        self.fire_start_time = QTimeEdit()
        self.fire_start_time.setStyleSheet("""
            QTimeEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QTimeEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        time_range_layout.addWidget(self.fire_start_time)
        
        end_label = QLabel("End Time:")
        end_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        time_range_layout.addWidget(end_label)
        
        self.fire_end_time = QTimeEdit()
        self.fire_end_time.setStyleSheet("""
            QTimeEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QTimeEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        time_range_layout.addWidget(self.fire_end_time)
        
        time_layout.addWidget(time_range_widget)
        layout.addWidget(time_group)
        
        # Detection Types
        detection_group = self.create_modern_group_box("Detection Types")
        detection_layout = QVBoxLayout(detection_group)
        
        self.fire_detection_checkbox = ModernCheckBox("Fire Detection")
        self.fire_detection_checkbox.setChecked(True)
        detection_layout.addWidget(self.fire_detection_checkbox)
        
        self.smoke_detection_checkbox = ModernCheckBox("Smoke Detection")
        self.smoke_detection_checkbox.setChecked(True)
        detection_layout.addWidget(self.smoke_detection_checkbox)
        
        layout.addWidget(detection_group)
        
        # Alarm Settings
        alarm_group = self.create_modern_group_box("Alarm Configuration")
        alarm_layout = QVBoxLayout(alarm_group)
        
        self.fire_alarm_enabled = ModernCheckBox("Enable Alarms")
        self.fire_alarm_enabled.setChecked(True)
        alarm_layout.addWidget(self.fire_alarm_enabled)
        
        # Confidence threshold
        confidence_widget = QWidget()
        confidence_layout = QHBoxLayout(confidence_widget)
        confidence_layout.setContentsMargins(0, 0, 0, 0)
        
        conf_label = QLabel("Min Confidence:")
        conf_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        confidence_layout.addWidget(conf_label)
        
        self.fire_confidence_threshold = QSpinBox()
        self.fire_confidence_threshold.setRange(50, 95)
        self.fire_confidence_threshold.setValue(70)
        self.fire_confidence_threshold.setSuffix("%")
        self.fire_confidence_threshold.setStyleSheet("""
            QSpinBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QSpinBox:focus {
                border: 2px solid #667eea;
            }
        """)
        confidence_layout.addWidget(self.fire_confidence_threshold)
        
        alarm_layout.addWidget(confidence_widget)
        layout.addWidget(alarm_group)
        
        # Save button
        save_btn = ModernButton("💾 Save Fire Detection Settings")
        save_btn.clicked.connect(self.save_fire_detection_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)
        return tab
        
    def create_sensitivity_tab(self):
        """Create sensitivity settings tab with modern design"""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2d3748;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #667eea;
            }
        """)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # People Detection Sensitivity
        people_sensitivity_group = self.create_modern_group_box("People Detection Sensitivity")
        people_layout = QVBoxLayout(people_sensitivity_group)
        
        # Detection confidence
        people_conf_widget = QWidget()
        people_conf_layout = QHBoxLayout(people_conf_widget)
        people_conf_layout.setContentsMargins(0, 0, 0, 0)
        
        conf_label = QLabel("Detection Confidence:")
        conf_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        people_conf_layout.addWidget(conf_label)
        
        self.people_confidence_slider = ModernSlider(Qt.Horizontal)
        self.people_confidence_slider.setRange(30, 95)
        self.people_confidence_slider.setValue(50)
        people_conf_layout.addWidget(self.people_confidence_slider)
        
        self.people_confidence_label = QLabel("50%")
        self.people_confidence_label.setStyleSheet("""
            color: #667eea;
            font-size: 16px;
            font-weight: 700;
            min-width: 50px;
            text-align: center;
        """)
        self.people_confidence_slider.valueChanged.connect(
            lambda v: self.people_confidence_label.setText(f"{v}%")
        )
        people_conf_layout.addWidget(self.people_confidence_label)
        
        people_layout.addWidget(people_conf_widget)
        layout.addWidget(people_sensitivity_group)
        
        # Fire Detection Sensitivity
        fire_sensitivity_group = self.create_modern_group_box("Fire/Smoke Detection Sensitivity")
        fire_layout = QVBoxLayout(fire_sensitivity_group)
        
        # Detection confidence
        fire_conf_widget = QWidget()
        fire_conf_layout = QHBoxLayout(fire_conf_widget)
        fire_conf_layout.setContentsMargins(0, 0, 0, 0)
        
        conf_label = QLabel("Detection Confidence:")
        conf_label.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: 600;")
        fire_conf_layout.addWidget(conf_label)
        
        self.fire_confidence_slider = ModernSlider(Qt.Horizontal)
        self.fire_confidence_slider.setRange(30, 95)
        self.fire_confidence_slider.setValue(70)
        fire_conf_layout.addWidget(self.fire_confidence_slider)
        
        self.fire_confidence_label = QLabel("70%")
        self.fire_confidence_label.setStyleSheet("""
            color: #f56565;
            font-size: 16px;
            font-weight: 700;
            min-width: 50px;
            text-align: center;
        """)
        self.fire_confidence_slider.valueChanged.connect(
            lambda v: self.fire_confidence_label.setText(f"{v}%")
        )
        fire_conf_layout.addWidget(self.fire_confidence_label)
        
        fire_layout.addWidget(fire_conf_widget)
        layout.addWidget(fire_sensitivity_group)
        
        # Save button
        save_btn = ModernButton("💾 Save Sensitivity Settings")
        save_btn.clicked.connect(self.save_sensitivity_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)
        return tab
        
    def load_camera_schedules(self):
        """Load camera schedules from configuration"""
        cameras = self.config_manager.load_cameras()
        self.camera_list.clear()
        
        for camera_id, camera_data in cameras.items():
            item = QListWidgetItem(f"📹 {camera_data['name']}")
            item.setData(Qt.UserRole, camera_id)
            self.camera_list.addItem(item)
            
    def on_camera_selected(self, item):
        """Handle camera selection"""
        camera_id = item.data(Qt.UserRole)
        camera_data = self.config_manager.get_camera(camera_id)
        
        if camera_data:
            self.camera_info_label.setText(f"Configuring: {camera_data['name']} ({camera_id})")
            self.load_camera_settings(camera_id)
            
    def load_camera_settings(self, camera_id):
        """Load settings for selected camera"""
        # Load people detection settings
        people_settings = self.config_manager.get_config(f"cameras.{camera_id}.people_detection", {})
        self.people_enabled_checkbox.setChecked(people_settings.get("enabled", False))
        self.people_24_7_checkbox.setChecked(people_settings.get("always_on", False))
        self.people_alarm_enabled.setChecked(people_settings.get("alarm_enabled", True))
        self.people_min_count.setValue(people_settings.get("min_count", 1))
        
        # Load time settings
        start_time = people_settings.get("start_time", "20:00")
        end_time = people_settings.get("end_time", "06:00")
        self.people_start_time.setTime(QTime.fromString(start_time, "HH:mm"))
        self.people_end_time.setTime(QTime.fromString(end_time, "HH:mm"))
        
        # Load fire detection settings
        fire_settings = self.config_manager.get_config(f"cameras.{camera_id}.fire_detection", {})
        self.fire_enabled_checkbox.setChecked(fire_settings.get("enabled", False))
        self.fire_24_7_checkbox.setChecked(fire_settings.get("always_on", False))
        self.fire_alarm_enabled.setChecked(fire_settings.get("alarm_enabled", True))
        self.fire_detection_checkbox.setChecked(fire_settings.get("fire_enabled", True))
        self.smoke_detection_checkbox.setChecked(fire_settings.get("smoke_enabled", True))
        self.fire_confidence_threshold.setValue(fire_settings.get("confidence_threshold", 70))
        
        # Load time settings
        start_time = fire_settings.get("start_time", "00:00")
        end_time = fire_settings.get("end_time", "23:59")
        self.fire_start_time.setTime(QTime.fromString(start_time, "HH:mm"))
        self.fire_end_time.setTime(QTime.fromString(end_time, "HH:mm"))
        
        # Load sensitivity settings
        sensitivity_settings = self.config_manager.get_config(f"cameras.{camera_id}.sensitivity", {})
        self.people_confidence_slider.setValue(sensitivity_settings.get("people_confidence", 50))
        self.fire_confidence_slider.setValue(sensitivity_settings.get("fire_confidence", 70))
        
        # Store current camera ID
        self.current_camera_id = camera_id
        
    def on_people_detection_toggled(self, state):
        """Handle people detection toggle"""
        if state == Qt.Checked:
            self.people_24_7_checkbox.setEnabled(True)
            self.people_start_time.setEnabled(True)
            self.people_end_time.setEnabled(True)
        else:
            self.people_24_7_checkbox.setEnabled(False)
            self.people_start_time.setEnabled(False)
            self.people_end_time.setEnabled(False)
            
    def on_fire_detection_toggled(self, state):
        """Handle fire detection toggle"""
        if state == Qt.Checked:
            self.fire_24_7_checkbox.setEnabled(True)
            self.fire_start_time.setEnabled(True)
            self.fire_end_time.setEnabled(True)
        else:
            self.fire_24_7_checkbox.setEnabled(False)
            self.fire_start_time.setEnabled(False)
            self.fire_end_time.setEnabled(False)
            
    def on_people_24_7_toggled(self, state):
        """Handle people 24/7 toggle"""
        enabled = state == Qt.Checked
        self.people_start_time.setEnabled(not enabled)
        self.people_end_time.setEnabled(not enabled)
        
    def on_fire_24_7_toggled(self, state):
        """Handle fire 24/7 toggle"""
        enabled = state == Qt.Checked
        self.fire_start_time.setEnabled(not enabled)
        self.fire_end_time.setEnabled(not enabled)
        
    def save_people_detection_settings(self):
        """Save people detection settings"""
        if hasattr(self, 'current_camera_id'):
            settings = {
                "enabled": self.people_enabled_checkbox.isChecked(),
                "always_on": self.people_24_7_checkbox.isChecked(),
                "alarm_enabled": self.people_alarm_enabled.isChecked(),
                "min_count": self.people_min_count.value(),
                "start_time": self.people_start_time.time().toString("HH:mm"),
                "end_time": self.people_end_time.time().toString("HH:mm")
            }
            
            self.config_manager.update_config(f"cameras.{self.current_camera_id}.people_detection", settings)
            
            # Update camera manager
            if self.camera_manager:
                self.camera_manager.enable_people_detection(self.current_camera_id, settings["enabled"])
                
            QMessageBox.information(self, "Success", "People detection settings saved successfully!")
            
    def save_fire_detection_settings(self):
        """Save fire detection settings"""
        if hasattr(self, 'current_camera_id'):
            settings = {
                "enabled": self.fire_enabled_checkbox.isChecked(),
                "always_on": self.fire_24_7_checkbox.isChecked(),
                "alarm_enabled": self.fire_alarm_enabled.isChecked(),
                "fire_enabled": self.fire_detection_checkbox.isChecked(),
                "smoke_enabled": self.smoke_detection_checkbox.isChecked(),
                "confidence_threshold": self.fire_confidence_threshold.value(),
                "start_time": self.fire_start_time.time().toString("HH:mm"),
                "end_time": self.fire_end_time.time().toString("HH:mm")
            }
            
            self.config_manager.update_config(f"cameras.{self.current_camera_id}.fire_detection", settings)
            
            # Update camera manager
            if self.camera_manager:
                self.camera_manager.enable_fire_smoke_detection(self.current_camera_id, settings["enabled"])
                
            QMessageBox.information(self, "Success", "Fire detection settings saved successfully!")
            
    def save_sensitivity_settings(self):
        """Save sensitivity settings"""
        if hasattr(self, 'current_camera_id'):
            settings = {
                "people_confidence": self.people_confidence_slider.value(),
                "fire_confidence": self.fire_confidence_slider.value()
            }
            
            self.config_manager.update_config(f"cameras.{self.current_camera_id}.sensitivity", settings)
            QMessageBox.information(self, "Success", "Sensitivity settings saved successfully!")
            
    def save_all_schedules(self):
        """Save all schedules for all cameras"""
        self.save_people_detection_settings()
        self.save_fire_detection_settings()
        self.save_sensitivity_settings()
        QMessageBox.information(self, "Success", "All settings saved successfully!")
        
    def refresh_schedules(self):
        """Refresh camera schedules"""
        self.load_camera_schedules()
        if hasattr(self, 'current_camera_id'):
            self.load_camera_settings(self.current_camera_id)
        QMessageBox.information(self, "Success", "Schedules refreshed successfully!")
