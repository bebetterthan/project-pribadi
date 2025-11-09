@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM ============================================================================
REM   AI PENTESTING AGENT - OPTIMIZED SHUTDOWN SCRIPT
REM   Version: 2.0 (Matching START_ALL.bat v2.0)
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║         AI PENTESTING AGENT - GRACEFUL SHUTDOWN                          ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

echo [SHUTDOWN] Stopping all services...
echo.

REM Function to gracefully kill process on port
call :StopService 8000 "Backend API (FastAPI + Uvicorn)"
call :StopService 3000 "Frontend Dev Server (Next.js)"

REM Kill any orphaned Python/Node processes related to the project
echo    → Cleaning up orphaned processes...
set CLEANED=0

REM Kill only Uvicorn processes (not all Python)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID:"') do (
    netstat -ano | findstr ":8000" | findstr "%%a" >nul 2>&1
    if !errorlevel! equ 0 (
        echo       └─ Terminating Python (Uvicorn) PID: %%a
        taskkill /F /PID %%a >nul 2>&1
        set CLEANED=1
    )
)

REM Kill only Node processes on port 3000 (not all Node)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr "PID:"') do (
    netstat -ano | findstr ":3000" | findstr "%%a" >nul 2>&1
    if !errorlevel! equ 0 (
        echo       └─ Terminating Node.js (Next.js) PID: %%a
        taskkill /F /PID %%a >nul 2>&1
        set CLEANED=1
    )
)

if !CLEANED! equ 0 (
    echo       └─ No orphaned processes found
)

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                  ✓ ALL SERVICES STOPPED SUCCESSFULLY                     ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo   📋 SHUTDOWN SUMMARY:
echo   ├─ Backend API:        Stopped (Port 8000)
echo   ├─ Frontend Dev:       Stopped (Port 3000)
echo   └─ Orphaned Process:   Cleaned
echo.
echo   💡 NEXT STEPS:
echo   • To restart: Run START_ALL.bat
echo   • Check logs: backend\logs\app.log
echo   • View scans: backend\pentest.db
echo.
echo   ⚠️  NOTE: Database and logs are preserved
echo.

timeout /t 2 /nobreak >nul
goto :EOF

REM ============================================================================
REM   HELPER FUNCTIONS
REM ============================================================================

:StopService
set PORT=%1
set SERVICE=%2
echo    [%PORT%] Stopping %SERVICE%...
set FOUND=0

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo         └─ Terminating PID: %%a
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)

if !FOUND! equ 0 (
    echo         └─ No process running on port %PORT%
) else (
    echo         └─ Service stopped
)
goto :EOF

