@echo off
REM Comprehensive Diagnostic Script for AI Pentesting Agent
REM Run this when things don't work

echo ================================================================
echo    AI PENTESTING AGENT - COMPREHENSIVE DIAGNOSTICS
echo ================================================================
echo.

REM Check 1: Backend Running?
echo [1/6] Checking if backend is running...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo    ❌ Backend is NOT running!
    echo    ➡️  FIX: Run start_backend.bat in a separate terminal
    echo.
    goto :frontend_check
) else (
    echo    ✅ Backend is running
    curl -s http://localhost:8000/health
    echo.
)

REM Check 2: Backend Routes
echo [2/6] Checking backend routes...
curl -s http://localhost:8000/api/v1/docs >nul 2>&1
if errorlevel 1 (
    echo    ❌ API docs not accessible
) else (
    echo    ✅ API docs accessible at http://localhost:8000/api/v1/docs
)

REM Test specific endpoint
curl -s -X POST http://localhost:8000/api/v1/scan/stream/create -H "Content-Type: application/json" -d "{\"target\":\"test\",\"user_prompt\":\"test\",\"tools\":[\"nmap\"],\"profile\":\"quick\",\"enable_ai\":true}" >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  Scan creation endpoint might have issues
) else (
    echo    ✅ Scan creation endpoint responding
)
echo.

:frontend_check
REM Check 3: Frontend Running?
echo [3/6] Checking if frontend is running...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo    ❌ Frontend is NOT running!
    echo    ➡️  FIX: Run start_frontend.bat in a separate terminal
    echo.
) else (
    echo    ✅ Frontend is running
    echo.
)

REM Check 4: Dependencies
echo [4/6] Checking backend dependencies...
cd backend
if exist venv (
    echo    ✅ Virtual environment exists
    call venv\Scripts\activate.bat
    
    REM Check critical packages
    pip show sse-starlette >nul 2>&1
    if errorlevel 1 (
        echo    ❌ sse-starlette is NOT installed!
        echo    ➡️  FIX: pip install sse-starlette
    ) else (
        echo    ✅ sse-starlette is installed
    )
    
    pip show google-generativeai >nul 2>&1
    if errorlevel 1 (
        echo    ❌ google-generativeai is NOT installed!
        echo    ➡️  FIX: pip install google-generativeai
    ) else (
        echo    ✅ google-generativeai is installed
    )
) else (
    echo    ❌ Virtual environment does NOT exist!
    echo    ➡️  FIX: Run INSTALL.bat
)
cd ..
echo.

REM Check 5: Frontend Dependencies
echo [5/6] Checking frontend dependencies...
cd frontend
if exist node_modules (
    echo    ✅ node_modules exists
    
    if exist node_modules\react-hot-toast (
        echo    ✅ react-hot-toast is installed
    ) else (
        echo    ❌ react-hot-toast is NOT installed!
        echo    ➡️  FIX: npm install react-hot-toast
    )
) else (
    echo    ❌ node_modules does NOT exist!
    echo    ➡️  FIX: Run npm install
)
cd ..
echo.

REM Check 6: Configuration Files
echo [6/6] Checking configuration files...
if exist backend\.env (
    echo    ✅ backend\.env exists
) else (
    echo    ⚠️  backend\.env missing (optional, will use defaults)
)

if exist frontend\.env.local (
    echo    ✅ frontend\.env.local exists
) else (
    echo    ⚠️  frontend\.env.local missing (optional, will use defaults)
)
echo.

REM Summary
echo ================================================================
echo    DIAGNOSTIC SUMMARY
echo ================================================================
echo.
echo QUICK FIXES:
echo.
echo 1. If backend not running:
echo    ^> cd backend
echo    ^> venv\Scripts\activate
echo    ^> uvicorn app.main:app --reload
echo.
echo 2. If frontend not running:
echo    ^> cd frontend  
echo    ^> npm run dev
echo.
echo 3. If dependencies missing:
echo    ^> Run INSTALL.bat
echo.
echo 4. If still stuck on "Initializing AI Agent":
echo    ^> Press F12 in browser
echo    ^> Check Console tab for errors
echo    ^> Check Network tab for failed requests
echo    ^> Look for 404 or 500 errors
echo.
echo 5. If 404 errors on /api/v1/scan/stream/create:
echo    ^> Restart backend server
echo    ^> Check backend logs for route listing
echo    ^> Verify URL in browser: http://localhost:8000/api/v1/docs
echo.
echo USEFUL URLS:
echo    Backend Health: http://localhost:8000/health
echo    API Docs: http://localhost:8000/api/v1/docs
echo    Frontend: http://localhost:3000
echo.
echo ================================================================
echo.
pause

