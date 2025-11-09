@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM ============================================================================
REM   AI PENTESTING AGENT - OPTIMIZED STARTUP SCRIPT
REM   Version: 2.0 (Optimized & Enhanced)
REM   Date: November 2025
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║         AI PENTESTING AGENT - OPTIMIZED STARTUP SYSTEM                   ║
echo ║         Hybrid AI Orchestrator ^| Flash 2.5 + Pro 2.5                    ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Enable Python verbose error output and UTF-8 encoding
set PYTHONUNBUFFERED=1
set PYTHONWARNINGS=default
set PYTHONFAULTHANDLER=1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM ============================================================================
REM   STEP 0: INTELLIGENT PORT CLEANUP
REM ============================================================================
echo [STEP 0/6] Smart Port Cleanup...
echo.

REM Function to kill process on specific port
call :KillPort 8000 "Backend API"
call :KillPort 3000 "Frontend Dev Server"

REM Gracefully terminate orphaned Node.js processes (avoid killing IDE)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr "PID:"') do (
    netstat -ano | findstr ":3000" | findstr "%%a" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    └─ Terminating Node.js process (PID: %%a)
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Short delay for cleanup
timeout /t 2 /nobreak >nul

echo    ✓ Ports cleaned
echo.

REM ============================================================================
REM   STEP 1: ENVIRONMENT VALIDATION
REM ============================================================================
echo [STEP 1/6] Environment Validation...
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ ERROR: Python not found!
    echo    └─ Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VER=%%v
echo    ✓ Python %PYTHON_VER% detected

REM Check Node.js installation
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ ERROR: Node.js not found!
    echo    └─ Please install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)

REM Get Node.js version
for /f "tokens=1" %%v in ('node --version') do set NODE_VER=%%v
echo    ✓ Node.js %NODE_VER% detected
echo.

REM ============================================================================
REM   STEP 2: BACKEND SETUP (Python + FastAPI)
REM ============================================================================
echo [STEP 2/6] Backend Environment Setup...
echo.
cd backend

REM Check/Create virtual environment
if not exist "venv\" (
    echo    → Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo    ✗ ERROR: Failed to create venv
        cd ..
        pause
        exit /b 1
    )
    echo    ✓ Virtual environment created
) else (
    echo    ✓ Virtual environment exists
)

REM Activate venv
call venv\Scripts\activate.bat

REM Smart dependency check (skip if already installed)
echo    → Checking dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, google.generativeai" >nul 2>&1
if !errorlevel! neq 0 (
    echo    → Installing backend dependencies...
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        echo    ✗ ERROR: Dependency installation failed
        deactivate
        cd ..
        pause
        exit /b 1
    )
    echo    ✓ Dependencies installed
) else (
    echo    ✓ Dependencies already satisfied
)

REM Initialize database
echo    → Initializing database...
python -c "from app.db.session import engine; from app.models import Base; Base.metadata.create_all(bind=engine)" 2>nul
if !errorlevel! equ 0 (
    echo    ✓ Database ready (pentest.db)
) else (
    echo    ⚠ Database init warning (will retry on startup)
)

REM Ensure logs directory exists
if not exist "logs" mkdir logs
if not exist "backend\logs" mkdir backend\logs


REM ============================================================================
REM   STEP 3: START BACKEND SERVER (FastAPI + Uvicorn)
REM ============================================================================
echo.
echo [STEP 3/6] Starting Backend Server...
echo.

REM Generate optimized PowerShell startup script
(
echo # AI Pentesting Backend - Optimized Startup
echo [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
echo $env:PYTHONIOENCODING = "utf-8"
echo $env:PYTHONUNBUFFERED = "1"
echo $env:PYTHONFAULTHANDLER = "1"
echo $env:LOG_LEVEL = "INFO"
echo.
echo cd "%~dp0backend"
echo.
echo Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
echo Write-Host "║  BACKEND API SERVER - FastAPI + Uvicorn                 ║" -ForegroundColor Cyan
echo Write-Host "║  Hybrid AI: Flash 2.5 ^(Tactical^) + Pro 2.5 ^(Strategic^)  ║" -ForegroundColor Cyan
echo Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
echo Write-Host ""
echo Write-Host "   Port:     http://localhost:8000" -ForegroundColor Green
echo Write-Host "   Docs:     http://localhost:8000/api/v1/docs" -ForegroundColor Yellow
echo Write-Host "   Health:   http://localhost:8000/api/v1/health" -ForegroundColor Yellow
echo Write-Host ""
echo Write-Host "▶ Starting server with auto-reload..." -ForegroundColor Green
echo Write-Host ""
echo.
echo try {
echo     ^& venv\Scripts\python.exe -u -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info --use-colors
echo } catch {
echo     Write-Host ""
echo     Write-Host "✗ Backend startup failed!" -ForegroundColor Red
echo     Write-Host "Error: $_" -ForegroundColor Red
echo     Write-Host ""
echo     Write-Host "Troubleshooting:" -ForegroundColor Yellow
echo     Write-Host "  1. Check if port 8000 is already in use" -ForegroundColor Gray
echo     Write-Host "  2. Verify virtual environment: .\venv\Scripts\activate" -ForegroundColor Gray
echo     Write-Host "  3. Check logs: .\logs\app.log" -ForegroundColor Gray
echo     Write-Host ""
echo     pause
echo }
) > backend\start_backend_debug.ps1

start "AI Pentest Backend | Port 8000" powershell -NoExit -ExecutionPolicy Bypass -File "backend\start_backend_debug.ps1"
echo    ✓ Backend server window opened
echo    └─ Initializing FastAPI application...

cd ..


REM ============================================================================
REM   STEP 4: BACKEND HEALTH CHECK (Smart Wait)
REM ============================================================================
echo.
echo [STEP 4/6] Backend Health Verification...
echo.

set WAIT_COUNT=0
set MAX_WAIT=20

echo    → Waiting for backend to initialize (max 60s)...

:WAIT_BACKEND
timeout /t 3 /nobreak >nul
set /a WAIT_COUNT+=1

REM Check if port is listening
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    if %WAIT_COUNT% geq %MAX_WAIT% (
        echo    ✗ Backend failed to start within 60 seconds
        echo    └─ Check backend window for errors
        pause
        exit /b 1
    )
    echo    ⌛ Still initializing... ^(%WAIT_COUNT%/%MAX_WAIT%^)
    goto WAIT_BACKEND
)

echo    ✓ Backend port 8000 is listening

REM HTTP health check
timeout /t 2 /nobreak >nul
echo    → Running health check endpoint...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health' -UseBasicParsing -TimeoutSec 10; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✓ Health check PASSED - Backend ready
) else (
    echo    ⚠ Health endpoint not responding yet (server still warming up)
    echo    └─ Continuing... (will retry on first scan)
)
echo.

REM ============================================================================
REM   STEP 5: FRONTEND SETUP (Next.js + React)
REM ============================================================================
echo [STEP 5/6] Frontend Environment Setup...
echo.
cd frontend

REM Smart dependency check
if not exist "node_modules\" (
    echo    → Installing npm packages (this may take 1-2 minutes)...
    call npm install --loglevel=error
    if !errorlevel! neq 0 (
        echo    ✗ ERROR: npm install failed
        cd ..
        pause
        exit /b 1
    )
    echo    ✓ Frontend dependencies installed
) else (
    echo    → Checking dependencies...
    REM Quick check for critical packages
    if not exist "node_modules\next\package.json" (
        echo    → Reinstalling dependencies...
        call npm install --loglevel=error
    )
    echo    ✓ Dependencies verified
)

REM Check for .env.local
if not exist ".env.local" (
    if exist ".env.local.example" (
        echo    ⚠ Note: .env.local not found (using defaults)
    )
)

echo.

REM ============================================================================
REM   STEP 6: START FRONTEND SERVER (Next.js)
REM ============================================================================
echo [STEP 6/6] Starting Frontend Server...
echo.

REM Create optimized PowerShell startup for frontend
(
echo [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
echo.
echo cd "%~dp0frontend"
echo.
echo Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
echo Write-Host "║  FRONTEND DEV SERVER - Next.js 14 + React 18            ║" -ForegroundColor Cyan
echo Write-Host "║  Modern UI with TanStack Query + Zustand               ║" -ForegroundColor Cyan
echo Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
echo Write-Host ""
echo Write-Host "   URL:      http://localhost:3000" -ForegroundColor Green
echo Write-Host "   Mode:     Development (Hot Reload)" -ForegroundColor Yellow
echo Write-Host ""
echo Write-Host "▶ Starting Next.js development server..." -ForegroundColor Green
echo Write-Host ""
echo.
echo npm run dev
) > frontend\start_frontend.ps1

start "AI Pentest Frontend | Port 3000" powershell -NoExit -ExecutionPolicy Bypass -File "frontend\start_frontend.ps1"
echo    ✓ Frontend server window opened
echo    └─ Building and starting Next.js...

cd ..

REM ============================================================================
REM   STARTUP COMPLETE
REM ============================================================================
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                     ✓ STARTUP COMPLETE - READY!                          ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo   🚀 SERVICES RUNNING:
echo   ├─ Backend API:       http://localhost:8000
echo   │  ├─ Swagger Docs:   http://localhost:8000/api/v1/docs
echo   │  ├─ Health Check:   http://localhost:8000/api/v1/health
echo   │  └─ Model: Flash 2.5 ^(Tactical^) + Pro 2.5 ^(Strategic^)
echo   │
echo   └─ Frontend UI:       http://localhost:3000
echo      └─ Dashboard:      http://localhost:3000/dashboard
echo.
echo   📋 INTEGRATED PENTESTING TOOLS:
echo   ├─ Network:  Nmap, Subfinder, HTTPX
echo   ├─ Web:      Nuclei, WhatWeb, FFUF
echo   ├─ Security: SSLScan, SQLMap
echo   └─ AI:       Google Gemini 2.5 ^(Flash + Pro^)
echo.
echo   ⚡ FEATURES:
echo   ├─ Hybrid AI Orchestration ^(Flash for speed, Pro for analysis^)
echo   ├─ Real-time SSE Streaming ^(live scan progress^)
echo   ├─ Tool Chaining ^(Subfinder → HTTPX workflow^)
echo   ├─ Cost Tracking ^(per-scan token usage^)
echo   └─ Auto-escalation ^(Flash → Pro for critical findings^)
echo.
echo ───────────────────────────────────────────────────────────────────────────
echo.
echo   💡 QUICK START:
echo      1. Open browser: http://localhost:3000
echo      2. Navigate to "New Scan"
echo      3. Enter target ^(domain/IP/URL^)
echo      4. Select tools and click "Start Scan"
echo      5. Watch real-time progress with AI analysis
echo.
echo   🔧 TROUBLESHOOTING:
echo   ├─ Backend errors:    Check backend window for stack traces
echo   ├─ SSE not working:   Ensure backend health check passed
echo   ├─ Port conflicts:    Run STOP_ALL.bat then restart
echo   └─ Dependencies:      Re-run pip install / npm install
echo.
echo   📝 LOGS:
echo   ├─ Backend:  backend\logs\app.log
echo   ├─ Error:    backend\logs\error_debug.log
echo   └─ Scan DB:  backend\pentest.db
echo.
echo   ⚠️  IMPORTANT NOTES:
echo   • Backend MUST be fully ready before starting scans
echo   • Wait for "Backend ready" message before using frontend
echo   • Close with Ctrl+C in each terminal window
echo   • For complete shutdown: run STOP_ALL.bat
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║  🎯 READY TO SCAN! Open: http://localhost:3000                           ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Auto-open browser after 3 seconds
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo Press any key to close this window...
pause >nul
goto :EOF

REM ============================================================================
REM   HELPER FUNCTIONS
REM ============================================================================

:KillPort
set PORT=%1
set SERVICE=%2
echo    → Checking port %PORT% ^(%SERVICE%^)...
set FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo       └─ Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
    set FOUND=1
)
if !FOUND! equ 0 (
    echo       └─ Port %PORT% is free
)
goto :EOF
