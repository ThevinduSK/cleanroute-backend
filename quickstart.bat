@echo off
REM CleanRoute Quick Start - CSV Mode (Simplest)
REM Perfect for demos and testing

echo ╔══════════════════════════════════════════════════════════════╗
echo ║       CleanRoute - Quick Start (CSV Mode)             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set FRONTEND_DIR=%SCRIPT_DIR%frontend

REM Check if virtual environment exists
if not exist "%BACKEND_DIR%\.venv" (
    echo Virtual environment not found. Running setup...
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)

REM Check/Generate mock data
if not exist "%BACKEND_DIR%\mock_data\bins_config.csv" (
    echo Generating mock data...
    cd "%BACKEND_DIR%"
    call .venv\Scripts\activate.bat
    python generate_mock_data.py
    if %errorlevel% neq 0 (
        echo Failed to generate mock data
        pause
        exit /b 1
    )
    echo Mock data generated
)

REM Start frontend
cd "%BACKEND_DIR%"
call .venv\Scripts\activate.bat
cd "%FRONTEND_DIR%"

echo.
echo ════════════════════════════════════════════════════════════════
echo Starting CleanRoute Dashboard...
echo ════════════════════════════════════════════════════════════════
echo.
echo 📍 Dashboard: http://localhost:5001
echo 📍 Districts: http://localhost:5001/districts
echo.
echo Press Ctrl+C to stop
echo ════════════════════════════════════════════════════════════════
echo.

REM Wait a moment then open browser
timeout /t 2 /nobreak >nul
start http://localhost:5001

python app.py
