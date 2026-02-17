#!/usr/bin/env python3
"""
Voice Command Dependencies Installer for FireVision Pro
This script installs the required packages for voice command functionality.
"""

import subprocess
import sys
import os
import platform

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required for voice commands")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_package(package_name, pip_name=None):
    """Install a package using pip"""
    if pip_name is None:
        pip_name = package_name
    
    print(f"📦 Installing {package_name}...")
    success, output = run_command(f"{sys.executable} -m pip install {pip_name}")
    
    if success:
        print(f"✅ {package_name} installed successfully")
        return True
    else:
        print(f"❌ Failed to install {package_name}: {output}")
        return False

def install_system_dependencies():
    """Install system-specific dependencies"""
    system = platform.system().lower()
    
    if system == "windows":
        print("🪟 Windows detected")
        print("📝 Note: PyAudio installation on Windows may require Microsoft Visual C++ Build Tools")
        print("💡 If installation fails, try: pip install pipwin && pipwin install pyaudio")
        
    elif system == "linux":
        print("🐧 Linux detected")
        print("📦 Installing system audio dependencies...")
        
        # Try to install portaudio development package
        success, _ = run_command("sudo apt-get update")
        if success:
            run_command("sudo apt-get install -y portaudio19-dev python3-pyaudio")
        else:
            print("⚠️ Could not update package list. You may need to install portaudio19-dev manually")
            
    elif system == "darwin":
        print("🍎 macOS detected")
        print("📦 Installing system audio dependencies...")
        run_command("brew install portaudio")
        
    else:
        print(f"⚠️ Unknown system: {system}")
        print("You may need to install audio dependencies manually")

def main():
    """Main installation function"""
    print("🎤 FireVision Pro Voice Command Dependencies Installer")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install system dependencies
    install_system_dependencies()
    
    print("\n📦 Installing Python packages...")
    
    # List of packages to install
    packages = [
        ("SpeechRecognition", "SpeechRecognition>=3.8.1"),
        ("pyttsx3", "pyttsx3>=2.90"),
        ("PyAudio", "pyaudio>=0.2.11"),
        ("OpenAI Whisper", "openai-whisper>=20231117")
    ]
    
    failed_packages = []
    
    for package_name, pip_name in packages:
        if not install_package(package_name, pip_name):
            failed_packages.append(package_name)
    
    print("\n" + "=" * 50)
    
    if failed_packages:
        print("❌ Some packages failed to install:")
        for package in failed_packages:
            print(f"   - {package}")
        
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure you have pip installed and updated")
        print("2. Try running: pip install --upgrade pip")
        print("3. On Windows, you may need Microsoft Visual C++ Build Tools")
        print("4. For PyAudio issues, try: pip install pipwin && pipwin install pyaudio")
        print("5. On Linux, make sure you have portaudio19-dev installed")
        
        return False
    else:
        print("✅ All voice command dependencies installed successfully!")
        print("\n🎉 Voice commands are now ready to use!")
        print("💡 To test voice commands:")
        print("   1. Start FireVision Pro")
        print("   2. Go to 'Voice Commands' in the sidebar")
        print("   3. Click 'Use Whisper' for better accuracy")
        print("   4. Click 'Start Listening'")
        print("   5. Say 'Fire Vision' followed by your command")
        print("\n🎯 Whisper provides much better accuracy than Google Speech Recognition!")
        
        return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🚀 Installation completed successfully!")
        else:
            print("\n⚠️ Installation completed with errors. Please check the troubleshooting tips above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 