#!/usr/bin/env python3
"""
Installation script for Fire Vision Pro dependencies
Complete setup for new computer installation
"""

import subprocess
import sys
import os
import platform

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    try:
        print("🔄 Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ Pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")
        return False

def main():
    print("🚀 Fire Vision Pro - Complete Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Upgrade pip
    upgrade_pip()
    
    print("\n🔧 Installing Fire Vision Pro dependencies...")
    
    # Core packages (install in order of dependency)
    core_packages = [
        "numpy>=1.19.0",
        "pillow>=9.0.0",
        "requests>=2.25.0",
        "websocket-client>=1.2.0",
    ]
    
    # PyQt5 packages
    pyqt_packages = [
        "PyQt5>=5.15.0",
        "PyQt5-QtWebEngine>=5.15.0",
        "PyQt5-QtMultimedia>=5.15.0",
        "PyQt5-QtMultimediaWidgets>=5.15.0",
    ]
    
    # AI/ML packages
    ai_packages = [
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "ultralytics>=8.0.0",
    ]
    
    # Computer vision
    cv_packages = [
        "opencv-python>=4.5.0",
    ]
    
    # Web and mapping
    web_packages = [
        "folium>=0.12.0",
    ]
    
    # Google API packages
    google_packages = [
        "google-api-python-client>=2.0.0",
        "google-auth-httplib2>=0.1.0",
        "google-auth-oauthlib>=0.5.0",
    ]
    
    # Combine all packages
    all_packages = core_packages + pyqt_packages + ai_packages + cv_packages + web_packages + google_packages
    
    failed_packages = []
    
    print("\n📦 Installing core dependencies...")
    for package in core_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n🎨 Installing PyQt5 components...")
    for package in pyqt_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n🤖 Installing AI/ML dependencies...")
    for package in ai_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n👁️ Installing computer vision libraries...")
    for package in cv_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n🌐 Installing web and mapping libraries...")
    for package in web_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n☁️ Installing Google API libraries...")
    for package in google_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    if failed_packages:
        print(f"❌ Failed to install: {', '.join(failed_packages)}")
        print("\n🔧 Manual installation instructions:")
        for package in failed_packages:
            print(f"   pip install {package}")
        
        print("\n💡 Troubleshooting tips:")
        print("   - Try installing packages one by one")
        print("   - Check your internet connection")
        print("   - Try using: pip install --upgrade pip")
        print("   - For PyQt5 issues, try: pip install PyQt5-tools")
        print("   - For torch issues, visit: https://pytorch.org/get-started/locally/")
    else:
        print("✅ All dependencies installed successfully!")
        
        print("\n🎉 Fire Vision Pro is ready to use!")
        print("\n🚀 To start the application:")
        print("   python main.py")
        print("\n🔧 To run background service only:")
        print("   python run_background_service.py")
        print("\n📱 To run with splash screen:")
        print("   python splash_screen.py")
        
        print("\n📋 System requirements:")
        print("   - Python 3.8+")
        print("   - 4GB+ RAM recommended")
        print("   - Webcam or IP camera for testing")
        print("   - Internet connection for Google Drive features")
        
        print("\n🔗 Additional setup:")
        print("   - Configure cameras in the application")
        print("   - Set up Google Drive credentials if needed")
        print("   - Adjust detection sensitivity as needed")

if __name__ == "__main__":
    main()
