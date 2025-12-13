@echo off
REM CleanRoute Startup Script for Windows
REM Supports both CSV-only mode and Full System mode

echo ╔══════════════════════════════════════════════════════════════╗
echo ║       CleanRoute - Smart Waste Management System      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend
set FRONTEND_DIR=%SCRIPT_DIR%frontend

REM Check if virtual environment exists
if not exist "%BACKEND_DIR%\.venv" (
    echo Error: Virtual environment not found at %BACKEND_DIR%\.venv
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Select Startup Mode:
echo   1) CSV Mode (Simple - No database required)
echo   2) Full System (PostgreSQL + MQTT + CSV fallback)
echo.
set /p choice="Enter choice [1-2] (default: 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" goto csv_mode
if "%choice%"=="2" goto full_mode
echo Invalid choice. Using CSV mode.
goto csv_mode

:csv_mode
echo.
echo ════════════════════════════════════════════════════════════════
echo 📄 Starting in CSV Mode (Mock Data Only)
echo ════════════════════════════════════════════════════════════════

REM Check if mock data exists
if not exist "%BACKEND_DIR%\mock_data\bins_config.csv" (
    echo Error: Mock data not found
    echo Generating mock data now...
    cd "%BACKEND_DIR%"
    call .venv\Scripts\activate.bat
    python generate_mock_data.py
    echo Mock data generated
)

REM Set environment for CSV mode
set USE_BACKEND=false

REM Start frontend only
cd "%BACKEND_DIR%"
call .venv\Scripts\activate.bat
cd "%FRONTEND_DIR%"

echo.
echo Starting Flask Frontend...
echo 📍 Dashboard: http://localhost:5001
echo 📍 Districts: http://localhost:5001/districts
echo.
echo Press Ctrl+C to stop
echo ════════════════════════════════════════════════════════════════
echo.

python app.py
goto end

:full_mode
echo.
echo ════════════════════════════════════════════════════════════════
echo Starting Full System (Backend + Frontend + MQTT)
echo ════════════════════════════════════════════════════════════════

REM Check PostgreSQL
echo Checking PostgreSQL...
pg_isready -h localhost -p 5432 >nul 2>&1
if %errorlevel% equ 0 (
    echo PostgreSQL is running
) else (
    echo ⚠️  PostgreSQL is not running. Checking Docker...
    
    docker ps >nul 2>&1
    if %errorlevel% neq 0 (
        echo Docker is not running
        echo.
        echo Please either:
        echo   1. Install and start Docker Desktop
        echo   2. Install PostgreSQL natively
        pause
        exit /b 1
    )
    
    REM Check if container exists
    docker ps -a --format "{{.Names}}" | findstr /x cleanroute-postgres >nul
    if %errorlevel% equ 0 (
        echo Starting existing PostgreSQL container...
        docker start cleanroute-postgres >nul 2>&1
        timeout /t 3 /nobreak >nul
        echo PostgreSQL started
    ) else (
        echo Creating new PostgreSQL container...
        docker run --name cleanroute-postgres ^
          -e POSTGRES_DB=cleanroute_db ^
          -e POSTGRES_USER=cleanroute_user ^
          -e POSTGRES_PASSWORD=cleanroute_pass ^
          -p 5432:5432 -d postgres:15 >nul 2>&1
        
        echo Waiting for PostgreSQL to initialize...
        timeout /t 5 /nobreak >nul
        echo PostgreSQL started successfully
    )
)

REM Activate environment
cd "%BACKEND_DIR%"
call .venv\Scripts\activate.bat

REM Set environment for backend mode
set USE_BACKEND=true
set BACKEND_URL=http://localhost:8000

REM Start FastAPI Backend
echo.
echo Starting FastAPI Backend (Port 8000)...
start /B cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1"
timeout /t 2 /nobreak >nul
echo Backend API started

REM Check MQTT
echo.
echo Checking MQTT Broker...
tasklist /FI "IMAGENAME eq mosquitto.exe" 2>NUL | find /I /N "mosquitto.exe" >nul
if %errorlevel% equ 0 (
    echo MQTT broker is running
) else (
    echo ⚠️  MQTT broker not running
    echo Start manually if needed: mosquitto -c mqtt/mosquitto_secure.conf
)

REM Start Frontend
echo.
echo Starting Flask Frontend (Port 5001)...
cd "%FRONTEND_DIR%"
start /B cmd /c "python app.py > ..\frontend.log 2>&1"
timeout /t 2 /nobreak >nul
echo Frontend started

echo.
echo ════════════════════════════════════════════════════════════════
echo 🎉 System Started Successfully!
echo ════════════════════════════════════════════════════════════════
echo.
echo Services:
echo   - Backend API:  http://localhost:8000
echo   - Frontend:     http://localhost:5001
echo   - API Docs:     http://localhost:8000/docs
echo.
echo 📝 Log Files:
echo   - Backend:      %SCRIPT_DIR%backend.log
echo   - Frontend:     %SCRIPT_DIR%frontend.log
echo.
echo To Stop: Run stop.bat
echo.
echo Press any key to open dashboard in browser...
pause >nul
start http://localhost:5001

:end
