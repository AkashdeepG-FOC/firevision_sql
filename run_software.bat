@echo off
cd /d "%~dp0software"
echo Starting Software Client...
python main.py
if errorlevel 1 pause
