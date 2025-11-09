@echo off
echo ================================================================================
echo    AGENT-P BACKEND - WITH ALL CRITICAL FIXES APPLIED
echo ================================================================================
echo.
echo [INFO] Comprehensive fixes applied:
echo   1. Tool Chaining: HTTPX now receives 500 subdomains (not 1)
echo   2. Duplicate Display: Removed (no more RUN_X + X duplicates)
echo   3. COMPLETE_ASSESSMENT: Fixed loop (calls once, not 6x)
echo   4. Logger F-String: Safe error logging (no '\n description' crash)
echo   5. Protobuf KeyError: Comprehensive error handling
echo   6. AI Reasoning: Now displays analysis between tool executions
echo.
echo [ACTION] Killing existing Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul

echo [ACTION] Starting backend with DEBUG logging...
cd backend
venv\Scripts\activate
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
python -Xdev -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

