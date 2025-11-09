# AI Pentesting Backend - Optimized Startup
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONFAULTHANDLER = "1"
$env:LOG_LEVEL = "INFO"

cd "D:\Project pribadi\AI_Pentesting\backend"

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  BACKEND API SERVER - FastAPI + Uvicorn                 ║" -ForegroundColor Cyan
Write-Host "║  Hybrid AI: Flash 2.5 ^(Tactical^) + Pro 2.5 ^(Strategic^)  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Port:     http://localhost:8000" -ForegroundColor Green
Write-Host "   Docs:     http://localhost:8000/api/v1/docs" -ForegroundColor Yellow
Write-Host "   Health:   http://localhost:8000/api/v1/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "▶ Starting server with auto-reload..." -ForegroundColor Green
Write-Host ""

try {
    & venv\Scripts\python.exe -u -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info --use-colors
} catch {
    Write-Host ""
    Write-Host "✗ Backend startup failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check if port 8000 is already in use" -ForegroundColor Gray
    Write-Host "  2. Verify virtual environment: .\venv\Scripts\activate" -ForegroundColor Gray
    Write-Host "  3. Check logs: .\logs\app.log" -ForegroundColor Gray
    Write-Host ""
    pause
}
