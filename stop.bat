@echo off
REM CleanRoute Stop Script for Windows
REM Stops all running CleanRoute services

echo Stopping CleanRoute Services...
echo ════════════════════════════════════════════════════════════════

REM Stop Frontend (Flask on port 5001)
echo Stopping Frontend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Frontend stopped
    goto backend
)
echo Frontend not running

:backend
REM Stop Backend (FastAPI on port 8000)
echo Stopping Backend API...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Backend API stopped
    goto mqtt
)
echo Backend not running

:mqtt
REM Stop MQTT Broker
echo.
set /p stop_mqtt="Stop MQTT broker (mosquitto)? (y/N): "
if /i "%stop_mqtt%"=="y" (
    taskkill /F /IM mosquitto.exe >nul 2>&1
    echo MQTT broker stopped
)

REM Stop PostgreSQL Docker container
docker ps --format "{{.Names}}" | findstr /x cleanroute-postgres >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    set /p stop_postgres="Stop PostgreSQL container? (y/N): "
    if /i "!stop_postgres!"=="y" (
        docker stop cleanroute-postgres >nul 2>&1
        echo PostgreSQL stopped
        echo ^(Container preserved. Run 'docker rm cleanroute-postgres' to remove it^)
    ) else (
        echo PostgreSQL container left running
    )
)

echo.
echo ════════════════════════════════════════════════════════════════
echo 🎉 All services stopped
echo ════════════════════════════════════════════════════════════════
pause
