@echo off
echo ================================================================================
echo    GEMINI FUNCTION CALLING DIAGNOSTIC TEST
echo ================================================================================
echo.
echo This test will determine which option works for your setup:
echo   Option A: Force function calling mode
echo   Option B: Switch to Gemini 1.5 Pro
echo   Option C: Build JSON parser (last resort)
echo.
echo Running test... (takes 30-60 seconds)
echo.

cd backend
call venv\Scripts\activate.bat

python test_gemini_function_calling.py

echo.
echo ================================================================================
echo Test complete! See results above.
echo ================================================================================
echo.
pause

