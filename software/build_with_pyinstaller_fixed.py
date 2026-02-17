#!/usr/bin/env python3
"""
Fixed PyInstaller Build Script for Fire Vision Pro
Excludes problematic modules and uses optimized settings
"""

import subprocess
import sys
import os
import shutil

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")
    
    # Remove spec files
    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)
            print(f"✅ Removed {file}")

def build_simple():
    """Build with simple PyInstaller command"""
    print("🔨 Building with simple PyInstaller command...")
    
    # Start with base command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=FireVisionPro",
        "--icon=icon.ico",
    ]

    # Add existing data folders
    if os.path.isdir("assests"):
        cmd.append("--add-data=assests;assests")
    if os.path.isdir("config"):
        cmd.append("--add-data=config;config")

    # Add optional model files only if present
    for weight in [
        "yolov8n.pt",
        "yolov8s.pt",
        "yolov8m.pt",
        "yolov8x.pt",
        "best_m.pt",
        "custom_model.pt",
    ]:
        if os.path.exists(weight):
            cmd.append(f"--add-data={weight};.")

    # Collect only the modules actually used in Fire Vision Pro
    cmd += [
        # Core PyQt5 modules used
        "--collect-all=PyQt5.QtCore",
        "--collect-all=PyQt5.QtGui", 
        "--collect-all=PyQt5.QtWidgets",
        "--collect-all=PyQt5.QtWebEngineWidgets",
        "--collect-all=PyQt5.QtWebChannel",
        
        # Computer Vision and AI
        "--collect-submodules=cv2",
        "--collect-all=ultralytics",
        "--collect-all=torch",
        "--collect-all=torchvision",
        "--collect-all=numpy",
        
        # Web mapping
        "--collect-all=folium",
        "--collect-all=branca",
        "--collect-all=jinja2",
        "--collect-all=markupsafe",
        
        # Voice commands (optional)
        "--collect-all=speech_recognition",
        "--collect-all=pyttsx3",
        "--collect-all=pydub",
        "--collect-all=noisereduce",
        "--collect-all=webrtcvad",
        "--collect-all=whisper",
        
        # HTTP requests
        "--collect-all=requests",
        
        # Date/time handling
        "--collect-all=pytz",
    ]

    # Exclude heavy/unused modules - comprehensive list for lean build
    cmd += [
        # Machine Learning frameworks not used
        "--exclude-module=onnx",
        "--exclude-module=onnxruntime", 
        "--exclude-module=onnxsim",
        "--exclude-module=tensorboard",
        "--exclude-module=tensorflow",
        "--exclude-module=keras",
        "--exclude-module=ml_dtypes",
        "--exclude-module=google.protobuf",
        
        # Data science libraries not used
        "--exclude-module=matplotlib",
        "--exclude-module=seaborn",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=sympy",
        "--exclude-module=networkx",
        "--exclude-module=contourpy",
        "--exclude-module=kiwisolver",
        "--exclude-module=cycler",
        "--exclude-module=pyparsing",
        
        # JAX ecosystem
        "--exclude-module=jax",
        "--exclude-module=jaxlib",
        "--exclude-module=opt_einsum",
        
        # Google services not used
        "--exclude-module=google.auth",
        "--exclude-module=google.oauth2", 
        "--exclude-module=google.api_core",
        "--exclude-module=googleapiclient",
        "--exclude-module=httplib2",
        "--exclude-module=uritemplate",
        "--exclude-module=google_auth_oauthlib",
        "--exclude-module=requests_oauthlib",
        "--exclude-module=oauthlib",
        "--exclude-module=jwt",
        
        # Media processing not used
        "--exclude-module=imageio",
        "--exclude-module=imageio_ffmpeg",
        "--exclude-module=tifffile",
        "--exclude-module=moviepy",
        "--exclude-module=proglog",
        "--exclude-module=mediapipe",
        
        # Audio processing not used (except voice commands)
        "--exclude-module=pygame",
        "--exclude-module=sounddevice",
        "--exclude-module=_sounddevice_data",
        
        # Database and ORM
        "--exclude-module=sqlalchemy",
        "--exclude-module=greenlet",
        
        # Async libraries not used
        "--exclude-module=aiohttp",
        "--exclude-module=fsspec",
        "--exclude-module=multidict",
        "--exclude-module=yarl",
        "--exclude-module=frozenlist",
        "--exclude-module=aiosignal",
        "--exclude-module=aiohappyeyeballs",
        
        # Windows specific not needed
        "--exclude-module=win32com",
        "--exclude-module=pywin",
        "--exclude-module=pythoncom",
        "--exclude-module=pywintypes",
        
        # Utilities not used
        "--exclude-module=tqdm",
        "--exclude-module=rich",
        "--exclude-module=pygments",
        "--exclude-module=colorama",
        "--exclude-module=cachetools",
        "--exclude-module=filelock",
        "--exclude-module=propcache",
        "--exclude-module=zstandard",
        "--exclude-module=blinker",
        "--exclude-module=wsgiref",
        "--exclude-module=websocket",
        
        # Security libraries not used
        "--exclude-module=bcrypt",
        "--exclude-module=cryptography",
        "--exclude-module=cffi",
        "--exclude-module=pycparser",
        "--exclude-module=rsa",
        "--exclude-module=pyasn1",
        "--exclude-module=pyasn1_modules",
        
        # Other heavy modules
        "--exclude-module=cloudpickle",
        "--exclude-module=thop",
        "--exclude-module=cpuinfo",
        "--exclude-module=lap",
        "--exclude-module=defusedxml",
        "--exclude-module=markdown_it",
        "--exclude-module=mdurl",
        "--exclude-module=astunparse",
        "--exclude-module=h5py",
        "--exclude-module=psutil",
    ]

    # Entry script
    cmd.append("main.py")
    
    command = " ".join(cmd)
    print(f"🚀 Running: {command}")
    
    success, stdout, stderr = run_command(command)
    
    if success:
        print("✅ Build completed successfully!")
        print("📁 Executable location: dist/FireVisionPro.exe")
        return True
    else:
        print("❌ Build failed:")
        print(stderr)
        return False

def build_minimal():
    """Build with minimal dependencies"""
    print("🔨 Building with minimal dependencies...")
    
    # Create a minimal main file for testing
    minimal_main = '''
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

class MinimalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fire Vision Pro - Minimal Build")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        label = QLabel("Fire Vision Pro - Minimal Build Successful!")
        label.setStyleSheet("font-size: 24px; color: #00BFAE;")
        layout.addWidget(label)
        
        status_label = QLabel("This is a minimal build to test PyInstaller compatibility")
        status_label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(status_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimalApp()
    window.show()
    sys.exit(app.exec_())
'''
    
    with open("minimal_main.py", "w") as f:
        f.write(minimal_main)
    
    # Build minimal version
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=FireVisionPro_Minimal",
        "--icon=icon.ico",
        "minimal_main.py"
    ]
    
    command = " ".join(cmd)
    print(f"🚀 Running: {command}")
    
    success, stdout, stderr = run_command(command)
    
    if success:
        print("✅ Minimal build completed successfully!")
        print("📁 Executable location: dist/FireVisionPro_Minimal.exe")
        return True
    else:
        print("❌ Minimal build failed:")
        print(stderr)
        return False

def create_optimized_spec():
    """Create an optimized spec file"""
    print("📝 Creating optimized spec file...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assests', 'assests'),
        ('config', 'config'),
        ('yolov8n.pt', '.'),
        ('yolov8s.pt', '.'),
        ('yolov8m.pt', '.'),
        ('yolov8x.pt', '.'),
        ('best_m.pt', '.'),
        ('custom_model.pt', '.'),
    ],
    hiddenimports=[
        # Core PyQt5 modules
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebChannel',
        
        # Computer Vision and AI
        'cv2',
        'ultralytics',
        'torch',
        'torchvision',
        'numpy',
        
        # Web mapping
        'folium',
        'branca',
        'jinja2',
        'markupsafe',
        
        # Voice commands (optional)
        'speech_recognition',
        'pyttsx3',
        'pydub',
        'noisereduce',
        'webrtcvad',
        'whisper',
        
        # HTTP and utilities
        'requests',
        'pytz',
        
        # Custom modules
        'config_manager',
        'background_service',
        'google_drive_manager',
        'recordings_page',
        'recording_manager',
        'stream_manager',
        'enhanced_camera_manager',
        'ui_components',
        'enhanced_fullscreen_widget',
        'enhanced_review_system',
        'fire_detection_backend',
        'notification_manager',
        'alerts_manager',
        'cloud_backup_manager',
        'user_managers',
        'voice_command_manager',
        'splash_screen',
        'DeviceSettings',
        'AdvancedCamera',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Machine Learning frameworks not used
        'onnx', 'onnxruntime', 'onnxsim', 'tensorboard', 'tensorflow', 'keras', 
        'ml_dtypes', 'google.protobuf',
        
        # Data science libraries not used
        'matplotlib', 'seaborn', 'pandas', 'scipy', 'sympy', 'networkx',
        'contourpy', 'kiwisolver', 'cycler', 'pyparsing',
        
        # JAX ecosystem
        'jax', 'jaxlib', 'opt_einsum',
        
        # Google services not used
        'google.auth', 'google.oauth2', 'google.api_core', 'googleapiclient',
        'httplib2', 'uritemplate', 'google_auth_oauthlib', 'requests_oauthlib',
        'oauthlib', 'jwt',
        
        # Media processing not used
        'imageio', 'imageio_ffmpeg', 'tifffile', 'moviepy', 'proglog', 'mediapipe',
        
        # Audio processing not used (except voice commands)
        'pygame', 'sounddevice', '_sounddevice_data',
        
        # Database and ORM
        'sqlalchemy', 'greenlet',
        
        # Async libraries not used
        'aiohttp', 'fsspec', 'multidict', 'yarl', 'frozenlist', 'aiosignal', 
        'aiohappyeyeballs',
        
        # Windows specific not needed
        'win32com', 'pywin', 'pythoncom', 'pywintypes',
        
        # Utilities not used
        'tqdm', 'rich', 'pygments', 'colorama', 'cachetools', 'filelock',
        'propcache', 'zstandard', 'blinker', 'wsgiref', 'websocket',
        
        # Security libraries not used
        'bcrypt', 'cryptography', 'cffi', 'pycparser', 'rsa', 'pyasn1', 
        'pyasn1_modules',
        
        # Other heavy modules
        'cloudpickle', 'thop', 'cpuinfo', 'lap', 'defusedxml', 'markdown_it',
        'mdurl', 'astunparse', 'h5py', 'psutil'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FireVisionPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
"""
    
    with open("FireVisionPro_Optimized.spec", "w") as f:
        f.write(spec_content)
    
    print("✅ Created FireVisionPro_Optimized.spec")

def build_with_optimized_spec():
    """Build using the optimized spec file"""
    print("🔨 Building with optimized spec file...")
    
    success, stdout, stderr = run_command("pyinstaller FireVisionPro_Optimized.spec")
    
    if success:
        print("✅ Build completed successfully!")
        print("📁 Executable location: dist/FireVisionPro.exe")
        return True
    else:
        print("❌ Build failed:")
        print(stderr)
        return False

def build_lean():
    """Build with only essential modules for Fire Vision Pro"""
    print("🔨 Building lean Fire Vision Pro executable...")
    
    # Start with base command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=FireVisionPro_Lean",
        "--icon=icon.ico",
        "--optimize=2",  # Python optimization level
        "--strip",       # Strip debug symbols
    ]

    # Add existing data folders
    if os.path.isdir("assests"):
        cmd.append("--add-data=assests;assests")
    if os.path.isdir("config"):
        cmd.append("--add-data=config;config")

    # Add only essential model files
    essential_models = ["yolov8n.pt", "best_m.pt", "custom_model.pt"]
    for weight in essential_models:
        if os.path.exists(weight):
            cmd.append(f"--add-data={weight};.")

    # Only include absolutely necessary modules
    cmd += [
        # Core PyQt5 (only what's used)
        "--collect-all=PyQt5.QtCore",
        "--collect-all=PyQt5.QtGui", 
        "--collect-all=PyQt5.QtWidgets",
        "--collect-all=PyQt5.QtWebEngineWidgets",
        "--collect-all=PyQt5.QtWebChannel",
        
        # Essential CV and AI
        "--collect-submodules=cv2",
        "--collect-all=ultralytics",
        "--collect-all=torch",
        "--collect-all=numpy",
        
        # Web mapping (minimal)
        "--collect-all=folium",
        "--collect-all=branca",
        "--collect-all=jinja2",
        "--collect-all=markupsafe",
        
        # HTTP requests
        "--collect-all=requests",
        
        # Date/time handling
        "--collect-all=pytz",
    ]

    # Comprehensive exclusions for lean build
    cmd += [
        # Exclude everything not essential
        "--exclude-module=onnx", "--exclude-module=onnxruntime", "--exclude-module=onnxsim",
        "--exclude-module=tensorboard", "--exclude-module=tensorflow", "--exclude-module=keras",
        "--exclude-module=ml_dtypes", "--exclude-module=google.protobuf",
        "--exclude-module=matplotlib", "--exclude-module=seaborn", "--exclude-module=pandas",
        "--exclude-module=scipy", "--exclude-module=sympy", "--exclude-module=networkx",
        "--exclude-module=jax", "--exclude-module=jaxlib", "--exclude-module=opt_einsum",
        "--exclude-module=google.auth", "--exclude-module=google.oauth2", "--exclude-module=google.api_core",
        "--exclude-module=googleapiclient", "--exclude-module=httplib2", "--exclude-module=uritemplate",
        "--exclude-module=google_auth_oauthlib", "--exclude-module=requests_oauthlib", "--exclude-module=oauthlib",
        "--exclude-module=jwt", "--exclude-module=imageio", "--exclude-module=imageio_ffmpeg",
        "--exclude-module=tifffile", "--exclude-module=moviepy", "--exclude-module=proglog",
        "--exclude-module=mediapipe", "--exclude-module=pygame", "--exclude-module=sounddevice",
        "--exclude-module=_sounddevice_data", "--exclude-module=sqlalchemy", "--exclude-module=greenlet",
        "--exclude-module=aiohttp", "--exclude-module=fsspec", "--exclude-module=multidict",
        "--exclude-module=yarl", "--exclude-module=frozenlist", "--exclude-module=aiosignal",
        "--exclude-module=aiohappyeyeballs", "--exclude-module=win32com", "--exclude-module=pywin",
        "--exclude-module=pythoncom", "--exclude-module=pywintypes", "--exclude-module=tqdm",
        "--exclude-module=rich", "--exclude-module=pygments", "--exclude-module=colorama",
        "--exclude-module=cachetools", "--exclude-module=filelock", "--exclude-module=propcache",
        "--exclude-module=zstandard", "--exclude-module=blinker", "--exclude-module=wsgiref",
        "--exclude-module=websocket", "--exclude-module=bcrypt", "--exclude-module=cryptography",
        "--exclude-module=cffi", "--exclude-module=pycparser", "--exclude-module=rsa",
        "--exclude-module=pyasn1", "--exclude-module=pyasn1_modules", "--exclude-module=cloudpickle",
        "--exclude-module=thop", "--exclude-module=cpuinfo", "--exclude-module=lap",
        "--exclude-module=defusedxml", "--exclude-module=contourpy", "--exclude-module=kiwisolver",
        "--exclude-module=cycler", "--exclude-module=pyparsing", "--exclude-module=markdown_it",
        "--exclude-module=mdurl", "--exclude-module=astunparse", "--exclude-module=h5py",
        "--exclude-module=psutil",
        
        # Voice command modules (optional - exclude for lean build)
        "--exclude-module=speech_recognition", "--exclude-module=pyttsx3", "--exclude-module=pydub",
        "--exclude-module=noisereduce", "--exclude-module=webrtcvad", "--exclude-module=whisper",
    ]

    # Entry script
    cmd.append("main.py")
    
    command = " ".join(cmd)
    print(f"🚀 Running lean build: {command}")
    
    success, stdout, stderr = run_command(command)
    
    if success:
        print("✅ Lean build completed successfully!")
        print("📁 Executable location: dist/FireVisionPro_Lean.exe")
        print("📊 This build excludes voice commands and other optional features for minimal size")
        return True
    else:
        print("❌ Lean build failed:")
        print(stderr)
        return False

def main():
    """Main build process"""
    print("🚀 Fire Vision Pro - Fixed PyInstaller Builder")
    print("=" * 50)
    
    # Clean previous builds
    clean_build()
    
    # Ask user for build method
    print("\nChoose build method:")
    print("1. Simple build with exclusions (recommended)")
    print("2. Minimal build (test only)")
    print("3. Optimized build with spec file")
    print("4. Lean build (essential modules only - smallest size)")
    
    # Support non-interactive execution via CLI arg
    if len(sys.argv) > 1 and sys.argv[1] in {"1", "2", "3", "4"}:
        choice = sys.argv[1]
        print(f"\nEnter your choice (1-4): {choice}")
    else:
        choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        success = build_simple()
    elif choice == "2":
        success = build_minimal()
    elif choice == "3":
        create_optimized_spec()
        success = build_with_optimized_spec()
    elif choice == "4":
        success = build_lean()
    else:
        print("❌ Invalid choice")
        return
    
    if success:
        print("\n🎉 Build completed successfully!")
        print("📁 Your executable is ready in the 'dist' folder")
        print("🚀 You can now run the application")
    else:
        print("\n❌ Build failed. Check the error messages above.")
        print("\n💡 Try the minimal build option to test PyInstaller compatibility.")

if __name__ == "__main__":
    main() 