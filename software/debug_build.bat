@echo off
echo Building Debug version of Fire Vision Pro...
echo.

call venv\Scripts\activate

rem Build debug version with console window
echo Building debug executable with console...
pyinstaller main.py --name=FireVisionPro_Debug --clean ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=config_manager ^
    --hidden-import=background_service ^
    --hidden-import=google_drive_manager ^
    --hidden-import=recordings_page ^
    --hidden-import=recording_manager ^
    --hidden-import=stream_manager ^
    --hidden-import=enhanced_camera_manager ^
    --hidden-import=ui_components ^
    --hidden-import=splash_screen ^
    --collect-all=cv2

if %errorlevel% neq 0 (
    echo Debug build failed!
    exit /b %errorlevel%
)

echo.
echo Debug build complete! The debug version with console is available in the dist folder.
echo. 