@echo off
REM AI Pentesting Agent - Complete Installation Script (Windows)
REM For personal use - one-click setup

echo ================================================================
echo    AI PENTESTING AGENT - COMPLETE INSTALLATION
echo    Personal Use Setup Script
echo ================================================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python found
echo.

REM Check if Node.js is installed
echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18+ first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
node --version
npm --version
echo [OK] Node.js found
echo.

REM Backend Setup
echo [3/6] Setting up Backend...
cd backend

echo    - Creating virtual environment...
if exist venv (
    echo    [SKIP] venv already exists
) else (
    python -m venv venv
    echo    [OK] venv created
)

echo    - Activating virtual environment...
call venv\Scripts\activate.bat

echo    - Upgrading pip...
python -m pip install --upgrade pip --quiet

echo    - Installing dependencies...
pip install -r requirements.txt --quiet
echo    [OK] Backend dependencies installed

echo    - Creating .env file...
if exist .env (
    echo    [SKIP] .env already exists
) else (
    (
        echo DEBUG=True
        echo USE_MOCK_TOOLS=True
        echo CORS_ORIGINS=http://localhost:3000
        echo LOG_LEVEL=INFO
    ) > .env
    echo    [OK] .env created
)

echo    - Testing setup...
python test_setup.py
if errorlevel 1 (
    echo [WARNING] Some backend checks failed. Review output above.
    pause
)

cd ..
echo [OK] Backend setup complete
echo.

REM Frontend Setup
echo [4/6] Setting up Frontend...
cd frontend

echo    - Installing dependencies...
call npm install --silent
if errorlevel 1 (
    echo [ERROR] npm install failed!
    pause
    exit /b 1
)
echo    [OK] Frontend dependencies installed

echo    - Creating .env.local file...
if exist .env.local (
    echo    [SKIP] .env.local already exists
) else (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo    [OK] .env.local created
)

echo    - Building frontend (test)...
call npm run build --silent
if errorlevel 1 (
    echo [WARNING] Build had warnings, but may still work
) else (
    echo    [OK] Frontend builds successfully
)

cd ..
echo [OK] Frontend setup complete
echo.

REM Create start scripts
echo [5/6] Creating start scripts...

REM Backend start script
(
    echo @echo off
    echo echo Starting AI Pentesting Agent Backend...
    echo cd backend
    echo call venv\Scripts\activate.bat
    echo uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) > start_backend.bat
echo [OK] Created start_backend.bat

REM Frontend start script
(
    echo @echo off
    echo echo Starting AI Pentesting Agent Frontend...
    echo cd frontend
    echo npm run dev
) > start_frontend.bat
echo [OK] Created start_frontend.bat

REM Combined start script
(
    echo @echo off
    echo echo ================================================================
    echo echo    AI PENTESTING AGENT - STARTING SERVICES
    echo echo ================================================================
    echo echo.
    echo echo Starting Backend ^(Terminal 1^)...
    echo start "Backend - AI Pentesting Agent" cmd /k start_backend.bat
    echo timeout /t 3 /nobreak ^>nul
    echo.
    echo echo Starting Frontend ^(Terminal 2^)...
    echo start "Frontend - AI Pentesting Agent" cmd /k start_frontend.bat
    echo.
    echo echo ================================================================
    echo echo    SERVICES STARTING
    echo echo ================================================================
    echo echo Backend will be available at: http://localhost:8000
    echo echo Frontend will be available at: http://localhost:3000
    echo echo.
    echo echo Open your browser to: http://localhost:3000
    echo echo.
    echo echo Press any key to open browser automatically...
    echo pause ^>nul
    echo start http://localhost:3000
) > START.bat
echo [OK] Created START.bat

echo.

REM Final summary
echo [6/6] Installation Summary
echo ================================================================
echo.
echo [SUCCESS] Installation complete!
echo.
echo NEXT STEPS:
echo   1. Get your Gemini API key from: https://makersuite.google.com/app/apikey
echo   2. Run START.bat to launch both backend and frontend
echo   3. Open http://localhost:3000 in your browser
echo   4. Enter your Gemini API key in the web interface
echo   5. Start scanning!
echo.
echo QUICK START:
echo   - Run:        START.bat
echo   - Backend:    start_backend.bat  (separate terminal)
echo   - Frontend:   start_frontend.bat (separate terminal)
echo   - Test:       cd backend ^&^& python test_api.py YOUR_API_KEY
echo.
echo TROUBLESHOOTING:
echo   - Backend logs: Check terminal running backend
echo   - Frontend: Press F12 in browser for console
echo   - Verify: http://localhost:8000/health should return OK
echo.
echo ================================================================
echo.
pause

