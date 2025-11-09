@echo off
REM ========================================
REM Test Backend-Frontend Connection
REM ========================================

echo.
echo ================================================
echo   CONNECTION TEST
echo ================================================
echo.

echo [1/3] Testing Backend Health...
curl -s http://localhost:8000/health >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo    [OK] Backend is running at http://localhost:8000
    curl -s http://localhost:8000/health
    echo.
) else (
    echo    [ERROR] Backend is NOT running!
    echo    Start it with: START_ALL.bat
    echo    Or manually: cd backend ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Testing API Documentation...
curl -s http://localhost:8000/api/v1/docs >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo    [OK] API Docs available at http://localhost:8000/api/v1/docs
) else (
    echo    [WARNING] API Docs endpoint issue
)

echo.
echo [3/3] Testing Frontend Connection...
curl -s http://localhost:3000 >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo    [OK] Frontend is running at http://localhost:3000
) else (
    echo    [WARNING] Frontend is NOT running
    echo    Start it with: cd frontend ^&^& npm run dev
)

echo.
echo ================================================
echo   TEST COMPLETE
echo ================================================
echo.
echo Next: Open http://localhost:3000 in browser
echo.
pause

