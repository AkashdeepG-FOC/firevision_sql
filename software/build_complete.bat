@echo off
echo ========================================
echo   Fire Vision Pro - Complete Build
echo ========================================
echo.

rem Create virtual environment if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install requirements.
        exit /b %errorlevel%
    )
) else (
    call venv\Scripts\activate
)

rem Make sure PyInstaller is installed
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Failed to install pyinstaller.
    exit /b %errorlevel%
)

rem Run helper script to handle OpenCV DLLs and generate hooks
echo Running import handler...
python handle_imports.py
if %errorlevel% neq 0 (
    echo Failed to handle imports.
    exit /b %errorlevel%
)

rem Update spec file to include hooks directory
echo Updating spec file with hooks...
set "find_text=hookspath=[],"
set "replace_text=hookspath=['hooks'],"
powershell -Command "(Get-Content FireVisionPro.spec) -replace '%find_text%', '%replace_text%' | Set-Content FireVisionPro.spec"

rem Run PyInstaller with spec file
echo Building executable...
pyinstaller FireVisionPro.spec --clean --additional-hooks-dir=hooks

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

rem Create a distribution folder with all necessary files
echo Creating distribution package...
if not exist "dist\FireVisionPro_package" mkdir "dist\FireVisionPro_package"
copy "dist\FireVisionPro.exe" "dist\FireVisionPro_package\"
if exist "opencv_dlls" xcopy /s /y "opencv_dlls\*" "dist\FireVisionPro_package\"
if exist "README.md" copy "README.md" "dist\FireVisionPro_package\"

echo.
echo ========================================
echo Build complete! 
echo Application is available in dist\FireVisionPro_package
echo ========================================
echo. 