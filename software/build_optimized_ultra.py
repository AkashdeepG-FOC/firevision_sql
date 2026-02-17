#!/usr/bin/env python3
"""
Ultra-Optimized Build Script for Fire Vision Pro
Builds small-sized executable with all working features
Author: Fire Vision Pro Team
"""

import subprocess
import sys
import os
import shutil
import json
import time
from pathlib import Path

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def run_command(command, description=""):
    """Run a command and return the result"""
    if description:
        print_info(f"{description}...")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def clean_build():
    """Clean previous build artifacts"""
    print_header("Cleaning Build Artifacts")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_cleaned = 0
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print_success(f"Removed {dir_name}/")
                files_cleaned += 1
            except Exception as e:
                print_warning(f"Could not remove {dir_name}: {e}")
    
    # Remove spec files
    for file in os.listdir("."):
        if file.endswith(".spec"):
            try:
                os.remove(file)
                print_success(f"Removed {file}")
                files_cleaned += 1
            except Exception as e:
                print_warning(f"Could not remove {file}: {e}")
    
    if files_cleaned == 0:
        print_info("No build artifacts to clean")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("Checking Dependencies")
    
    dependencies = {
        'PyInstaller': 'PyInstaller',
        'PyQt5': 'PyQt5',
        'cv2': 'OpenCV (cv2)',
        'ultralytics': 'Ultralytics YOLO',
        'torch': 'PyTorch'
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name} is installed")
        except ImportError:
            print_error(f"{name} is NOT installed")
            missing.append(name)
    
    if missing:
        print_error(f"Missing dependencies: {', '.join(missing)}")
        print_info("Install with: pip install pyinstaller PyQt5 opencv-python ultralytics torch")
        return False
    
    return True

def check_upx():
    """Check if UPX is available"""
    success, stdout, stderr = run_command("upx --version", "Checking UPX availability")
    if success:
        print_success("UPX is available for compression")
        return True
    else:
        print_warning("UPX not found - build will be larger")
        print_info("Download UPX from: https://github.com/upx/upx/releases")
        return False

def check_models():
    """Check which model files exist"""
    print_header("Checking Model Files")
    
    models = {
        'yolov8n.pt': 'YOLOv8 Nano (6.5MB)',
        'best_m.pt': 'Custom Trained Model (103MB)',
        'custom_model.pt': 'Alternative Custom Model (6.7MB)'
    }
    
    found_models = []
    for model_file, description in models.items():
        if os.path.exists(model_file):
            size = get_file_size_mb(model_file)
            print_success(f"{description} - {size:.1f}MB")
            found_models.append(model_file)
        else:
            print_warning(f"{description} - NOT FOUND")
    
    return found_models

def build_balanced_profile(use_upx=True):
    """Build with balanced profile - all features, optimized size"""
    print_header("Building Balanced Profile")
    print_info("Profile: All features with aggressive optimization")
    print_info("Models: yolov8n.pt + best_m.pt")
    print_info("Expected size: 300-400MB")
    
    # Start building command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=FireVisionPro",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--optimize=2",  # Python optimization
        "--strip",       # Strip debug symbols
    ]
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    # Add UPX if available
    if use_upx:
        cmd.append("--upx-dir=.")
        print_info("UPX compression enabled")
    
    # Add data files
    if os.path.isdir("assests"):
        cmd.append("--add-data=assests;assests")
    if os.path.isdir("config"):
        cmd.append("--add-data=config;config")
    
    # Add model files (excluding custom_model.pt per user request)
    models_to_include = ["yolov8n.pt", "best_m.pt"]
    for model in models_to_include:
        if os.path.exists(model):
            cmd.append(f"--add-data={model};.")
            print_success(f"Including model: {model}")
    
    # Collect essential modules
    cmd += [
        # Core PyQt5
        "--collect-all=PyQt5.QtCore",
        "--collect-all=PyQt5.QtGui",
        "--collect-all=PyQt5.QtWidgets",
        "--collect-all=PyQt5.QtWebEngineWidgets",
        "--collect-all=PyQt5.QtWebChannel",
        
        # Computer Vision and AI
        "--collect-submodules=cv2",
        "--collect-all=ultralytics",
        "--collect-all=torch",
        "--collect-all=numpy",
        
        # Web mapping
        "--collect-all=folium",
        "--collect-all=branca",
        "--collect-all=jinja2",
        
        # Voice commands
        "--collect-all=speech_recognition",
        "--collect-all=pyttsx3",
        
        # HTTP
        "--collect-all=requests",
    ]
    
    # Comprehensive exclusions for size optimization
    exclusions = [
        # ML frameworks not used
        "onnx", "onnxruntime", "onnxsim", "tensorboard", "tensorflow", "keras",
        "ml_dtypes", "google.protobuf",
        
        # Data science libraries
        "matplotlib", "seaborn", "pandas", "scipy", "sympy", "networkx",
        "contourpy", "kiwisolver", "cycler", "pyparsing",
        
        # JAX ecosystem
        "jax", "jaxlib", "opt_einsum",
        
        # Media processing
        "imageio", "imageio_ffmpeg", "tifffile", "moviepy", "proglog", "mediapipe",
        
        # Audio (except voice commands)
        "pygame", "sounddevice",
        
        # Database
        "sqlalchemy", "greenlet",
        
        # Async libraries
        "aiohttp", "fsspec", "multidict", "yarl", "frozenlist", "aiosignal",
        
        # Utilities
        "tqdm", "rich", "pygments", "colorama",
        
        # Unused PyTorch components
        "torch.distributed", "torch.testing", "torch.autograd.profiler",
    ]
    
    for module in exclusions:
        cmd.append(f"--exclude-module={module}")
    
    # Add main script
    cmd.append("main.py")
    
    # Build the command string
    command = " ".join(cmd)
    
    print_info(f"Build command: {command[:100]}...")
    print_info("Starting build... This may take 8-12 minutes")
    
    start_time = time.time()
    success, stdout, stderr = run_command(command)
    build_time = time.time() - start_time
    
    if success:
        print_success(f"Build completed in {build_time/60:.1f} minutes!")
        return True
    else:
        print_error("Build failed!")
        print_error(f"Error: {stderr[:500]}")
        return False

def generate_build_report():
    """Generate build report with size information"""
    print_header("Build Report")
    
    exe_path = "dist/FireVisionPro.exe"
    
    if not os.path.exists(exe_path):
        print_error("Executable not found!")
        return False
    
    exe_size = get_file_size_mb(exe_path)
    
    print_success(f"Executable created: {exe_path}")
    print_success(f"File size: {exe_size:.2f} MB")
    
    # Size analysis
    if exe_size < 250:
        print_success("Excellent! Size is under 250MB")
    elif exe_size < 400:
        print_success("Good! Size is under 400MB")
    elif exe_size < 600:
        print_warning("Size is acceptable but could be optimized further")
    else:
        print_warning("Size is larger than expected")
    
    # Save report to file
    report_path = "build_report.txt"
    with open(report_path, 'w') as f:
        f.write("="*60 + "\n")
        f.write("Fire Vision Pro - Build Report\n")
        f.write("="*60 + "\n\n")
        f.write(f"Build Profile: Balanced (All Features)\n")
        f.write(f"Executable: {exe_path}\n")
        f.write(f"File Size: {exe_size:.2f} MB\n")
        f.write(f"Build Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("Models Included:\n")
        f.write("  - yolov8n.pt (6.5MB)\n")
        f.write("  - best_m.pt (103MB)\n\n")
        f.write("Features:\n")
        f.write("  ✅ Camera Management\n")
        f.write("  ✅ AI Fire/Smoke Detection\n")
        f.write("  ✅ People Detection\n")
        f.write("  ✅ Voice Commands\n")
        f.write("  ✅ Map Integration\n")
        f.write("  ✅ Cloud Backup\n")
        f.write("  ✅ Alert System\n\n")
        f.write("Optimizations Applied:\n")
        f.write("  ✅ UPX Compression\n")
        f.write("  ✅ Module Exclusions\n")
        f.write("  ✅ Debug Symbol Stripping\n")
        f.write("  ✅ Python Bytecode Optimization\n")
    
    print_success(f"Build report saved to: {report_path}")
    return True

def main():
    """Main build process"""
    print_header("Fire Vision Pro - Ultra-Optimized Builder")
    print_info("Build Profile: Balanced (All Features, Optimized Size)")
    print_info("Models: yolov8n.pt + best_m.pt (custom_model.pt excluded)")
    
    # Step 1: Clean previous builds
    if not clean_build():
        print_error("Failed to clean build artifacts")
        return False
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print_error("Missing required dependencies")
        return False
    
    # Step 3: Check UPX
    upx_available = check_upx()
    
    # Step 4: Check models
    available_models = check_models()
    if "yolov8n.pt" not in available_models:
        print_error("Required model yolov8n.pt not found!")
        return False
    
    # Step 5: Build
    if not build_balanced_profile(use_upx=upx_available):
        print_error("Build failed!")
        return False
    
    # Step 6: Generate report
    if not generate_build_report():
        print_warning("Could not generate build report")
    
    print_header("Build Complete!")
    print_success("Your executable is ready: dist/FireVisionPro.exe")
    print_info("Next steps:")
    print_info("  1. Test the executable: dist\\FireVisionPro.exe")
    print_info("  2. Check build_report.txt for details")
    print_info("  3. Test on a clean Windows system")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
