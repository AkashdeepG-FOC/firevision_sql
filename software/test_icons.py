#!/usr/bin/env python3
"""
Test script to verify the icon files are created and accessible.
"""

import os
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

def test_icons():
    """Test if icon files exist and can be loaded"""
    icons_dir = "assests/icons"
    
    if not os.path.exists(icons_dir):
        print(f"❌ Icons directory not found: {icons_dir}")
        return False
    
    icon_files = [
        "play.png", "pause.png", "stop.png", "record.png",
        "previous.png", "next.png", "people.png", "fire.png",
        "auto.png", "zoom_in.png", "zoom_out.png"
    ]
    
    print("🔍 Checking icon files:")
    all_exist = True
    
    for icon_file in icon_files:
        icon_path = os.path.join(icons_dir, icon_file)
        if os.path.exists(icon_path):
            print(f"  ✅ {icon_file}")
        else:
            print(f"  ❌ {icon_file} - NOT FOUND")
            all_exist = False
    
    return all_exist

def create_test_ui():
    """Create a simple test UI to show the icons"""
    app = QApplication([])
    
    window = QWidget()
    window.setWindowTitle("Icon Test")
    window.setGeometry(100, 100, 600, 100)
    
    layout = QHBoxLayout(window)
    
    icons = [
        ("play.png", "Play"),
        ("pause.png", "Pause"),
        ("record.png", "Record"),
        ("people.png", "People"),
        ("fire.png", "Fire"),
        ("zoom_in.png", "Zoom In")
    ]
    
    for icon_file, tooltip in icons:
        btn = QPushButton()
        btn.setFixedSize(50, 50)
        btn.setToolTip(tooltip)
        
        icon_path = os.path.join("assests/icons", icon_file)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            btn.setIcon(icon)
            btn.setIconSize(QSize(32, 32))
        else:
            btn.setText(tooltip[:2])
        
        layout.addWidget(btn)
    
    window.show()
    print("📱 Test UI created. Close the window to exit.")
    app.exec_()

if __name__ == "__main__":
    print("🧪 Testing icon files...")
    
    if test_icons():
        print("\n✅ All icon files found!")
        print("\n🎨 Creating test UI to display icons...")
        create_test_ui()
    else:
        print("\n❌ Some icon files are missing. Run create_icons.py first.")