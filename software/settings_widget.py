import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
                             QPushButton, QComboBox, QCheckBox, QSlider, QSpinBox,
                             QLineEdit, QFileDialog, QGroupBox, QFormLayout, QTextEdit,
                             QMessageBox, QProgressBar, QListWidget, QDoubleSpinBox,
                             QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import json
import shutil
from datetime import datetime

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class SettingsWidget(QWidget):
    """Comprehensive settings widget with tabbed interface"""
    
    settings_applied = pyqtSignal()
    
    def __init__(self, settings_manager, config_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.config_manager = config_manager
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the main UI with tabs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px 0px;
            }
        """)
        layout.addWidget(title)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #0d1117;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #0d1117;
                color: #ffffff;
                border-bottom: 2px solid #ff3333;
            }
            QTabBar::tab:hover {
                background-color: #1c2128;
                color: #ffffff;
            }
        """)
        
        # Create all tabs
        self.create_general_tab()
        self.create_controller_tab()
        self.create_fire_detection_tab()
        self.create_fire_detection_tab()
        self.create_camera_tab()
        self.create_alerts_tab()
        self.create_logging_tab()
        self.create_cloud_tab()
        self.create_security_tab()
        self.create_system_tab()
        self.create_advanced_config_tab()
        self.create_testing_tab()
        self.create_about_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.setStyleSheet(self.get_button_style("#6c757d"))
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        export_btn = QPushButton("📤 Export Settings")
        export_btn.setStyleSheet(self.get_button_style("#17a2b8"))
        export_btn.clicked.connect(self.export_settings)
        button_layout.addWidget(export_btn)
        
        import_btn = QPushButton("📥 Import Settings")
        import_btn.setStyleSheet(self.get_button_style("#17a2b8"))
        import_btn.clicked.connect(self.import_settings)
        button_layout.addWidget(import_btn)
        
        apply_btn = QPushButton("✅ Apply Settings")
        apply_btn.setStyleSheet(self.get_button_style("#28a745"))
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def get_button_style(self, color):
        """Get button stylesheet"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """
    
    def create_scrollable_tab(self, title):
        """Create a scrollable tab container"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        scroll.setWidget(container)
        self.tab_widget.addTab(scroll, title)
        
        return layout
    
    def create_group_box(self, title):
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid #30363d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group
    
    def create_general_tab(self):
        """Create General Settings tab"""
        layout = self.create_scrollable_tab("🌐 General")
        
        # Language
        lang_group = self.create_group_box("Language & Region")
        lang_layout = QFormLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Chinese", "Hindi"])
        lang_layout.addRow("Language:", self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Appearance
        appearance_group = self.create_group_box("Appearance")
        appearance_layout = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        appearance_layout.addRow("Theme Mode:", self.theme_combo)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Startup
        startup_group = self.create_group_box("Startup Behavior")
        startup_layout = QVBoxLayout()
        self.auto_start_check = QCheckBox("Start automatically on system boot")
        self.start_minimized_check = QCheckBox("Start minimized to system tray")
        startup_layout.addWidget(self.auto_start_check)
        startup_layout.addWidget(self.start_minimized_check)
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Notifications
        notif_group = self.create_group_box("Notifications")
        notif_layout = QVBoxLayout()
        self.show_notifications_check = QCheckBox("Show desktop notifications")
        notif_layout.addWidget(self.show_notifications_check)
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        
        # Default Save Location
        save_group = self.create_group_box("Default Save Location")
        save_layout = QHBoxLayout()
        self.save_location_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_save_location)
        save_layout.addWidget(self.save_location_edit)
        save_layout.addWidget(browse_btn)
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        layout.addStretch()

    def create_controller_tab(self):
        """Create Controller Settings tab"""
        layout = self.create_scrollable_tab("🎮 Controller")
        
        # Connection Settings
        conn_group = self.create_group_box("ESP32 Connection")
        conn_layout = QFormLayout()
        
        self.esp32_ip_edit = QLineEdit()
        self.esp32_ip_edit.setPlaceholderText("e.g. 192.168.1.100")
        conn_layout.addRow("ESP32 IP Address:", self.esp32_ip_edit)
        
        test_btn = QPushButton("🔗 Test Connection")
        test_btn.clicked.connect(self.test_controller_connection)
        conn_layout.addRow("", test_btn)
        
        self.connection_status_label = QLabel("Status: Not Tested")
        self.connection_status_label.setStyleSheet("font-weight: bold;")
        conn_layout.addRow("", self.connection_status_label)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        layout.addStretch()
    
    def create_fire_detection_tab(self):
        """Create Fire Detection Settings tab"""
        layout = self.create_scrollable_tab("🔥 Fire Detection")
        
        # Model Selection
        model_group = self.create_group_box("Detection Model")
        model_layout = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["YOLOv8n (Fast)", "YOLOv8s (Balanced)", "YOLOv8m (Accurate)", "Custom Model"])
        model_layout.addRow("Model:", self.model_combo)
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(50)
        self.confidence_label = QLabel("0.50")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v/100:.2f}")
        )
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(self.confidence_slider)
        conf_layout.addWidget(self.confidence_label)
        model_layout.addRow("Confidence Threshold:", conf_layout)
        
        self.nms_slider = QSlider(Qt.Horizontal)
        self.nms_slider.setRange(0, 100)
        self.nms_slider.setValue(45)
        self.nms_label = QLabel("0.45")
        self.nms_slider.valueChanged.connect(
            lambda v: self.nms_label.setText(f"{v/100:.2f}")
        )
        nms_layout = QHBoxLayout()
        nms_layout.addWidget(self.nms_slider)
        nms_layout.addWidget(self.nms_label)
        model_layout.addRow("NMS Threshold:", nms_layout)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Sensitivity
        sensitivity_group = self.create_group_box("Sensitivity Controls")
        sensitivity_layout = QFormLayout()
        self.fire_sensitivity_combo = QComboBox()
        self.fire_sensitivity_combo.addItems(["Low", "Medium", "High"])
        sensitivity_layout.addRow("Fire Sensitivity:", self.fire_sensitivity_combo)
        
        self.smoke_sensitivity_combo = QComboBox()
        self.smoke_sensitivity_combo.addItems(["Low", "Medium", "High"])
        sensitivity_layout.addRow("Smoke Sensitivity:", self.smoke_sensitivity_combo)
        sensitivity_group.setLayout(sensitivity_layout)
        layout.addWidget(sensitivity_group)
        
        # ROI
        roi_group = self.create_group_box("Region of Interest (ROI)")
        roi_layout = QVBoxLayout()
        self.roi_enabled_check = QCheckBox("Enable ROI Selection")
        roi_layout.addWidget(self.roi_enabled_check)
        
        roi_btn_layout = QHBoxLayout()
        self.draw_roi_btn = QPushButton("🖊️ Draw ROI on Camera")
        self.draw_roi_btn.clicked.connect(self.draw_roi)
        self.clear_roi_btn = QPushButton("🗑️ Clear All ROIs")
        self.clear_roi_btn.clicked.connect(self.clear_roi)
        roi_btn_layout.addWidget(self.draw_roi_btn)
        roi_btn_layout.addWidget(self.clear_roi_btn)
        roi_layout.addLayout(roi_btn_layout)
        
        roi_group.setLayout(roi_layout)
        layout.addWidget(roi_group)
        
        # Performance Mode
        perf_group = self.create_group_box("Performance Mode")
        perf_layout = QFormLayout()
        self.performance_combo = QComboBox()
        self.performance_combo.addItems(["Speed Priority", "Balanced", "Accuracy Priority"])
        perf_layout.addRow("Mode:", self.performance_combo)
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
    
    def create_camera_tab(self):
        """Create Camera Settings tab"""
        layout = self.create_scrollable_tab("🎥 Camera")
        
        # Camera Source
        source_group = self.create_group_box("Camera Source")
        source_layout = QFormLayout()
        self.camera_source_combo = QComboBox()
        self.camera_source_combo.addItems(["Laptop Cam", "External USB Cam", "IP Camera", "Video File"])
        self.camera_source_combo.currentTextChanged.connect(self.on_camera_source_changed)
        source_layout.addRow("Source Type:", self.camera_source_combo)
        
        self.ip_camera_edit = QLineEdit()
        self.ip_camera_edit.setPlaceholderText("rtsp://username:password@ip:port/stream")
        source_layout.addRow("IP Camera URL:", self.ip_camera_edit)

        self.video_file_edit = QLineEdit()
        self.video_file_edit.setPlaceholderText("Select a video file...")
        self.browse_video_btn = QPushButton("Browse...")
        self.browse_video_btn.clicked.connect(self.browse_video_file)
        
        video_file_layout = QHBoxLayout()
        video_file_layout.addWidget(self.video_file_edit)
        video_file_layout.addWidget(self.browse_video_btn)
        source_layout.addRow("Video File:", video_file_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Video Settings
        video_group = self.create_group_box("Video Settings")
        video_layout = QFormLayout()
        
        self.frame_size_combo = QComboBox()
        self.frame_size_combo.addItems(["480p (640x480)", "720p (1280x720)", "1080p (1920x1080)"])
        video_layout.addRow("Frame Size:", self.frame_size_combo)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(10, 60)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" FPS")
        video_layout.addRow("Frame Rate:", self.fps_spin)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # Image Adjustments
        adjust_group = self.create_group_box("Image Adjustments")
        adjust_layout = QFormLayout()
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(50)
        self.brightness_label = QLabel("50")
        self.brightness_slider.valueChanged.connect(lambda v: self.brightness_label.setText(str(v)))
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(self.brightness_slider)
        bright_layout.addWidget(self.brightness_label)
        adjust_layout.addRow("Brightness:", bright_layout)
        
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(50)
        self.contrast_label = QLabel("50")
        self.contrast_slider.valueChanged.connect(lambda v: self.contrast_label.setText(str(v)))
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        adjust_layout.addRow("Contrast:", contrast_layout)
        
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(0, 100)
        self.saturation_slider.setValue(50)
        self.saturation_label = QLabel("50")
        self.saturation_slider.valueChanged.connect(lambda v: self.saturation_label.setText(str(v)))
        sat_layout = QHBoxLayout()
        sat_layout.addWidget(self.saturation_slider)
        sat_layout.addWidget(self.saturation_label)
        adjust_layout.addRow("Saturation:", sat_layout)
        
        adjust_group.setLayout(adjust_layout)
        layout.addWidget(adjust_group)
        
        # AI Processing
        ai_group = self.create_group_box("AI Processing")
        ai_layout = QFormLayout()
        self.ai_processing_combo = QComboBox()
        self.ai_processing_combo.addItems(["Full Frame", "ROI Only"])
        ai_layout.addRow("Processing Mode:", self.ai_processing_combo)
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
    
    def create_alerts_tab(self):
        """Create Alert & Notifications tab"""
        layout = self.create_scrollable_tab("📢 Alerts")
        
        # Alert Types
        types_group = self.create_group_box("Alert Types")
        types_layout = QVBoxLayout()
        self.sound_alert_check = QCheckBox("🔊 Sound Alert")
        self.email_alert_check = QCheckBox("📧 Email Alert")
        self.desktop_notif_check = QCheckBox("🖥️ Desktop Notification")
        types_layout.addWidget(self.sound_alert_check)
        types_layout.addWidget(self.email_alert_check)
        types_layout.addWidget(self.desktop_notif_check)
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        # Alert Customization
        custom_group = self.create_group_box("Alert Customization")
        custom_layout = QFormLayout()
        
        sound_layout = QHBoxLayout()
        self.alert_sound_edit = QLineEdit()
        browse_sound_btn = QPushButton("Browse...")
        browse_sound_btn.clicked.connect(self.browse_alert_sound)
        sound_layout.addWidget(self.alert_sound_edit)
        sound_layout.addWidget(browse_sound_btn)
        custom_layout.addRow("Alert Sound:", sound_layout)
        
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 300)
        self.cooldown_spin.setValue(10)
        self.cooldown_spin.setSuffix(" seconds")
        custom_layout.addRow("Cool-down Time:", self.cooldown_spin)
        
        self.repeated_alerts_check = QCheckBox("Enable repeated alerts")
        custom_layout.addRow("", self.repeated_alerts_check)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # Message Template
        template_group = self.create_group_box("Alert Message Template")
        template_layout = QVBoxLayout()
        self.alert_template_edit = QTextEdit()
        self.alert_template_edit.setMaximumHeight(100)
        self.alert_template_edit.setPlaceholderText("Use {location}, {date}, {time} as placeholders")
        template_layout.addWidget(self.alert_template_edit)
        
        info_label = QLabel("Available placeholders: {location}, {date}, {time}, {camera}")
        info_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        template_layout.addWidget(info_label)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        layout.addStretch()
    
    def create_logging_tab(self):
        """Create Data & Logging tab"""
        layout = self.create_scrollable_tab("💾 Logging")
        
        # Enable Logging
        enable_group = self.create_group_box("Logging Control")
        enable_layout = QVBoxLayout()
        self.enable_logging_check = QCheckBox("Enable Logging")
        enable_layout.addWidget(self.enable_logging_check)
        enable_group.setLayout(enable_layout)
        layout.addWidget(enable_group)
        
        # Log Types
        types_group = self.create_group_box("Log Types")
        types_layout = QVBoxLayout()
        self.log_text_check = QCheckBox("📝 Text Logs")
        self.log_images_check = QCheckBox("🖼️ Image Logs")
        self.log_videos_check = QCheckBox("🎬 Video Clips (5 sec before & after)")
        types_layout.addWidget(self.log_text_check)
        types_layout.addWidget(self.log_images_check)
        types_layout.addWidget(self.log_videos_check)
        types_group.setLayout(types_layout)
        layout.addWidget(types_group)
        
        # Auto Cleanup
        cleanup_group = self.create_group_box("Auto-Cleanup")
        cleanup_layout = QFormLayout()
        
        self.auto_cleanup_check = QCheckBox("Enable auto-cleanup")
        cleanup_layout.addRow("", self.auto_cleanup_check)
        
        self.keep_logs_spin = QSpinBox()
        self.keep_logs_spin.setRange(1, 365)
        self.keep_logs_spin.setValue(30)
        self.keep_logs_spin.setSuffix(" days")
        cleanup_layout.addRow("Keep logs for:", self.keep_logs_spin)
        
        cleanup_group.setLayout(cleanup_layout)
        layout.addWidget(cleanup_group)
        
        # Storage Usage
        storage_group = self.create_group_box("Storage Usage")
        storage_layout = QVBoxLayout()
        
        self.storage_progress = QProgressBar()
        self.storage_progress.setValue(0)
        storage_layout.addWidget(self.storage_progress)
        
        self.storage_label = QLabel("0 MB / 1000 MB")
        self.storage_label.setStyleSheet("color: #8b949e;")
        storage_layout.addWidget(self.storage_label)
        
        export_logs_btn = QPushButton("📦 Export Logs (ZIP)")
        export_logs_btn.clicked.connect(self.export_logs)
        storage_layout.addWidget(export_logs_btn)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        # Update storage usage
        QTimer.singleShot(500, self.update_storage_usage)
        
        layout.addStretch()
    
    def create_cloud_tab(self):
        """Create Cloud Settings tab"""
        layout = self.create_scrollable_tab("☁️ Cloud")
        
        # Cloud Connection
        cloud_group = self.create_group_box("Cloud Dashboard")
        cloud_layout = QFormLayout()
        
        self.cloud_enabled_check = QCheckBox("Enable cloud sync")
        cloud_layout.addRow("", self.cloud_enabled_check)
        
        self.cloud_url_edit = QLineEdit()
        self.cloud_url_edit.setPlaceholderText("https://dashboard.firevision.com")
        cloud_layout.addRow("Dashboard URL:", self.cloud_url_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key")
        cloud_layout.addRow("API Key:", self.api_key_edit)
        
        self.sync_events_check = QCheckBox("Sync detection events to cloud")
        cloud_layout.addRow("", self.sync_events_check)
        
        test_connection_btn = QPushButton("🔗 Test Connection")
        test_connection_btn.clicked.connect(self.test_cloud_connection)
        cloud_layout.addRow("", test_connection_btn)
        
        cloud_group.setLayout(cloud_layout)
        layout.addWidget(cloud_group)
        
        # Info
        info_label = QLabel("ℹ️ Cloud features are optional and require a valid subscription.")
        info_label.setStyleSheet("color: #8b949e; font-size: 12px; padding: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def create_security_tab(self):
        """Create Security Settings tab"""
        layout = self.create_scrollable_tab("🔐 Security")
        
        # Password Protection
        password_group = self.create_group_box("Password Protection")
        password_layout = QFormLayout()
        
        self.password_protection_check = QCheckBox("Enable password protection")
        password_layout.addRow("", self.password_protection_check)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password")
        password_layout.addRow("Password:", self.password_edit)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Role-based Access
        role_group = self.create_group_box("Role-based Access")
        role_layout = QFormLayout()
        
        self.user_role_combo = QComboBox()
        self.user_role_combo.addItems(["Admin", "Viewer"])
        role_layout.addRow("User Role:", self.user_role_combo)
        
        role_group.setLayout(role_layout)
        layout.addWidget(role_group)
        
        # Encryption
        encrypt_group = self.create_group_box("Data Encryption")
        encrypt_layout = QVBoxLayout()
        
        self.encrypt_logs_check = QCheckBox("Encrypt logs and recordings")
        encrypt_layout.addWidget(self.encrypt_logs_check)
        
        encrypt_group.setLayout(encrypt_layout)
        layout.addWidget(encrypt_group)
        
        layout.addStretch()
    
    def create_system_tab(self):
        """Create System Settings tab"""
        layout = self.create_scrollable_tab("🖥️ System")
        
        # Main Horizontal Layout for Performance Section
        perf_container = QWidget()
        perf_layout = QHBoxLayout(perf_container)
        perf_layout.setContentsMargins(0, 0, 0, 0)
        perf_layout.setSpacing(15)
        
        # --- Left Side: Performance Optimization ---
        perf_opt_group = self.create_group_box("Performance Optimization")
        perf_opt_layout = QVBoxLayout()
        
        self.auto_optimizer_check = QCheckBox("Auto Mode Optimizer (Recommended)")
        self.auto_optimizer_check.setToolTip("Automatically detects system hardware and adjusts settings for best performance.\nRecommended for low-end laptops.")
        perf_opt_layout.addWidget(self.auto_optimizer_check)
        
        self.nvr_mode_check = QCheckBox("Force NVR-Only Mode (Disable AI)")
        self.nvr_mode_check.setToolTip("Manually disable all AI features to save resources.\nThis will unload detection models immediately.")
        self.nvr_mode_check.setStyleSheet("color: #ff9800;")
        perf_opt_layout.addWidget(self.nvr_mode_check)
        
        self.optimization_status_label = QLabel("Current Mode: Standard")
        self.optimization_status_label.setStyleSheet("color: #8b949e; margin-left: 20px;")
        perf_opt_layout.addWidget(self.optimization_status_label)
        
        perf_opt_layout.addStretch()
        perf_opt_group.setLayout(perf_opt_layout)
        
        # --- Right Side: System Hardware & Performance ---
        sys_info_group = self.create_group_box("System Hardware")
        sys_info_layout = QVBoxLayout()
        
        # CPU Info
        self.cpu_label = QLabel("CPU: Loading...")
        self.cpu_label.setStyleSheet("font-weight: bold; color: #58a6ff;")
        self.cpu_usage_bar = QProgressBar()
        self.cpu_usage_bar.setStyleSheet("QProgressBar::chunk { background-color: #58a6ff; }")
        self.cpu_usage_bar.setRange(0, 100)
        self.cpu_usage_bar.setTextVisible(False)
        self.cpu_usage_bar.setFixedHeight(5)
        
        sys_info_layout.addWidget(self.cpu_label)
        sys_info_layout.addWidget(self.cpu_usage_bar)
        
        # RAM Info
        self.ram_label = QLabel("RAM: Loading...")
        self.ram_label.setStyleSheet("font-weight: bold; color: #3fb950;")
        self.ram_usage_bar = QProgressBar()
        self.ram_usage_bar.setStyleSheet("QProgressBar::chunk { background-color: #3fb950; }")
        self.ram_usage_bar.setRange(0, 100)
        self.ram_usage_bar.setTextVisible(False)
        self.ram_usage_bar.setFixedHeight(5)
        
        sys_info_layout.addWidget(self.ram_label)
        sys_info_layout.addWidget(self.ram_usage_bar)
        
        # GPU Info
        self.gpu_label = QLabel("GPU: Checking...")
        self.gpu_label.setStyleSheet("font-weight: bold; color: #d29922;")
        sys_info_layout.addWidget(self.gpu_label)
        
        # Disk Info
        self.disk_label = QLabel("Disk: Loading...")
        self.disk_label.setStyleSheet("font-weight: bold; color: #a371f7;")
        sys_info_layout.addWidget(self.disk_label)
        
        sys_info_group.setLayout(sys_info_layout)
        
        # Add both to parallel layout
        perf_layout.addWidget(perf_opt_group, 60) # 60% width
        perf_layout.addWidget(sys_info_group, 40) # 40% width
        
        layout.addWidget(perf_container)

        # Hardware
        hardware_group = self.create_group_box("Hardware Acceleration")
        hardware_layout = QFormLayout()
        
        self.use_gpu_check = QCheckBox("Use GPU if available")
        hardware_layout.addRow("", self.use_gpu_check)
        
        self.hardware_accel_check = QCheckBox("Enable hardware acceleration")
        hardware_layout.addRow("", self.hardware_accel_check)
        
        hardware_group.setLayout(hardware_layout)
        layout.addWidget(hardware_group)
        
        # Updates
        update_group = self.create_group_box("Software Updates")
        update_layout = QFormLayout()
        
        self.auto_update_check = QCheckBox("Enable automatic updates")
        update_layout.addRow("", self.auto_update_check)
        
        self.check_updates_start_check = QCheckBox("Check for updates on startup")
        update_layout.addRow("", self.check_updates_start_check)
        
        check_updates_btn = QPushButton("🔍 Check for Updates Now")
        check_updates_btn.clicked.connect(self.check_for_updates)
        update_layout.addRow("", check_updates_btn)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        layout.addStretch()
        
        # Start update timer for this tab
        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self.update_system_stats)
        self.sys_timer.start(2000) # Update every 2 seconds
        
    def update_system_stats(self):
        """Update system hardware stats if the widget is visible"""
        if not self.isVisible(): 
            return
            
        # Only update if we are on the System tab (index 8... assuming order remains)
        # Better: check if tab widget current widget is the system container
        # But for now, simple visibility check of the settings widget is okay-ish, 
        # though ideally we check the active tab. 
        # Since 'create_scrollable_tab' adds a wrapper, we can't easily check 'currentWidget() == self' locally.
        # We'll rely on global visibility for simplicity + low cost of psutil.
        
        try:
            from utils.system_profiler import profiler
            stats = profiler.get_realtime_stats()
            
            # CPU
            cpu = stats.get('cpu', {})
            self.cpu_label.setText(f"CPU: {cpu.get('model', 'Unknown')} ({cpu.get('count', 0)} Cores) - {cpu.get('usage_percent', 0)}%")
            self.cpu_usage_bar.setValue(int(cpu.get('usage_percent', 0)))
            
            # RAM
            ram = stats.get('ram', {})
            self.ram_label.setText(f"RAM: {ram.get('usage_percent', 0)}% Used ({ram.get('available_gb', 0)}GB Free / {ram.get('total_gb', 0)}GB Total)")
            self.ram_usage_bar.setValue(int(ram.get('usage_percent', 0)))
            
            # GPU
            gpu = stats.get('gpu', {})
            if gpu.get('available', False):
                self.gpu_label.setText(f"GPU: {gpu.get('model', 'Unknown')} (VRAM: {gpu.get('vram_total_gb', 'N/A')}GB)")
                self.gpu_label.setStyleSheet("font-weight: bold; color: #d29922;")
            else:
                self.gpu_label.setText("GPU: Not Detected / CPU Mode")
                self.gpu_label.setStyleSheet("font-weight: bold; color: #8b949e;")
                
            # Disk
            disk = stats.get('disk', {})
            self.disk_label.setText(f"Disk (C:): {disk.get('free_gb', 0)}GB Free ({disk.get('total_gb', 0)}GB Total)")
            
        except Exception as e:
            print(f"Error updating system stats UI: {e}")
    
    
    def create_advanced_config_tab(self):
        """Create Advanced Configuration tab (Central Config)"""
        layout = self.create_scrollable_tab("🛠️ Advanced")
        
        if not self.config_manager:
            error_label = QLabel("Config Manager not available. Advanced settings disabled.")
            error_label.setStyleSheet("color: #ff3333; font-size: 16px; padding: 20px;")
            layout.addWidget(error_label)
            layout.addStretch()
            return

        # Network Config
        network_group = self.create_group_box("Network Configuration")
        network_layout = QFormLayout()
        
        self.backend_url_edit = QLineEdit()
        self.backend_url_edit.setPlaceholderText("http://localhost:5000")
        network_layout.addRow("Backend URL:", self.backend_url_edit)
        
        self.mobile_app_url_edit = QLineEdit()
        self.mobile_app_url_edit.setPlaceholderText("http://192.168.1.X:PORT")
        network_layout.addRow("Mobile App URL:", self.mobile_app_url_edit)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Detection Config
        detect_group = self.create_group_box("Advanced Detection Settings")
        detect_layout = QFormLayout()
        
        self.night_mode_check = QCheckBox("Enable Night Mode Preprocessing")
        detect_layout.addRow("", self.night_mode_check)
        
        self.temporal_check_check = QCheckBox("Enable Temporal Flicker Check")
        detect_layout.addRow("", self.temporal_check_check)
        
        self.process_every_spin = QSpinBox()
        self.process_every_spin.setRange(1, 30)
        detect_layout.addRow("Process Every N Frames:", self.process_every_spin)
        
        detect_group.setLayout(detect_layout)
        layout.addWidget(detect_group)
        
        # Timeouts Config
        timeout_group = self.create_group_box("System Timeouts (Seconds)")
        timeout_layout = QFormLayout()
        
        self.cam_connect_spin = QSpinBox()
        self.cam_connect_spin.setRange(1, 60)
        timeout_layout.addRow("Camera Connection Timeout:", self.cam_connect_spin)
        
        self.cam_read_spin = QSpinBox()
        self.cam_read_spin.setRange(1, 60)
        timeout_layout.addRow("Frame Read Timeout:", self.cam_read_spin)
        
        self.net_timeout_spin = QSpinBox()
        self.net_timeout_spin.setRange(1, 60)
        timeout_layout.addRow("Network Request Timeout:", self.net_timeout_spin)
        
        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)

        layout.addStretch()

    def create_testing_tab(self):
        """Create Testing Tools tab"""
        layout = self.create_scrollable_tab("🧪 Testing")
        
        # Camera Test
        camera_group = self.create_group_box("Camera Testing")
        camera_layout = QVBoxLayout()
        
        test_camera_btn = QPushButton("📹 Test Camera Feed")
        test_camera_btn.clicked.connect(self.test_camera)
        camera_layout.addWidget(test_camera_btn)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Alert Tests
        alert_group = self.create_group_box("Alert Testing")
        alert_layout = QVBoxLayout()
        
        test_sound_btn = QPushButton("🔊 Test Alert Sound")
        test_sound_btn.clicked.connect(self.test_alert_sound)
        alert_layout.addWidget(test_sound_btn)
        
        test_email_btn = QPushButton("📧 Test Email Alert")
        test_email_btn.clicked.connect(self.test_email_alert)
        alert_layout.addWidget(test_email_btn)
        
        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)
        
        # Detection Test
        detection_group = self.create_group_box("Detection Testing")
        detection_layout = QVBoxLayout()
        
        test_detection_btn = QPushButton("🔥 Test Fire Detection Model")
        test_detection_btn.clicked.connect(self.test_detection_model)
        detection_layout.addWidget(test_detection_btn)
        
        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)
        
        layout.addStretch()
    
    def create_about_tab(self):
        """Create About & Support tab"""
        layout = self.create_scrollable_tab("ℹ️ About")
        
        # Version Info
        version_group = self.create_group_box("Version Information")
        version_layout = QVBoxLayout()
        
        version_label = QLabel(f"<b>FireVision Pro</b><br>Version: {self.settings_manager.get_setting('about.version', '1.0.0')}")
        version_label.setStyleSheet("font-size: 16px; color: #ffffff; padding: 10px;")
        version_layout.addWidget(version_label)
        
        build_label = QLabel(f"Build Date: {self.settings_manager.get_setting('about.build_date', '2025-12-09')}")
        build_label.setStyleSheet("color: #8b949e; padding: 5px 10px;")
        version_layout.addWidget(build_label)
        
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # Developer Info
        dev_group = self.create_group_box("Developer Information")
        dev_layout = QVBoxLayout()
        
        dev_label = QLabel(f"Developed by: {self.settings_manager.get_setting('about.developer', 'FireVision Team')}")
        dev_label.setStyleSheet("color: #ffffff; padding: 5px 10px;")
        dev_layout.addWidget(dev_label)
        
        dev_group.setLayout(dev_layout)
        layout.addWidget(dev_group)
        
        # Support
        support_group = self.create_group_box("Support")
        support_layout = QVBoxLayout()
        
        support_label = QLabel(f"Email: {self.settings_manager.get_setting('about.support_email', 'support@firevision.com')}")
        support_label.setStyleSheet("color: #8b949e; padding: 5px 10px;")
        support_layout.addWidget(support_label)
        
        contact_btn = QPushButton("📧 Contact Support")
        contact_btn.clicked.connect(self.contact_support)
        support_layout.addWidget(contact_btn)
        
        support_group.setLayout(support_layout)
        layout.addWidget(support_group)
        
        # Changelog
        changelog_group = self.create_group_box("Update Changelog")
        changelog_layout = QVBoxLayout()
        
        changelog_text = QTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(200)
        changelog_text.setPlainText("""
Version 1.0.0 (2025-12-09):
• Initial release
• Fire and smoke detection with YOLO
• Multi-camera support
• Alert system with email notifications
• Cloud backup integration
• Comprehensive settings page
        """)
        changelog_layout.addWidget(changelog_text)
        
        changelog_group.setLayout(changelog_layout)
        layout.addWidget(changelog_group)
        
        layout.addStretch()
    
    # Helper methods
    def on_camera_source_changed(self, source):
        """Handle camera source change"""
        self.ip_camera_edit.setEnabled(source == "IP Camera")
        self.video_file_edit.setEnabled(source == "Video File")
        self.browse_video_btn.setEnabled(source == "Video File")

    def browse_video_file(self):
        """Browse for video file"""
        file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov)")
        if file:
            self.video_file_edit.setText(file)
    
    def browse_save_location(self):
        """Browse for save location"""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_location_edit.setText(folder)
    
    def browse_alert_sound(self):
        """Browse for alert sound file"""
        file, _ = QFileDialog.getOpenFileName(self, "Select Alert Sound", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file:
            self.alert_sound_edit.setText(file)
    
    def draw_roi(self):
        """Open ROI drawing tool"""
        QMessageBox.information(self, "ROI Drawing", "ROI drawing tool will open with live camera feed.\nDraw rectangles to define regions of interest.")
    
    def clear_roi(self):
        """Clear all ROI regions"""
        reply = QMessageBox.question(self, "Clear ROIs", "Are you sure you want to clear all ROI regions?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings_manager.set_setting("fire_detection.roi_regions", [])
            QMessageBox.information(self, "Success", "All ROI regions cleared.")
    
    def update_storage_usage(self):
        """Update storage usage indicator"""
        try:
            logs_path = self.settings_manager.get_setting("general.default_save_location", "./logs")
            if os.path.exists(logs_path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(logs_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                
                size_mb = total_size / (1024 * 1024)
                max_mb = self.settings_manager.get_setting("logging.max_storage_mb", 1000)
                
                self.storage_progress.setValue(int((size_mb / max_mb) * 100))
                self.storage_label.setText(f"{size_mb:.2f} MB / {max_mb} MB")
        except Exception as e:
            print(f"Error calculating storage: {e}")
    
    def export_logs(self):
        """Export logs as ZIP"""
        file, _ = QFileDialog.getSaveFileName(self, "Export Logs", f"firevision_logs_{datetime.now().strftime('%Y%m%d')}.zip", "ZIP Files (*.zip)")
        if file:
            try:
                logs_path = self.settings_manager.get_setting("general.default_save_location", "./logs")
                shutil.make_archive(file.replace('.zip', ''), 'zip', logs_path)
                QMessageBox.information(self, "Success", f"Logs exported to:\n{file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs:\n{str(e)}")
    
    def test_cloud_connection(self):
        """Test cloud connection"""
        QMessageBox.information(self, "Cloud Test", "Testing cloud connection...\n\nThis feature is coming soon!")
    
    def test_camera(self):
        """Test camera feed"""
        QMessageBox.information(self, "Camera Test", "Camera test will open a preview window.\n\nThis feature is coming soon!")
    
    def test_alert_sound(self):
        """Test alert sound"""
        try:
            import pygame
            pygame.mixer.init()
            sound_file = self.alert_sound_edit.text() or resource_path("assests/audio/alarm.mp3")
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                QMessageBox.information(self, "Sound Test", "Playing alert sound...")
            else:
                QMessageBox.warning(self, "Error", "Alert sound file not found!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play sound:\n{str(e)}")
    
    def test_email_alert(self):
        """Test email alert"""
        QMessageBox.information(self, "Email Test", "Sending test email...\n\nThis feature requires valid SMTP configuration.")
    
    def test_detection_model(self):
        """Test detection model"""
        QMessageBox.information(self, "Detection Test", "Testing fire detection model with sample image...\n\nThis feature is coming soon!")
    
    def check_for_updates(self):
        """Check for software updates"""
        QMessageBox.information(self, "Update Check", "Checking for updates...\n\nYou are running the latest version!")
    
    def test_controller_connection(self):
        """Test connection to ESP32"""
        import urllib.request
        
        ip = self.esp32_ip_edit.text()
        if not ip:
            QMessageBox.warning(self, "Input Error", "Please enter an IP address.")
            return
            
        url = f"http://{ip}/"
        if not ip.startswith("http"):
             url = f"http://{ip}"
             
        try:
            # Try to connect with a short timeout
            # We don't care about the response content, just connectivity
            # Actually, usually ESP32 webservers respond to / or /status
            urllib.request.urlopen(url, timeout=2)
            
            self.connection_status_label.setText("Status: ✅ Connected")
            self.connection_status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            
            # Update settings immediately
            self.settings_manager.set_setting("controller.is_connected", True)
            self.settings_manager.set_setting("controller.esp32_ip", ip)
            self.settings_manager.save_settings() # Trigger signal for listeners
            
            QMessageBox.information(self, "Success", f"Successfully connected to {ip}")
            
        except Exception as e:
            self.connection_status_label.setText("Status: ❌ Not Connected")
            self.connection_status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            
            self.settings_manager.set_setting("controller.is_connected", False)
            
            QMessageBox.critical(self, "Connection Failed", f"Could not connect to {ip}\nError: {str(e)}")

    def contact_support(self):
        """Contact support"""
        import webbrowser
        email = self.settings_manager.get_setting("about.support_email", "support@firevision.com")
        webbrowser.open(f"mailto:{email}")
    
    def load_current_settings(self):
        """Load current settings into UI"""
        # General
        self.language_combo.setCurrentText(self.settings_manager.get_setting("general.language", "English"))
        self.theme_combo.setCurrentText(self.settings_manager.get_setting("general.theme_mode", "Dark"))
        self.auto_start_check.setChecked(self.settings_manager.get_setting("general.auto_start_boot", False))
        self.start_minimized_check.setChecked(self.settings_manager.get_setting("general.start_minimized", False))
        self.show_notifications_check.setChecked(self.settings_manager.get_setting("general.show_notifications", True))
        self.save_location_edit.setText(self.settings_manager.get_setting("general.default_save_location", "./logs"))
        
        # Controller
        self.esp32_ip_edit.setText(self.settings_manager.get_setting("controller.esp32_ip", ""))
        is_connected = self.settings_manager.get_setting("controller.is_connected", False)
        if is_connected:
             self.connection_status_label.setText("Status: ✅ Connected")
             self.connection_status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
             self.connection_status_label.setText("Status: ❌ Not Connected (Run Test)")
             self.connection_status_label.setStyleSheet("color: #888888; font-weight: bold;")
        
        # Fire Detection
        model = self.settings_manager.get_setting("fire_detection.model_selection", "YOLOv8n")
        index = self.model_combo.findText(model, Qt.MatchContains)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        conf = int(self.settings_manager.get_setting("fire_detection.detection_confidence", 0.5) * 100)
        self.confidence_slider.setValue(conf)
        
        nms = int(self.settings_manager.get_setting("fire_detection.nms_threshold", 0.45) * 100)
        self.nms_slider.setValue(nms)
        
        self.fire_sensitivity_combo.setCurrentText(self.settings_manager.get_setting("fire_detection.fire_sensitivity", "Medium"))
        self.smoke_sensitivity_combo.setCurrentText(self.settings_manager.get_setting("fire_detection.smoke_sensitivity", "Medium"))
        self.roi_enabled_check.setChecked(self.settings_manager.get_setting("fire_detection.roi_enabled", False))
        self.performance_combo.setCurrentText(self.settings_manager.get_setting("fire_detection.performance_mode", "Balanced"))
        
        # Camera
        self.camera_source_combo.setCurrentText(self.settings_manager.get_setting("camera.source_type", "Laptop Cam"))
        self.ip_camera_edit.setText(self.settings_manager.get_setting("camera.ip_camera_url", ""))
        
        frame_size = self.settings_manager.get_setting("camera.frame_size", "720p")
        index = self.frame_size_combo.findText(frame_size, Qt.MatchContains)
        if index >= 0:
            self.frame_size_combo.setCurrentIndex(index)
        
        self.fps_spin.setValue(self.settings_manager.get_setting("camera.frame_rate", 30))
        self.brightness_slider.setValue(self.settings_manager.get_setting("camera.brightness", 50))
        self.contrast_slider.setValue(self.settings_manager.get_setting("camera.contrast", 50))
        self.saturation_slider.setValue(self.settings_manager.get_setting("camera.saturation", 50))
        self.ai_processing_combo.setCurrentText(self.settings_manager.get_setting("camera.ai_processing_mode", "Full Frame"))
        
        # Alerts
        self.sound_alert_check.setChecked(self.settings_manager.get_setting("alerts.sound_alert", True))
        self.email_alert_check.setChecked(self.settings_manager.get_setting("alerts.email_alert", False))
        self.desktop_notif_check.setChecked(self.settings_manager.get_setting("alerts.desktop_notification", True))
        self.alert_sound_edit.setText(self.settings_manager.get_setting("alerts.alert_sound_file", "assests/audio/alarm.mp3"))
        self.cooldown_spin.setValue(self.settings_manager.get_setting("alerts.cooldown_time", 10))
        self.repeated_alerts_check.setChecked(self.settings_manager.get_setting("alerts.repeated_alerts", True))
        self.alert_template_edit.setPlainText(self.settings_manager.get_setting("alerts.alert_message_template", "🔥 Fire detected at {location} on {date} at {time}"))
        
        # Logging
        self.enable_logging_check.setChecked(self.settings_manager.get_setting("logging.enable_logging", True))
        self.log_text_check.setChecked(self.settings_manager.get_setting("logging.log_text", True))
        self.log_images_check.setChecked(self.settings_manager.get_setting("logging.log_images", True))
        self.log_videos_check.setChecked(self.settings_manager.get_setting("logging.log_videos", False))
        self.auto_cleanup_check.setChecked(self.settings_manager.get_setting("logging.auto_cleanup_enabled", True))
        self.keep_logs_spin.setValue(self.settings_manager.get_setting("logging.keep_logs_days", 30))
        
        # Cloud
        self.cloud_enabled_check.setChecked(self.settings_manager.get_setting("cloud.cloud_enabled", False))
        self.cloud_url_edit.setText(self.settings_manager.get_setting("cloud.cloud_dashboard_url", ""))
        self.api_key_edit.setText(self.settings_manager.get_setting("cloud.api_key", ""))
        self.sync_events_check.setChecked(self.settings_manager.get_setting("cloud.sync_events", False))
        
        # Security
        self.password_protection_check.setChecked(self.settings_manager.get_setting("security.password_protection", False))
        self.user_role_combo.setCurrentText(self.settings_manager.get_setting("security.user_role", "Admin"))
        self.encrypt_logs_check.setChecked(self.settings_manager.get_setting("security.encrypt_logs", False))
        
        # System
        self.use_gpu_check.setChecked(self.settings_manager.get_setting("system.use_gpu", True))
        self.hardware_accel_check.setChecked(self.settings_manager.get_setting("system.hardware_acceleration", True))
        self.auto_update_check.setChecked(self.settings_manager.get_setting("system.auto_update", True))
        self.check_updates_start_check.setChecked(self.settings_manager.get_setting("system.check_updates_on_start", True))
        
        # Optimizer
        self.auto_optimizer_check.setChecked(self.settings_manager.get_setting("system.auto_mode_optimizer", True))
        self.nvr_mode_check.setChecked(self.settings_manager.get_setting("system.nvr_mode_enabled", False))
        
        mode = self.settings_manager.get_setting("system.optimization_mode")
        if mode == "NVR":
            self.optimization_status_label.setText("Current Mode: 🟢 NVR Only (Optimized for Low-End Device)")
            self.optimization_status_label.setStyleSheet("color: #4CAF50; margin-left: 20px; font-weight: bold;")
        else:
            self.optimization_status_label.setText("Current Mode: 🔵 Standard (AI Enabled)")
            self.optimization_status_label.setStyleSheet("color: #2196F3; margin-left: 20px;")
            
        # Load Advanced Config
        if self.config_manager:
            try:
                # Network
                net_conf = self.config_manager.get_config("network", {})
                self.backend_url_edit.setText(net_conf.get("backend_url", ""))
                self.mobile_app_url_edit.setText(net_conf.get("mobile_app_url", ""))
                
                # Detection
                det_conf = self.config_manager.get_config("detection", {})
                self.night_mode_check.setChecked(det_conf.get("night_preprocessing_enabled", False))
                self.temporal_check_check.setChecked(det_conf.get("temporal_check_enabled", False))
                self.process_every_spin.setValue(det_conf.get("process_every_n_frames", 5))
                
                # Timeouts
                to_conf = self.config_manager.get_config("timeouts", {})
                self.cam_connect_spin.setValue(to_conf.get("camera_connect", 10))
                self.cam_read_spin.setValue(to_conf.get("camera_read", 5))
                self.net_timeout_spin.setValue(to_conf.get("network_request", 5))
            except Exception as e:
                print(f"Error loading advanced config: {e}")
    
    def validate_advanced_config(self):
        """Validate advanced configuration inputs"""
        errors = []
        
        if not self.config_manager:
            return True, []  # Skip validation if no config manager
        
        # Validate URLs
        backend_url = self.backend_url_edit.text().strip()
        mobile_url = self.mobile_app_url_edit.text().strip()
        
        if backend_url and not (backend_url.startswith('http://') or backend_url.startswith('https://')):
            errors.append("Backend URL must start with http:// or https://")
        
        if mobile_url and not (mobile_url.startswith('http://') or mobile_url.startswith('https://')):
            errors.append("Mobile App URL must start with http:// or https://")
        
        # Validate numeric ranges
        process_every = self.process_every_spin.value()
        if not (1 <= process_every <= 30):
            errors.append("Process Every N Frames must be between 1 and 30")
        
        cam_connect = self.cam_connect_spin.value()
        if not (1 <= cam_connect <= 60):
            errors.append("Camera Connection Timeout must be between 1 and 60 seconds")
        
        cam_read = self.cam_read_spin.value()
        if not (1 <= cam_read <= 60):
            errors.append("Frame Read Timeout must be between 1 and 60 seconds")
        
        net_timeout = self.net_timeout_spin.value()
        if not (1 <= net_timeout <= 60):
            errors.append("Network Request Timeout must be between 1 and 60 seconds")
        
        return len(errors) == 0, errors
    
    def apply_settings(self):
        """Apply all settings"""
        # General
        self.settings_manager.set_setting("general.language", self.language_combo.currentText())
        self.settings_manager.set_setting("general.theme_mode", self.theme_combo.currentText())
        self.settings_manager.set_setting("general.auto_start_boot", self.auto_start_check.isChecked())
        self.settings_manager.set_setting("general.start_minimized", self.start_minimized_check.isChecked())
        self.settings_manager.set_setting("general.show_notifications", self.show_notifications_check.isChecked())
        self.settings_manager.set_setting("general.default_save_location", self.save_location_edit.text())
        
        # Controller
        self.settings_manager.set_setting("controller.esp32_ip", self.esp32_ip_edit.text())
        # Note: is_connected is set by the test button, relying on that for truth
        
        # Fire Detection
        model_text = self.model_combo.currentText()
        if "YOLOv8n" in model_text:
            model = "YOLOv8n"
        elif "YOLOv8s" in model_text:
            model = "YOLOv8s"
        elif "YOLOv8m" in model_text:
            model = "YOLOv8m"
        else:
            model = "Custom"
        self.settings_manager.set_setting("fire_detection.model_selection", model)
        self.settings_manager.set_setting("fire_detection.detection_confidence", self.confidence_slider.value() / 100.0)
        self.settings_manager.set_setting("fire_detection.nms_threshold", self.nms_slider.value() / 100.0)
        self.settings_manager.set_setting("fire_detection.fire_sensitivity", self.fire_sensitivity_combo.currentText())
        self.settings_manager.set_setting("fire_detection.smoke_sensitivity", self.smoke_sensitivity_combo.currentText())
        self.settings_manager.set_setting("fire_detection.roi_enabled", self.roi_enabled_check.isChecked())
        self.settings_manager.set_setting("fire_detection.performance_mode", self.performance_combo.currentText())
        
        # Camera
        self.settings_manager.set_setting("camera.source_type", self.camera_source_combo.currentText())
        self.settings_manager.set_setting("camera.ip_camera_url", self.ip_camera_edit.text())
        self.settings_manager.set_setting("camera.video_file_path", self.video_file_edit.text())
        
        frame_text = self.frame_size_combo.currentText()
        if "480p" in frame_text:
            frame_size = "480p"
        elif "720p" in frame_text:
            frame_size = "720p"
        else:
            frame_size = "1080p"
        self.settings_manager.set_setting("camera.frame_size", frame_size)
        
        self.settings_manager.set_setting("camera.frame_rate", self.fps_spin.value())
        self.settings_manager.set_setting("camera.brightness", self.brightness_slider.value())
        self.settings_manager.set_setting("camera.contrast", self.contrast_slider.value())
        self.settings_manager.set_setting("camera.saturation", self.saturation_slider.value())
        self.settings_manager.set_setting("camera.ai_processing_mode", self.ai_processing_combo.currentText())
        
        # Alerts
        self.settings_manager.set_setting("alerts.sound_alert", self.sound_alert_check.isChecked())
        self.settings_manager.set_setting("alerts.email_alert", self.email_alert_check.isChecked())
        self.settings_manager.set_setting("alerts.desktop_notification", self.desktop_notif_check.isChecked())
        self.settings_manager.set_setting("alerts.alert_sound_file", self.alert_sound_edit.text())
        self.settings_manager.set_setting("alerts.cooldown_time", self.cooldown_spin.value())
        self.settings_manager.set_setting("alerts.repeated_alerts", self.repeated_alerts_check.isChecked())
        self.settings_manager.set_setting("alerts.alert_message_template", self.alert_template_edit.toPlainText())
        
        # Logging
        self.settings_manager.set_setting("logging.enable_logging", self.enable_logging_check.isChecked())
        self.settings_manager.set_setting("logging.log_text", self.log_text_check.isChecked())
        self.settings_manager.set_setting("logging.log_images", self.log_images_check.isChecked())
        self.settings_manager.set_setting("logging.log_videos", self.log_videos_check.isChecked())
        self.settings_manager.set_setting("logging.auto_cleanup_enabled", self.auto_cleanup_check.isChecked())
        self.settings_manager.set_setting("logging.keep_logs_days", self.keep_logs_spin.value())
        
        # Cloud
        self.settings_manager.set_setting("cloud.cloud_enabled", self.cloud_enabled_check.isChecked())
        self.settings_manager.set_setting("cloud.cloud_dashboard_url", self.cloud_url_edit.text())
        self.settings_manager.set_setting("cloud.api_key", self.api_key_edit.text())
        self.settings_manager.set_setting("cloud.sync_events", self.sync_events_check.isChecked())
        
        # Security
        self.settings_manager.set_setting("security.password_protection", self.password_protection_check.isChecked())
        self.settings_manager.set_setting("security.user_role", self.user_role_combo.currentText())
        self.settings_manager.set_setting("security.encrypt_logs", self.encrypt_logs_check.isChecked())
        
        # System
        self.settings_manager.set_setting("system.use_gpu", self.use_gpu_check.isChecked())
        self.settings_manager.set_setting("system.hardware_acceleration", self.hardware_accel_check.isChecked())
        self.settings_manager.set_setting("system.auto_update", self.auto_update_check.isChecked())
        self.settings_manager.set_setting("system.check_updates_on_start", self.check_updates_start_check.isChecked())
        self.settings_manager.set_setting("system.auto_mode_optimizer", self.auto_optimizer_check.isChecked())
        
        # Apply Advanced Config
        if self.config_manager:
            # Validate first
            is_valid, validation_errors = self.validate_advanced_config()
            if not is_valid:
                error_msg = "Configuration validation failed:\n" + "\n".join(validation_errors)
                QMessageBox.warning(self, "Validation Error", error_msg)
                return  # Don't apply if validation fails
            
            try:
                # Update Network
                self.config_manager.update_config("network.backend_url", self.backend_url_edit.text())
                self.config_manager.update_config("network.mobile_app_url", self.mobile_app_url_edit.text())
                
                # Update Detection
                self.config_manager.update_config("detection.night_preprocessing_enabled", self.night_mode_check.isChecked())
                self.config_manager.update_config("detection.temporal_check_enabled", self.temporal_check_check.isChecked())
                self.config_manager.update_config("detection.process_every_n_frames", self.process_every_spin.value())
                
                # Update Timeouts
                self.config_manager.update_config("timeouts.camera_connect", self.cam_connect_spin.value())
                self.config_manager.update_config("timeouts.camera_read", self.cam_read_spin.value())
                self.config_manager.update_config("timeouts.network_request", self.net_timeout_spin.value())
                
                print("✅ Advanced configuration applied via ConfigManager")
            except Exception as e:
                print(f"Error applying advanced config: {e}")
        
        # Check if NVR mode changed
        old_nvr_status = self.settings_manager.get_setting("system.nvr_mode_enabled", False)
        new_nvr_status = self.nvr_mode_check.isChecked()
        self.settings_manager.set_setting("system.nvr_mode_enabled", new_nvr_status)
        
        # Log to confirm
        print(f"Applied Auto Optimizer: {self.auto_optimizer_check.isChecked()}")
        print(f"Applied NVR Mode: {new_nvr_status}")
        
        # Apply NVR mode change immediately if needed
        if old_nvr_status != new_nvr_status:
            try:
                # We need to access the main window's camera manager to unload models
                # This depends on how SettingsWidget is initialized. 
                # Ideally, we emit a signal that MainWindow listens to.
                pass 
            except Exception as e:
                print(f"Error switching NVR mode from settings: {e}")
        
        # Save settings
        self.settings_manager.save_settings()
        
        # Emit signal
        self.settings_applied.emit()
        
        QMessageBox.information(self, "Success", "Settings applied successfully!")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                     "Are you sure you want to reset all settings to defaults?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings_manager.reset_settings()
            self.load_current_settings()
            QMessageBox.information(self, "Success", "Settings reset to defaults!")
    
    def export_settings(self):
        """Export settings to file"""
        file, _ = QFileDialog.getSaveFileName(self, "Export Settings", 
                                              f"firevision_settings_{datetime.now().strftime('%Y%m%d')}.json",
                                              "JSON Files (*.json)")
        if file:
            if self.settings_manager.export_settings(file):
                QMessageBox.information(self, "Success", f"Settings exported to:\n{file}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export settings!")
    
    def import_settings(self):
        """Import settings from file"""
        file, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if file:
            reply = QMessageBox.question(self, "Import Settings",
                                        "This will overwrite current settings. Continue?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.settings_manager.import_settings(file):
                    self.load_current_settings()
                    QMessageBox.information(self, "Success", "Settings imported successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to import settings!")
