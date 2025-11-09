@echo off
REM ========================================
REM Quick Fix Script - Apply all fixes
REM ========================================

echo.
echo ================================================
echo   AI PENTEST AGENT - QUICK FIX
echo ================================================
echo.
echo This script will:
echo   1. Setup environment files
echo   2. Clear caches
echo   3. Restart services
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo [1/4] Setting up environment files...
call SETUP_ENV.bat

echo.
echo [2/4] Clearing frontend cache...
cd frontend
if exist .next (
    echo    Removing .next directory...
    rmdir /s /q .next
    echo    [OK] Cache cleared
) else (
    echo    [INFO] No cache to clear
)

echo.
echo [3/4] Checking backend...
cd ..\backend
if exist pentest.db (
    echo    [OK] Database exists
) else (
    echo    [INFO] Database will be created on first run
)

echo.
echo [4/4] Ready to start!
cd ..

echo.
echo ================================================
echo   FIX COMPLETE!
echo ================================================
echo.
echo Next steps:
echo   1. Run: START_ALL.bat
echo   2. Wait for both servers to start (5-10 seconds)
echo   3. Open http://localhost:3000
echo.
echo Troubleshooting:
echo   - If still having issues, check CHECK_AND_FIX.md
echo   - View logs in terminal windows
echo.
pause

