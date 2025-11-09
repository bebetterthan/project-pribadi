@echo off
REM Quick restart backend only (for debugging)

REM Colors
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

echo %BLUE%================================================================================
echo    QUICK BACKEND RESTART (Debug Mode)
echo ================================================================================%RESET%
echo.

echo %YELLOW%[1/3] Stopping existing backend...%RESET%

REM Kill port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Also kill any Python processes that might be hanging
echo Killing any hanging Python processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1

timeout /t 2 /nobreak >nul

REM Verify port is free
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo %YELLOW%[WARNING] Port 8000 still in use! Force killing again...%RESET%
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo %GREEN%[OK] Backend stopped%RESET%
echo.

echo %YELLOW%[2/3] Starting backend with DEBUG logging...%RESET%
cd backend

REM Ensure logs directory exists
if not exist "logs" mkdir logs

REM Start backend with PowerShell for better output
start "AI Pentest - Backend [DEBUG]" powershell -NoExit -ExecutionPolicy Bypass -Command ^
"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; ^
$env:PYTHONIOENCODING='utf-8'; ^
$env:PYTHONUNBUFFERED='1'; ^
$env:LOG_LEVEL='DEBUG'; ^
Write-Host '=============================================' -ForegroundColor Cyan; ^
Write-Host '  BACKEND DEBUG MODE - FULL ERROR LOGS' -ForegroundColor Cyan; ^
Write-Host '=============================================' -ForegroundColor Cyan; ^
Write-Host ''; ^
Write-Host 'All errors will appear in this window' -ForegroundColor Yellow; ^
Write-Host 'Log Level: DEBUG' -ForegroundColor Green; ^
Write-Host ''; ^
Write-Host '=============================================' -ForegroundColor Cyan; ^
Write-Host ''; ^
cd 'D:\Project pribadi\AI_Pentesting\backend'; ^
& venv\Scripts\python.exe -X dev -u -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug --access-log --use-colors"

cd ..
echo %GREEN%[OK] Backend started%RESET%
echo.

echo %YELLOW%[3/3] Waiting for backend to be ready...%RESET%
timeout /t 5 /nobreak >nul

REM Check if backend is listening
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[OK] Backend is running on port 8000!%RESET%
    echo.
    echo %BLUE%================================================================================%RESET%
    echo %GREEN%[SUCCESS] Backend restarted with full debug logging%RESET%
    echo %BLUE%================================================================================%RESET%
    echo.
    echo %YELLOW%Watch the backend window for detailed error logs%RESET%
    echo %YELLOW%Logs also saved to: backend\logs\error_debug.log%RESET%
    echo.
) else (
    echo %RED%[ERROR] Backend failed to start!%RESET%
    echo %YELLOW%Check the backend window for errors%RESET%
    echo.
)

pause
