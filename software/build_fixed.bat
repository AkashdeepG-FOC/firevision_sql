@echo off
echo Fire Vision Pro - Fixed Build Script
echo ===================================

echo Installing fixed requirements...
pip install pyinstaller==5.13.2
pip install ultralytics==8.0.196
pip install torch==2.0.1 torchvision==0.15.2
pip install scipy==1.11.3
pip install numpy==1.24.3
pip install opencv-python==4.8.1.78
pip install PyQt5==5.15.9

echo.
echo Building with fixes...
python fix_build_issues.py

echo.
echo Build completed! Check dist/ folder.
pause
