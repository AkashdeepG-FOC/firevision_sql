pyinstaller main.py --onedir --windowed --noupx --noconfirm --clean ^
  --name firevision ^
  --icon "assests/logo/fv_logo.ico" ^
  --add-data "config;config" ^
  --add-data "assests/icons;icons" ^
  --add-data "assests;assests" ^
  --hidden-import=ui_components ^
  --hidden-import=PyQt5.QtCore ^
  --hidden-import=PyQt5.QtGui ^
  --hidden-import=PyQt5.QtWidgets ^
  --hidden-import=PyQt5.QtNetwork ^
  --hidden-import=PyQt5.QtMultimedia ^
  --hidden-import=PyQt5.QtMultimediaWidgets ^
  --hidden-import=PyQt5.QtPrintSupport ^
  --hidden-import=DeviceSettings ^
  --hidden-import=AdvancedCamera ^
  --hidden-import=config_manager ^
  --hidden-import=background_service ^
  --hidden-import=google_drive_manager ^
  --hidden-import=recordings_page ^
  --hidden-import=recording_manager ^
  --hidden-import=stream_manager ^
  --hidden-import=enhanced_camera_manager ^
  --hidden-import=enhanced_fullscreen_widget ^
  --hidden-import=enhanced_review_system ^
  --hidden-import=fire_detection_backend ^
  --hidden-import=notification_manager ^
  --hidden-import=alerts_manager ^
  --hidden-import=cloud_backup_manager ^
  --hidden-import=user_managers ^
  --hidden-import=voice_command_manager ^
  --hidden-import=splash_screen ^
  --exclude-module tensorflow ^
  --exclude-module tensorboard ^
  --exclude-module onnx ^
  --exclude-module onnxruntime ^
  --exclude-module openvino

echo Creating models directory...
if not exist "dist\firevision\models" mkdir "dist\firevision\models"

echo Copying models...
copy "best_m.pt" "dist\firevision\models\"
copy "yolov8n.pt" "dist\firevision\models\"

echo Build complete. executable is in dist\firevision\firevision.exe
pause
