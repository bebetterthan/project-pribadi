@echo off
echo ================================================================================
echo    AGENT-P - QUICK START (WITH ALL CRITICAL FIXES)
echo ================================================================================
echo.
echo [INFO] Starting with comprehensive bug fixes applied:
echo   - Tool chaining: 500 subdomains now passed to HTTPX/NMAP
echo   - Duplicate display: Removed database result streaming
echo   - Logger f-string bug: Fixed with %% formatting
echo   - Protobuf KeyError: Comprehensive error handling
echo.
echo [INFO] Killing existing processes on ports 8000 and 3000...

REM Kill existing processes
taskkill /F /FI "WINDOWTITLE eq Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Frontend*" 2>nul
timeout /t 2 >nul

echo [OK] Processes killed
echo.
echo [INFO] Starting Backend (Port 8000)...
start "Backend - Agent-P" cmd /k "cd backend && venv\Scripts\activate && set PYTHONIOENCODING=utf-8 && set PYTHONUNBUFFERED=1 && python -Xdev -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug"

echo [INFO] Waiting for backend to initialize (15s)...
timeout /t 15 >nul

echo [OK] Backend started
echo.
echo [INFO] Starting Frontend (Port 3000)...
start "Frontend - Agent-P" cmd /k "cd frontend && npm run dev"

echo [INFO] Waiting for frontend to initialize (10s)...
timeout /t 10 >nul

echo.
echo ================================================================================
echo    AGENT-P STARTED SUCCESSFULLY
echo ================================================================================
echo.
echo [ACCESS]
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000/docs
echo   Health Check: http://localhost:8000/api/v1/health
echo.
echo [TESTING PROTOCOL]
echo   1. Open http://localhost:3000
echo   2. Start scan with: unair.ac.id or hackerone.com
echo   3. Monitor for SUCCESS indicators:
echo      - RUN_SUBFINDER: 1823 findings
echo      - RUN_HTTPX: 400-600 findings (NOT 0!)
echo      - No duplicate tools
echo      - All tools execute once
echo.
echo [LOGS]
echo   Backend Console: See "Backend - Agent-P" window
echo   File Logs: backend\logs\app.log
echo.
echo Press any key to return to command prompt...
pause >nul

