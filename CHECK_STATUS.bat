@echo off
echo ================================================================================
echo    AI PENTESTING AGENT - STATUS CHECK
echo ================================================================================
echo.

REM Check Backend Port 8000
echo [1/3] Checking Backend (Port 8000)...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is RUNNING on port 8000
    
    REM Try health check
    echo [TEST] Testing backend health endpoint...
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health' -UseBasicParsing -TimeoutSec 5; Write-Host '[OK] Backend health check PASSED'; Write-Host $response.Content } catch { Write-Host '[ERROR] Backend health check FAILED'; Write-Host $_.Exception.Message }"
) else (
    echo [ERROR] Backend is NOT running
    echo [FIX] Run START_ALL.bat to start backend
)

echo.

REM Check Frontend Port 3000
echo [2/3] Checking Frontend (Port 3000)...
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend is RUNNING on port 3000
    echo [INFO] Open http://localhost:3000 in browser
) else (
    echo [ERROR] Frontend is NOT running
    echo [FIX] Run START_ALL.bat to start frontend
)

echo.

REM Check Database
echo [3/3] Checking Database...
if exist "backend\scans.db" (
    echo [OK] Database file exists
) else (
    echo [WARNING] Database file not found (will be created on first run)
)

echo.
echo ================================================================================
echo    STATUS CHECK COMPLETE
echo ================================================================================
echo.

REM Summary
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
set BACKEND_STATUS=%errorlevel%

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
set FRONTEND_STATUS=%errorlevel%

if %BACKEND_STATUS% equ 0 (
    if %FRONTEND_STATUS% equ 0 (
        echo [SUCCESS] Both services are running!
        echo [INFO] Access dashboard: http://localhost:3000
    ) else (
        echo [PARTIAL] Backend running, but frontend is down
        echo [ACTION] Restart START_ALL.bat
    )
) else (
    echo [ERROR] Backend is not running
    echo [ACTION] Run START_ALL.bat to start all services
)

echo.
pause

