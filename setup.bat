@echo off
REM CleanRoute Setup Script for Windows
REM This script sets up the Python environment and installs dependencies

echo 🔧 Setting up CleanRoute...
echo ============================
echo.

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend

cd "%BACKEND_DIR%"

REM Check if Python 3 is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python 3 is not installed
    echo Please install Python 3.9 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Found Python: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo 📥 Installing dependencies...
pip install flask flask-cors pandas numpy python-dateutil requests psycopg2-binary paho-mqtt fastapi uvicorn --quiet

echo.
echo ✅ Setup complete!
echo.
echo To start the dashboard, run:
echo   start.bat
echo.
echo Or manually:
echo   cd backend ^&^& .venv\Scripts\activate.bat ^&^& cd ..\frontend ^&^& python app.py
echo.
pause
