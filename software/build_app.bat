@echo off
echo Building Fire Vision Pro application...
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

rem Run PyInstaller with spec file
echo Building executable...
pyinstaller FireVisionPro.spec --clean

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo.
echo Build complete! Application is available in the dist folder.
echo. 