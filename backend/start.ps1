# AI Pentest Agent - Backend Startup Script (PowerShell)

Write-Host "🛡️  Starting AI Pentest Agent Backend..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found. Please run installation first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Check if dependencies are installed
python -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependencies not installed. Installing now..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Create logs directory if it doesn't exist
if (-Not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start the server
Write-Host "✅ Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
