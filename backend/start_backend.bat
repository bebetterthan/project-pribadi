@echo off
echo Starting AI Pentesting Backend Server...
echo.
cd /d "d:\Project pribadi\AI_Pentesting\backend"
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
