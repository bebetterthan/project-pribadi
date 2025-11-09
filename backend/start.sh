#!/bin/bash

# AI Pentest Agent - Backend Startup Script

echo "🛡️  Starting AI Pentest Agent Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run installation first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed. Installing now..."
    pip install -r requirements.txt
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "✅ Starting FastAPI server on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
