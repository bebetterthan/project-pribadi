@echo off
REM ============================================================================
REM   QUICK REFERENCE: AI Pentesting Agent Commands
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                AI PENTESTING AGENT - QUICK REFERENCE                     ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo   📋 STARTUP COMMANDS:
echo   ├─ START_ALL.bat          Start both Backend + Frontend
echo   ├─ STOP_ALL.bat           Stop all services
echo   └─ CHECK_STATUS.bat       Check if services are running
echo.
echo   🔧 BACKEND COMMANDS:
echo   ├─ backend\start.sh                  Start backend (Unix)
echo   ├─ backend\start.ps1                 Start backend (PowerShell)
echo   └─ backend\start_backend.bat         Start backend (Windows)
echo.
echo   🌐 FRONTEND COMMANDS:
echo   ├─ cd frontend ^& npm run dev         Start dev server
echo   ├─ cd frontend ^& npm run build       Build production
echo   └─ cd frontend ^& npm run start       Start production server
echo.
echo   🔍 TESTING COMMANDS:
echo   ├─ TEST_FUNCTION_CALLING.bat         Test AI function calling
echo   ├─ backend\test_api.py               Test backend API
echo   ├─ backend\test_integration.py       Integration tests
echo   └─ backend\check_tools.py            Verify pentesting tools
echo.
echo   📊 DATABASE COMMANDS:
echo   ├─ sqlite3 backend\pentest.db        Open database
echo   ├─ backend\migrate_*.py              Database migrations
echo   └─ View in: backend\pentest.db
echo.
echo   🛠️ TROUBLESHOOTING:
echo   ├─ DIAGNOSE.bat                      Full system diagnostic
echo   ├─ QUICK_FIX.bat                     Apply quick fixes
echo   └─ RESTART_BACKEND.bat               Force restart backend
echo.
echo   📝 LOGS:
echo   ├─ backend\logs\app.log              Application logs
echo   ├─ backend\logs\error_debug.log      Error logs
echo   └─ backend\logs\CRITICAL_ERROR.txt   Critical errors
echo.
echo   🌍 ACCESS URLS:
echo   ├─ Frontend:      http://localhost:3000
echo   ├─ Backend API:   http://localhost:8000
echo   ├─ API Docs:      http://localhost:8000/api/v1/docs
echo   ├─ Health:        http://localhost:8000/api/v1/health
echo   └─ Dashboard:     http://localhost:3000/dashboard
echo.
echo   🔐 ENVIRONMENT:
echo   ├─ SETUP_ENV.bat              Setup environment (Windows)
echo   ├─ SETUP_ENV.sh               Setup environment (Unix)
echo   └─ .env (backend)             API keys ^& config
echo.
echo   🎯 PENTESTING TOOLS:
echo   ├─ Nmap            Network scanning
echo   ├─ Nuclei          Vulnerability scanning
echo   ├─ WhatWeb         Web tech identification
echo   ├─ SSLScan         SSL/TLS analysis
echo   ├─ Subfinder       Subdomain enumeration
echo   ├─ HTTPX           HTTP probing
echo   ├─ FFUF            Web fuzzing
echo   └─ SQLMap          SQL injection testing
echo.
echo   📦 DEPENDENCIES:
echo   ├─ Python 3.9+                Required
echo   ├─ Node.js 18+                Required
echo   ├─ Gemini API Key             Required (for AI)
echo   └─ Pentesting Tools           Optional (use mock mode)
echo.
echo   ⚡ QUICK START:
echo      1. Run: START_ALL.bat
echo      2. Wait for "Backend ready" message
echo      3. Open: http://localhost:3000
echo      4. Create new scan
echo      5. Watch real-time AI analysis
echo.
echo   🆘 COMMON ISSUES:
echo   ├─ Port in use:          Run STOP_ALL.bat first
echo   ├─ Backend won't start:  Check logs, verify Python
echo   ├─ Frontend won't load:  Run: cd frontend ^& npm install
echo   ├─ SSE not working:      Backend not ready, wait longer
echo   └─ No API key:           Set GEMINI_API_KEY in .env
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║  💡 TIP: Keep this window open for quick reference                      ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
pause
