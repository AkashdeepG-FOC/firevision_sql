#!/usr/bin/env python3
"""
Debug script to test icon display in buttons with different styles
"""

import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

def set_button_icon(button, icon_path, fallback_text):
    """Set icon for button with fallback to text"""
    try:
        print(f"Setting icon: {icon_path}")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(24, 24))
            button.setText("")
            print(f"✅ Icon set successfully: {not icon.isNull()}")
        else:
            button.setText(fallback_text)
            button.setIcon(QIcon())
            print(f"❌ Icon file not found, using fallback: {fallback_text}")
    except Exception as e:
        print(f"❌ Error setting button icon {icon_path}: {e}")
        button.setText(fallback_text)
        button.setIcon(QIcon())

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Icon Debug Test")
    window.setGeometry(100, 100, 600, 200)
    window.setStyleSheet("background-color: #2d2d2d;")
    
    layout = QHBoxLayout(window)
    
    # Test 1: Button with no special styling
    btn1 = QPushButton()
    btn1.setFixedSize(40, 40)
    set_button_icon(btn1, "assests/icons/fire.png", "🔥")
    
    label1 = QLabel("No Style")
    label1.setStyleSheet("color: white;")
    
    # Test 2: Button with circular styling (like in the app)
    btn2 = QPushButton()
    btn2.setFixedSize(40, 40)
    btn2.setStyleSheet("""
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #505050;
            border-radius: 20px;
            padding: 8px;
        }
        QPushButton:hover {
            border-color: #707070;
        }
    """)
    set_button_icon(btn2, "assests/icons/fire.png", "🔥")
    
    label2 = QLabel("Circular Style")
    label2.setStyleSheet("color: white;")
    
    # Test 3: Button with text to see if styling affects text
    btn3 = QPushButton("🔥")
    btn3.setFixedSize(40, 40)
    btn3.setStyleSheet("""
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #505050;
            border-radius: 20px;
            padding: 8px;
        }
    """)
    
    label3 = QLabel("Text Only")
    label3.setStyleSheet("color: white;")
    
    # Test 4: Button with both icon and text
    btn4 = QPushButton()
    btn4.setFixedSize(40, 40)
    btn4.setStyleSheet("""
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #505050;
            border-radius: 20px;
            padding: 8px;
        }
    """)
    icon = QIcon("assests/icons/fire.png")
    btn4.setIcon(icon)
    btn4.setIconSize(QSize(24, 24))
    btn4.setText("🔥")  # Set both icon and text
    
    label4 = QLabel("Icon + Text")
    label4.setStyleSheet("color: white;")
    
    # Add to layout
    layout.addWidget(btn1)
    layout.addWidget(label1)
    layout.addWidget(btn2)
    layout.addWidget(label2)
    layout.addWidget(btn3)
    layout.addWidget(label3)
    layout.addWidget(btn4)
    layout.addWidget(label4)
    
    window.show()
    
    print("Debug window created. Check which buttons show icons correctly.")
    print("Close the window to exit.")
    
    app.exec_()

if __name__ == "__main__":
    main()