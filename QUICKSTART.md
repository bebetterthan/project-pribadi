# Quick Start Guide

## 🚀 Quick Installation (For Developers)

### Prerequisites Check
Before starting, ensure you have:
- [ ] Python 3.9+
- [ ] Node.js 18+
- [ ] Nmap installed
- [ ] Nuclei installed
- [ ] WhatWeb installed
- [ ] SSLScan installed
- [ ] Google Gemini API Key

### One-Command Setup (Linux/macOS)

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd AI_Pentesting

# 2. Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 3. Setup frontend (in new terminal)
cd frontend
npm install
cp .env.local.example .env.local

# 4. Verify tools (in backend directory)
python check_tools.py
```

### One-Command Setup (Windows PowerShell)

```powershell
# 1. Clone and enter directory
git clone <repo-url>
cd AI_Pentesting

# 2. Setup backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# 3. Setup frontend (in new terminal)
cd frontend
npm install
copy .env.local.example .env.local

# 4. Verify tools (in backend directory)
python check_tools.py
```

## 🎯 Running the Application

### Option 1: Manual (2 Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# or .\venv\Scripts\Activate.ps1  # Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Using Scripts

**Linux/macOS:**
```bash
# Backend
cd backend
chmod +x start.sh
./start.sh

# Frontend (new terminal)
cd frontend
npm run dev
```

**Windows:**
```powershell
# Backend
cd backend
.\start.ps1

# Frontend (new terminal)
cd frontend
npm run dev
```

## 🧪 Testing the Setup

1. **Check Backend:**
   - Open http://localhost:8000
   - You should see: `{"message": "AI Pentest Agent API"}`
   - Check API docs: http://localhost:8000/api/v1/docs

2. **Check Frontend:**
   - Open http://localhost:3000
   - You should see the dashboard

3. **Run a Test Scan:**
   - Click "Start New Scan"
   - Target: `scanme.nmap.org` (official Nmap test server)
   - Tools: Select all
   - Profile: Quick
   - Enable AI: Yes (enter your Gemini API key)
   - Click "Start Scan"

## 📋 Common Issues

### Backend Won't Start

**Issue:** `Module not found` error
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue:** `Port already in use`
```bash
# Solution: Use different port
uvicorn app.main:app --reload --port 8001

# Update frontend .env.local:
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
```

### Frontend Won't Start

**Issue:** `Cannot find module` errors
```bash
# Solution: Clean install
rm -rf node_modules package-lock.json
npm install
```

**Issue:** `API connection refused`
```bash
# Solution: Verify backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Tools Not Found

**Issue:** `Tool not installed` error
```bash
# Solution: Check tool installation
python backend/check_tools.py

# Install missing tools (see README.md)
```

## 🎓 Next Steps

1. **Read the Full README.md** for detailed documentation
2. **Explore the API docs** at http://localhost:8000/api/v1/docs
3. **Check the project structure** to understand the codebase
4. **Review security notes** before scanning production targets

## ⚠️ Important Reminders

- ✅ Always get permission before scanning any target
- ✅ Use `scanme.nmap.org` for testing
- ✅ Keep your Gemini API key secure
- ✅ This is localhost-only (don't expose to internet)
- ✅ Scan history is stored in SQLite database

## 📞 Need Help?

- Check the full [README.md](README.md)
- Review the [API documentation](http://localhost:8000/api/v1/docs)
- Check logs in `backend/logs/app.log`
