# Fire Vision Pro - Build Instructions

This guide will help you create an executable (.exe) file for Fire Vision Pro.

## Quick Start

### Method 1: Automated Build Script (Recommended)

1. **Run the build script:**
   \`\`\`bash
   python build_exe.py
   \`\`\`

2. **Choose option 1 or 2:**
   - Option 1: Creates a folder with the executable
   - Option 2: Creates a single .exe file

3. **Find your executable:**
   - Folder version: `dist/FireVisionPro/FireVisionPro.exe`
   - Single file: `dist/FireVisionPro.exe`

### Method 2: Windows Batch File

1. **Double-click:** `build.bat`
2. **Follow the prompts**

## Manual Build Methods

### PyInstaller (Recommended)

1. **Install PyInstaller:**
   \`\`\`bash
   pip install pyinstaller
   \`\`\`

2. **Basic build:**
   \`\`\`bash
   pyinstaller --onefile --windowed --name=FireVisionPro enhanced_main.py
   \`\`\`

3. **Advanced build with dependencies:**
   \`\`\`bash
   pyinstaller --onefile --windowed --name=FireVisionPro \
   --add-data="config;config" \
   --hidden-import=cv2 \
   --hidden-import=PyQt5.QtCore \
   --hidden-import=ultralytics \
   enhanced_main.py
   \`\`\`

### cx_Freeze Alternative

1. **Install cx_Freeze:**
   \`\`\`bash
   pip install cx_freeze
   \`\`\`

2. **Run build script:**
   \`\`\`bash
   python build_exe.py
   # Choose option 3
   \`\`\`

## Build Optimization

### For Smaller File Size

1. **Use optimized build:**
   \`\`\`bash
   python optimize_build.py
   \`\`\`

2. **Manual optimization:**
   \`\`\`bash
   pyinstaller --onefile --windowed --strip --upx-dir=upx enhanced_main.py
   \`\`\`

## Troubleshooting

### Common Issues

1. **Missing modules error:**
   - Add `--hidden-import=module_name` to PyInstaller command
   - Check the build script for common hidden imports

2. **Large file size:**
   - Use `optimize_build.py`
   - Exclude unnecessary modules with `--exclude-module`

3. **Slow startup:**
   - Use folder distribution instead of single file
   - Consider using `--onedir` instead of `--onefile`

4. **Missing DLL errors:**
   - Install Visual C++ Redistributable on target machine
   - Include DLLs manually with `--add-binary`

### Dependencies Issues

If you get import errors, install these packages:
\`\`\`bash
pip install pyinstaller cx_freeze auto-py-to-exe pillow
\`\`\`

## Distribution

### Creating an Installer

1. **Install NSIS:** Download from https://nsis.sourceforge.io/
2. **Generate installer script:**
   \`\`\`bash
   python build_exe.py
   # Choose option 5
   \`\`\`
3. **Compile installer:**
   \`\`\`bash
   makensis installer.nsi
   \`\`\`

### Testing Your Executable

1. **Test on build machine:** Run the .exe file
2. **Test on clean machine:** Copy to a computer without Python
3. **Test different Windows versions:** Windows 10, 11, etc.

## File Structure After Build

\`\`\`
dist/
├── FireVisionPro/          # Folder distribution
│   ├── FireVisionPro.exe   # Main executable
│   ├── config/             # Configuration files
│   ├── _internal/          # PyInstaller files
│   └── ...
└── FireVisionPro.exe       # Single file distribution
\`\`\`

## Advanced Configuration

### Custom Icon

1. **Create icon.ico file** (64x64 pixels recommended)
2. **Add to build command:**
   \`\`\`bash
   pyinstaller --icon=icon.ico enhanced_main.py
   \`\`\`

### Including Additional Files

\`\`\`bash
pyinstaller --add-data="path/to/file;destination" enhanced_main.py
\`\`\`

### Excluding Modules

\`\`\`bash
pyinstaller --exclude-module=module_name enhanced_main.py
\`\`\`

## Performance Tips

1. **Use folder distribution** for faster startup
2. **Optimize imports** in your code
3. **Use UPX compression** for smaller size
4. **Test on target hardware** before distribution

## Security Considerations

1. **Code signing:** Sign your executable for Windows SmartScreen
2. **Antivirus:** Some antivirus may flag PyInstaller executables
3. **Testing:** Test on multiple antivirus solutions

## Support

If you encounter issues:
1. Check the console output for error messages
2. Try different build methods
3. Update PyInstaller: `pip install --upgrade pyinstaller`
4. Check PyInstaller documentation: https://pyinstaller.readthedocs.io/
