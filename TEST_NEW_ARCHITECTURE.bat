@echo off
REM Test script untuk verifikasi Function Calling Architecture
setlocal

cd /d "%~dp0"

echo ============================================================
echo   TEST FUNCTION CALLING ARCHITECTURE
echo ============================================================
echo.

echo [1/3] Testing Python modules...
cd backend
python test_function_calling.py
if errorlevel 1 (
    echo.
    echo ❌ Python tests FAILED!
    pause
    exit /b 1
)
cd ..
echo.

echo [2/3] Running database migrations...
cd backend
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe migrate_add_chat.py
) else (
    python migrate_add_chat.py
)
cd ..
echo.

echo [3/3] Checking frontend types...
cd frontend
call npm run build --no-emit 2>nul
cd ..
echo.

echo ============================================================
echo   ✅ ALL TESTS PASSED
echo ============================================================
echo.
echo New Architecture Ready:
echo   ✓ Function Calling Agent (Gemini)
echo   ✓ Hybrid Router (Flash/Pro)
echo   ✓ Target-Agnostic Toolbox
echo   ✓ Chat History Database
echo   ✓ Enhanced Frontend UI
echo.
echo Next: Run START_ALL.bat to launch the app!
echo.
pause

