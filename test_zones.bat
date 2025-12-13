@echo off
REM Test Zone-Based Routing

echo.
echo ========================================
echo  CleanRoute Zone Routing Test
echo ========================================
echo.

REM Check if server is running
curl -s http://localhost:5001/api/stats >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Server is not running!
    echo Please start the server first: .\quickstart.bat
    pause
    exit /b 1
)

echo Server is running...
echo.

echo ========================================
echo  1. Getting All Zones
echo ========================================
echo.
curl -s http://localhost:5001/api/zones | python -m json.tool
echo.
pause

echo.
echo ========================================
echo  2. Getting Zone-Based Routes
echo ========================================
echo.

REM Calculate tomorrow's date and time (2 PM)
for /f "tokens=1-3 delims=/" %%a in ('echo %date%') do (
    set MM=%%a
    set DD=%%b
    set YYYY=%%c
)

REM Simple date calculation (just use current date for now)
set TARGET_TIME=2025-12-14-14-00

echo Target Time: %TARGET_TIME%
echo.
curl -s http://localhost:5001/api/route-by-zone/%TARGET_TIME% | python -m json.tool
echo.
pause

echo.
echo ========================================
echo  3. Comparison: Single vs Zone-Based
echo ========================================
echo.

echo Single Route:
curl -s http://localhost:5001/api/route/%TARGET_TIME% | python -m json.tool 2>nul | findstr /C:"bins_count" /C:"total_distance_km" /C:"estimated_time_hours"
echo.

echo Zone-Based Routes:
curl -s http://localhost:5001/api/route-by-zone/%TARGET_TIME% | python -m json.tool 2>nul | findstr /C:"total_zones" /C:"total_bins" /C:"total_distance_km"
echo.

echo.
echo ========================================
echo  Test Complete!
echo ========================================
echo.
echo Open http://localhost:5001 to see the dashboard
echo.
pause
