@echo off
echo ================================================================================
echo    PROTOBUF PARSING DEBUGGER
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/2] Loading environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

echo [2/2] Running debug script...
echo.
python debug_protobuf_parsing.py
echo.

echo ================================================================================
echo    DEBUG COMPLETE
echo ================================================================================
echo.
echo Check output above for '\n description' error analysis
echo.
pause

