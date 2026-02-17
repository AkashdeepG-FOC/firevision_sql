# Fire Vision Pro - Build Optimization Guide

## Overview

This guide explains how to build Fire Vision Pro as a small-sized executable while maintaining all features.

## Quick Start

```bash
# Run the optimized build script
python build_optimized_ultra.py
```

The script will automatically:
- Clean previous build artifacts
- Check dependencies
- Detect available models
- Build with optimized settings
- Generate size report

## Build Configuration

Edit `build_config.json` to customize your build:

```json
{
  "build_profile": "balanced",
  "models_to_include": ["yolov8n.pt", "best_m.pt"],
  "enable_upx": true,
  "upx_level": 9
}
```

## Size Optimization Techniques

### 1. UPX Compression (30-50% reduction)

**Install UPX:**
```bash
# Download from: https://github.com/upx/upx/releases
# Extract to C:\upx or add to PATH
upx --version  # Verify installation
```

**Benefits:**
- Reduces executable size by 30-50%
- No performance impact
- Automatic decompression at runtime

### 2. Module Exclusions

The build script excludes unused heavy modules:
- TensorFlow, Keras (not used)
- Matplotlib, Pandas (not used)
- JAX ecosystem (not used)
- Unused PyTorch components

### 3. Model Selection

**Included Models:**
- `yolov8n.pt` (6.5MB) - Fast, lightweight
- `best_m.pt` (103MB) - Your custom trained model

**Excluded Models:**
- `custom_model.pt` (6.7MB) - Not needed

### 4. Python Optimization

```bash
--optimize=2  # Removes docstrings and assertions
--strip       # Removes debug symbols
```

## Build Profiles Comparison

| Profile | Size | Models | Features | Use Case |
|---------|------|--------|----------|----------|
| Ultra-Lean | 150-250MB | yolov8n.pt only | Core only | Minimal install |
| **Balanced** | **300-400MB** | **yolov8n.pt + best_m.pt** | **All features** | **Recommended** |
| Full-Featured | 500-600MB | All models | Everything | Development |

## Troubleshooting

### Build Fails with "Module not found"

**Solution:** Install missing dependencies
```bash
pip install -r requirements.txt
```

### Executable is too large

**Solutions:**
1. Enable UPX compression
2. Exclude more modules
3. Use smaller models
4. Switch to Ultra-Lean profile

### UPX not found

**Solution:** Download and install UPX
```bash
# Windows: Download from GitHub releases
# Add to PATH or place upx.exe in project folder
```

### Missing DLL errors on target system

**Solution:** Install Visual C++ Redistributable
- Download from Microsoft website
- Include in installer package

### Slow startup time

**Solutions:**
1. Use `--onedir` instead of `--onefile`
2. Reduce number of included modules
3. Use smaller models

## Advanced Customization

### Custom Module Exclusions

Edit `build_optimized_ultra.py` and add to exclusions list:

```python
exclusions = [
    "your_module_here",
    # ... existing exclusions
]
```

### Include Additional Files

```python
cmd.append("--add-data=your_folder;your_folder")
```

### Change Compression Level

```python
# In build_config.json
"upx_level": 9  # Maximum compression (slower)
"upx_level": 1  # Minimal compression (faster build)
```

## Performance Benchmarks

| Metric | Target | Typical |
|--------|--------|---------|
| Build Time | 8-12 min | 10 min |
| Executable Size | 300-400MB | 350MB |
| Startup Time | <10s | 6-8s |
| RAM Usage | <2GB | 1.5GB |

## Best Practices

1. **Always test on clean system** - Copy exe to machine without Python
2. **Use UPX compression** - Reduces size significantly
3. **Include only needed models** - Each model adds 6-100MB
4. **Test all features** - Ensure nothing breaks after optimization
5. **Keep build logs** - Save build_report.txt for reference

## File Size Breakdown

Typical balanced build (350MB):
- PyQt5 + Qt libraries: ~120MB
- PyTorch: ~100MB
- YOLO models: ~110MB
- OpenCV: ~15MB
- Other dependencies: ~5MB

## Next Steps

After successful build:

1. **Test locally:**
   ```bash
   dist\FireVisionPro.exe
   ```

2. **Test on clean Windows 10/11 machine**

3. **Create installer** (optional):
   ```bash
   # Use NSIS or Inno Setup
   makensis installer.nsi
   ```

4. **Sign executable** (optional):
   ```bash
   # For Windows SmartScreen
   signtool sign /f cert.pfx dist\FireVisionPro.exe
   ```

## Support

For issues or questions:
- Check `build_report.txt` for build details
- Review PyInstaller logs in `build/` folder
- Test with `--console` flag to see errors
