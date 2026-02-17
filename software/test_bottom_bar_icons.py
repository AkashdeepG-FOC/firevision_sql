#!/usr/bin/env python3
"""
Test the bottom bar icons to make sure they're visible
"""

import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

def set_button_icon(button, icon_path, fallback_text):
    """Set icon for button with fallback to text"""
    try:
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(28, 28))
            button.setText("")
            print(f"✅ Icon set: {icon_path}")
            return True
        else:
            button.setText(fallback_text)
            button.setIcon(QIcon())
            print(f"❌ Icon not found, using fallback: {icon_path}")
            return False
    except Exception as e:
        print(f"❌ Error setting button icon {icon_path}: {e}")
        button.setText(fallback_text)
        button.setIcon(QIcon())
        return False

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Bottom Bar Icons Test")
    window.setGeometry(100, 100, 800, 150)
    window.setStyleSheet("background-color: #1a1a1a;")
    
    layout = QHBoxLayout(window)
    
    # Button styles from the app
    toggle_button_style = """
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #505050;
            border-radius: 20px;
            padding: 4px;
        }
        QPushButton:checked {
            background-color: #00aa00;
            border-color: #00cc00;
        }
        QPushButton:hover {
            border-color: #707070;
        }
    """
    
    # Test icons from the bottom bar
    icons_to_test = [
        ("assests/icons/previous.png", "⏮️", "Previous"),
        ("assests/icons/play.png", "▶️", "Play"),
        ("assests/icons/next.png", "⏭️", "Next"),
        ("assests/icons/people.png", "👥", "People"),
        ("assests/icons/fire.png", "🔥", "Fire"),
        ("assests/icons/record.png", "⏺", "Record"),
        ("assests/icons/auto.png", "🤖", "Auto"),
        ("assests/icons/zoom_out.png", "🔍-", "Zoom Out"),
        ("assests/icons/zoom_in.png", "🔍+", "Zoom In"),
        ("assests/icons/water.png", "💧", "Water"),
        ("assests/icons/fan.png", "🌀", "Fan"),
    ]
    
    for icon_path, fallback, label_text in icons_to_test:
        # Create button
        btn = QPushButton()
        btn.setFixedSize(40, 40)
        btn.setStyleSheet(toggle_button_style)
        btn.setCheckable(True)
        
        # Set icon
        success = set_button_icon(btn, icon_path, fallback)
        
        # Create label
        label = QLabel(label_text)
        label.setStyleSheet("color: white; font-size: 10px;")
        label.setFixedWidth(60)
        
        # Add to layout
        layout.addWidget(btn)
        layout.addWidget(label)
    
    window.show()
    
    print("\\n🎨 Bottom bar icons test window created.")
    print("Check if all icons are visible. Close window to exit.")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())