#!/bin/bash
# ========================================
# Setup Environment Files for AI Pentest Agent
# ========================================

echo ""
echo "================================================"
echo "  SETUP ENVIRONMENT CONFIGURATION"
echo "================================================"
echo ""

# Create frontend .env.local
echo "[1/2] Creating frontend/.env.local..."
cd "$(dirname "$0")/frontend"

if [ -f .env.local ]; then
    echo "   File already exists, backing up..."
    cp .env.local .env.local.backup
fi

cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

if [ $? -eq 0 ]; then
    echo "   ✅ frontend/.env.local created successfully"
else
    echo "   ❌ Failed to create frontend/.env.local"
    exit 1
fi

echo ""
echo "[2/2] Checking backend configuration..."
cd "$(dirname "$0")/backend"

if [ -f .env ]; then
    echo "   ✅ backend/.env already exists"
else
    echo "   ℹ️  No backend/.env found (using defaults)"
fi

cd "$(dirname "$0")"

echo ""
echo "================================================"
echo "  SETUP COMPLETE!"
echo "================================================"
echo ""
echo "Environment files created:"
echo "  - frontend/.env.local ✅"
echo ""
echo "Next steps:"
echo "  1. Make sure backend is running:"
echo "     cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo ""
echo "  2. Start frontend:"
echo "     cd frontend && npm run dev"
echo ""
echo "  3. Open http://localhost:3000"
echo ""

