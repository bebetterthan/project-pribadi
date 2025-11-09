@echo off
REM ========================================
REM Setup Environment Files for AI Pentest Agent
REM ========================================

echo.
echo ================================================
echo   SETUP ENVIRONMENT CONFIGURATION
echo ================================================
echo.

REM Create frontend .env.local
echo [1/2] Creating frontend/.env.local...
cd /d "%~dp0frontend"

if exist .env.local (
    echo    File already exists, backing up...
    copy .env.local .env.local.backup >nul 2>&1
)

(
echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
) > .env.local

if %ERRORLEVEL% EQU 0 (
    echo    [OK] frontend/.env.local created successfully
) else (
    echo    [ERROR] Failed to create frontend/.env.local
    pause
    exit /b 1
)

echo.
echo [2/2] Checking backend configuration...
cd /d "%~dp0backend"

if exist .env (
    echo    [OK] backend/.env already exists
) else (
    echo    [INFO] No backend/.env found ^(using defaults^)
)

cd /d "%~dp0"

echo.
echo ================================================
echo   SETUP COMPLETE!
echo ================================================
echo.
echo Environment files created:
echo   - frontend/.env.local [OK]
echo.
echo Next steps:
echo   1. Run: START_ALL.bat
echo   2. Or manually:
echo      - Backend: cd backend ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload
echo      - Frontend: cd frontend ^&^& npm run dev
echo.
echo   3. Open http://localhost:3000
echo.
if "%1" NEQ "silent" pause

