#!/bin/bash

echo "========================================"
echo "Fire Vision Pro - Dependency Installer"
echo "========================================"
echo

echo "Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo
echo "Installing all dependencies..."
python3 install_requirements.py

echo
echo "Installation complete!"
echo
echo "To run Fire Vision Pro:"
echo "  python3 main.py"
echo
echo "To run background service:"
echo "  python3 run_background_service.py"
echo 