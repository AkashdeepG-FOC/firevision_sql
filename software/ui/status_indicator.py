from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QVariantAnimation, pyqtProperty
from PyQt5.QtGui import QColor, QFont

class SystemStatusIndicator(QWidget):
    """
    Real-time system connectivity status indicator badge.
    Displays ONLINE, OFFLINE, SYNCING, or LIMITED CONNECTIVITY
    with smooth color transitions.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = "unknown"
        self._bg_color = QColor(100, 100, 100) # Default gray
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 6, 12, 6)
        self.layout.setSpacing(8)
        
        self.icon_label = QLabel("⚪")
        self.text_label = QLabel("Connecting...")
        
        font = QFont("Segoe UI", 10, QFont.Bold)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: white; background: transparent;")
        self.icon_label.setStyleSheet("background: transparent;")
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.update_style()
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

    @pyqtProperty(QColor)
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, color):
        self._bg_color = color
        self.update_style()

    def update_style(self):
        """Update the stylesheet using the current background color."""
        r, g, b, a = self._bg_color.getRgb()
        self.setStyleSheet(f"""
            SystemStatusIndicator {{
                background-color: rgba({r}, {g}, {b}, 0.8);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)

    def set_status(self, data: dict):
        """Update the indicator based on status data from the Local API."""
        mode = data.get("mode", "offline")
        if mode == self.current_mode and mode != "syncing":
            # If syncing, we want to update the text to show remaining queue
            return
            
        self.current_mode = mode
        
        target_color = QColor(100, 100, 100)
        text = "Unknown"
        icon = "⚪"
        
        if mode == "online":
            target_color = QColor(34, 197, 94) # Green
            text = "Connected to Cloud"
            icon = "🟢"
        elif mode == "offline":
            target_color = QColor(239, 68, 68) # Red
            text = "Offline Mode Active"
            icon = "🔴"
        elif mode == "syncing":
            target_color = QColor(234, 179, 8) # Yellow
            pending = data.get("sync_pending", 0)
            text = f"Synchronizing Events ({pending})"
            icon = "🟡"
        elif mode == "limited":
            target_color = QColor(249, 115, 22) # Orange
            text = "Limited Connectivity"
            icon = "🟠"
            
        self.text_label.setText(text)
        self.icon_label.setText(icon)
        
        self.animate_color(target_color)
        
    def animate_color(self, target_color):
        """Smoothly transition the background color."""
        self.animation = QPropertyAnimation(self, b"bg_color")
        self.animation.setDuration(500)
        self.animation.setStartValue(self._bg_color)
        self.animation.setEndValue(target_color)
        self.animation.start()
