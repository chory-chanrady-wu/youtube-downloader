@echo off
REM YouTube Downloader - Batch Launcher
REM This is a lightweight alternative to the .exe (requires Python 3.10+ installed)

echo.
echo =====================================
echo     YouTube Downloader
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10+ is not installed or not on PATH
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if ffmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ffmpeg is not installed or not on PATH
    echo MP3 downloads will not work
    echo.
    echo Install ffmpeg with: winget install gyan.ffmpeg
    echo Then restart this batch file
    pause
)

echo Starting server...
echo Opening browser at http://127.0.0.1:8000
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate venv and run the app
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt 2>nul
python launcher.py

pause

