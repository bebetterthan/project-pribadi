# 🛡️ AI Pentest Agent

> Automated penetration testing platform with AI-powered analysis using Google Gemini

A lightweight, localhost-focused penetration testing tool that integrates multiple security scanning tools (Nmap, Nuclei, WhatWeb, SSLScan) with AI analysis for automated reconnaissance and vulnerability assessment.

## 🎯 Features

- **Multiple Pentesting Tools**
  - 🔍 **Nmap**: Network scanning and service detection
  - 🎯 **Nuclei**: Vulnerability scanning with 10,000+ templates
  - 🌐 **WhatWeb**: Web technology identification
  - 🔐 **SSLScan**: SSL/TLS security analysis

- **AI-Powered Analysis**
  - 🤖 Google Gemini integration for intelligent vulnerability analysis
  - Actionable exploitation recommendations
  - False positive detection
  - Attack path suggestions

- **Modern Web Interface**
  - Built with Next.js 14 and React
  - Real-time scan progress tracking
  - Beautiful UI with Tailwind CSS
  - Scan history management

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (with WSL recommended)
- **Python**: 3.9 or higher
- **Node.js**: 18.x or higher
- **npm** or **yarn**

### Required Tools
You need to install the following penetration testing tools on your system:

#### 1. Nmap
```bash
# Ubuntu/Debian
sudo apt install nmap

# macOS
brew install nmap

# Windows
# Download from https://nmap.org/download.html
```

#### 2. Nuclei
```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Or download binary from https://github.com/projectdiscovery/nuclei/releases
```

#### 3. WhatWeb
```bash
# Ubuntu/Debian
sudo apt install whatweb

# macOS
brew install whatweb

# Or from source
git clone https://github.com/urbanadventurer/WhatWeb.git
cd WhatWeb
sudo make install
```

#### 4. SSLScan
```bash
# Ubuntu/Debian
sudo apt install sslscan

# macOS
brew install sslscan

# Or from source
git clone https://github.com/rbsec/sslscan.git
cd sslscan
make
sudo make install
```

### Google Gemini API Key
Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI_Pentesting
```

### 2. Backend Setup

#### Create Python Virtual Environment
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
.\venv\Scripts\activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (defaults should work for localhost)
```

#### Initialize Database
The database will be automatically created on first run, but you can verify the setup:
```bash
# The app will create pentest.db SQLite database automatically
python -m app.main
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
# or
yarn install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local if backend is not on default port
# Default: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 🎮 Usage

### Start the Backend Server

```bash
cd backend

# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- Health Check: http://localhost:8000/health

### Start the Frontend

Open a new terminal:

```bash
cd frontend

# Start Next.js development server
npm run dev
# or
yarn dev
```

The web interface will be available at: http://localhost:3000

## 📖 How to Use

### 1. Open Web Interface
Navigate to http://localhost:3000 in your browser

### 2. Start a New Scan
Click "Start New Scan" and configure:
- **Target**: Enter domain, IP, or URL (e.g., `example.com`, `192.168.1.1`)
- **Tools**: Select which tools to run
- **Scan Profile**:
  - **Quick**: 2-3 minutes (fast scan, limited scope)
  - **Normal**: 5-7 minutes (recommended)
  - **Aggressive**: 10-15 minutes (comprehensive scan)
- **AI Analysis**: Enable and provide your Gemini API key

### 3. View Results
- **AI Analysis Tab**: View intelligent analysis with exploitation recommendations
- **Tool Results Tab**: View raw and parsed output from each tool

### 4. Scan History
Access all previous scans from the History page

## 🏗️ Project Structure

```
AI_Pentesting/
├── backend/                 # Python FastAPI Backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tools/          # Tool wrappers
│   │   └── utils/          # Utilities
│   ├── requirements.txt
│   └── .env
│
├── frontend/               # Next.js Frontend
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # Utilities
│   │   ├── store/         # State management
│   │   └── types/         # TypeScript types
│   ├── package.json
│   └── .env.local
│
└── README.md
```

## 🔒 Security Notes

### Input Validation
- All targets are validated and sanitized
- Command injection prevention with parameterized execution
- Blacklisted private IP ranges (localhost, private networks)

### API Key Handling
- API keys are stored in browser session only
- Never persisted to database or logs
- Transmitted via secure headers

### Localhost Only (MVP)
- Designed for local development and testing
- No authentication system (single user)
- Do not expose to public internet

## 🛠️ API Endpoints

### Scan Management
- `POST /api/v1/scan` - Create and start new scan
- `GET /api/v1/scan/{scan_id}` - Get scan status
- `GET /api/v1/scan/{scan_id}/results` - Get complete scan results
- `DELETE /api/v1/scan/{scan_id}` - Delete scan

### Analysis
- `GET /api/v1/analysis/{scan_id}` - Get AI analysis

### History
- `GET /api/v1/history` - Get scan history (with pagination)

Full API documentation: http://localhost:8000/api/v1/docs

## 📊 Database Schema

### Scans Table
- Stores scan metadata (target, tools, status, timestamps)

### Scan Results Table
- Stores output from each tool (raw + parsed)

### AI Analyses Table
- Stores AI analysis with token usage and cost

## 🐛 Troubleshooting

### Backend Issues

**Database locked error**
```bash
# Delete the database file and restart
rm pentest.db
```

**Tool not found error**
```bash
# Verify tool installation
nmap --version
nuclei -version
whatweb --version
sslscan --version
```

**Port already in use**
```bash
# Use different port
uvicorn app.main:app --port 8001
```

### Frontend Issues

**Module not found errors**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**API connection refused**
```bash
# Check backend is running on http://localhost:8000
# Verify .env.local has correct API URL
```

## 🚧 Limitations (MVP)

- **Synchronous execution**: Scans run sequentially, not parallel
- **No real-time updates**: Must refresh to see progress
- **Single user**: No authentication or multi-user support
- **Localhost only**: Not designed for production deployment
- **No persistent API keys**: Must re-enter on refresh

## 🔮 Future Enhancements

- [ ] Async task queue with Celery
- [ ] WebSocket for real-time updates
- [ ] Heavy tool integration (OWASP ZAP, sqlmap, Burp Suite)
- [ ] User authentication system
- [ ] Scheduled scans
- [ ] Export reports (PDF, JSON, HTML)
- [ ] Scan comparison and diff
- [ ] Custom tool configuration
- [ ] Deployment to cloud (GCP)

## 📝 License

MIT License - See LICENSE file for details

## 👤 Author

Built with ❤️ for penetration testing automation

## 🙏 Acknowledgments

- [Nmap](https://nmap.org/) - Network scanning
- [Nuclei](https://github.com/projectdiscovery/nuclei) - Vulnerability scanning
- [WhatWeb](https://github.com/urbanadventurer/WhatWeb) - Technology identification
- [SSLScan](https://github.com/rbsec/sslscan) - SSL/TLS testing
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI analysis
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework

## ⚠️ Disclaimer

This tool is for educational and authorized testing purposes only. Always ensure you have explicit permission before scanning any target. Unauthorized access to computer systems is illegal.
