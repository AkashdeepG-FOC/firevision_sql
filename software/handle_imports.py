import os
import sys
import site
import shutil
import subprocess
import pkg_resources

def find_module_path(module_name):
    """Find the path to a module."""
    try:
        # Try to find using importlib
        import importlib
        module = importlib.import_module(module_name)
        return os.path.dirname(module.__file__)
    except (ImportError, AttributeError):
        # Try with pkg_resources
        try:
            dist = pkg_resources.get_distribution(module_name)
            return dist.location
        except pkg_resources.DistributionNotFound:
            return None

def copy_opencv_dlls(target_dir):
    """Copy OpenCV DLLs to the target directory."""
    cv2_path = find_module_path('cv2')
    if not cv2_path:
        print("ERROR: OpenCV (cv2) module not found.")
        return False
    
    print(f"Found OpenCV at {cv2_path}")
    
    # Look for OpenCV DLLs in the cv2 directory
    opencv_dlls = []
    for file in os.listdir(cv2_path):
        if file.lower().endswith('.dll'):
            opencv_dlls.append(os.path.join(cv2_path, file))
    
    # If we didn't find them in cv2 directory, try the parent directories
    if not opencv_dlls:
        parent_dir = os.path.dirname(cv2_path)
        for root, dirs, files in os.walk(parent_dir):
            for file in files:
                if file.lower().startswith('opencv_') and file.lower().endswith('.dll'):
                    opencv_dlls.append(os.path.join(root, file))
    
    # Make the target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy DLLs to the target directory
    copied_files = []
    for dll_path in opencv_dlls:
        dest_path = os.path.join(target_dir, os.path.basename(dll_path))
        shutil.copy2(dll_path, dest_path)
        copied_files.append(dest_path)
        print(f"Copied: {dll_path} -> {dest_path}")
    
    if copied_files:
        print(f"Successfully copied {len(copied_files)} OpenCV DLLs.")
        return True
    else:
        print("WARNING: No OpenCV DLLs were found to copy.")
        return False

def generate_hook_file():
    """Generate a hook file for PyInstaller."""
    hook_content = """
# PyInstaller hook for cv2 and other problematic modules
import os
import sys
import site
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules

# Add OpenCV binaries
binaries = []
opencv_binaries = collect_dynamic_libs('cv2')
binaries.extend(opencv_binaries)

# Add numpy data files
datas = collect_data_files('numpy')

# Collect all submodules
hiddenimports = []
hiddenimports.extend(collect_submodules('cv2'))
hiddenimports.extend(collect_submodules('numpy'))
hiddenimports.extend(collect_submodules('PyQt5'))
"""
    
    hooks_dir = "hooks"
    os.makedirs(hooks_dir, exist_ok=True)
    
    hook_path = os.path.join(hooks_dir, "hook-cv2.py")
    with open(hook_path, "w") as f:
        f.write(hook_content)
    
    print(f"Generated PyInstaller hook file: {hook_path}")
    return hooks_dir

if __name__ == "__main__":
    # Copy OpenCV DLLs to a directory that will be included with the application
    copy_opencv_dlls("opencv_dlls")
    
    # Generate hook file
    hooks_dir = generate_hook_file()
    
    print("\nNow you can build your application with:")
    print(f"pyinstaller --additional-hooks-dir={hooks_dir} FireVisionPro.spec") 