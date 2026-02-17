@echo off
cd /d "%~dp0"
echo Starting Backend...
:: Running as a module allows relative imports to work
python -m uvicorn backend.main:app --reload --port 8000
if errorlevel 1 pause
