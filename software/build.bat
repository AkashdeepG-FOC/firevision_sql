@echo off
echo Fire Vision Pro - Quick Build Script
echo ====================================

echo Installing build requirements...
pip install -r requirements_build.txt

echo.
echo Building executable...
python build_exe.py

echo.
echo Build completed! Check the dist/ folder for your executable.
pause
