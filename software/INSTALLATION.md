# Fire Vision Pro - Installation Guide

## 🚀 Quick Start

### Windows Users
1. Double-click `install_dependencies.bat`
2. Wait for installation to complete
3. Run `python main.py`

### Linux/Mac Users
1. Open terminal in project directory
2. Run: `chmod +x install_dependencies.sh && ./install_dependencies.sh`
3. Run: `python3 main.py`

## 📋 System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Camera**: Webcam or IP camera for testing
- **Internet**: Required for Google Drive features

## 🔧 Manual Installation

### Step 1: Install Python
Download and install Python 3.8+ from [python.org](https://python.org)

### Step 2: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation
```bash
python -c "import cv2, PyQt5, ultralytics, torch; print('All packages installed successfully!')"
```

## 📦 Package Details

### Core Dependencies
- **opencv-python**: Computer vision library
- **numpy**: Numerical computing
- **PyQt5**: GUI framework
- **requests**: HTTP library
- **websocket-client**: WebSocket support

### AI/ML Dependencies
- **ultralytics**: YOLOv8 object detection
- **torch**: PyTorch deep learning
- **torchvision**: Computer vision for PyTorch

### PyQt5 Components
- **PyQt5-QtWebEngine**: Web browser component
- **PyQt5-QtMultimedia**: Media playback
- **PyQt5-QtMultimediaWidgets**: Media widgets

### Additional Libraries
- **folium**: Interactive maps
- **pillow**: Image processing
- **google-api-python-client**: Google Drive integration

## 🐛 Troubleshooting

### Common Issues

#### PyQt5 Installation Fails
```bash
# Try alternative installation
pip install PyQt5-tools
pip install PyQt5-QtWebEngine
```

#### Torch Installation Issues
Visit [pytorch.org](https://pytorch.org/get-started/locally/) for platform-specific installation.

#### OpenCV Issues
```bash
# Try alternative
pip uninstall opencv-python
pip install opencv-python-headless
```

#### Permission Errors (Linux/Mac)
```bash
# Use user installation
pip install --user -r requirements.txt
```

### Network Issues
If you're behind a proxy or firewall:
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## 🚀 Running the Application

### Main Application
```bash
python main.py
```

### Background Service
```bash
python run_background_service.py
```

### With Splash Screen
```bash
python splash_screen.py
```

## 📁 Project Structure

```
FireVisionPro/
├── main.py                    # Main application
├── requirements.txt           # Dependencies
├── install_requirements.py    # Installation script
├── install_dependencies.bat   # Windows installer
├── install_dependencies.sh    # Linux/Mac installer
├── config/                    # Configuration files
├── data/                      # Data storage
├── recordings/                # Video recordings
├── thumbnails/                # Event thumbnails
└── models/                    # AI models
```

## 🔐 First Time Setup

1. **Configure Cameras**: Add your cameras in the application
2. **Google Drive**: Set up credentials for cloud backup
3. **Detection Settings**: Adjust sensitivity as needed
4. **Storage**: Configure recording storage location

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify Python version: `python --version`
3. Check installed packages: `pip list`
4. Review error logs in the application

## 🔄 Updates

To update dependencies:
```bash
pip install --upgrade -r requirements.txt
```

## 📝 License

This project is proprietary software. Please refer to the license agreement. 