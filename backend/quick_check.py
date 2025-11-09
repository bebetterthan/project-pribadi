#!/usr/bin/env python3
"""
Quick check script - verify backend is ready
Run this to debug issues
"""
import sys
import os

print("=" * 60)
print("🔍 QUICK BACKEND CHECK")
print("=" * 60)
print()

# Check 1: Python imports
print("[1/5] Checking Python imports...")
try:
    from app.config import settings
    print("   ✅ Config loaded")
    print(f"      - DEBUG: {settings.DEBUG}")
    print(f"      - USE_MOCK_TOOLS: {settings.USE_MOCK_TOOLS}")
    print(f"      - CORS: {settings.CORS_ORIGINS}")
except Exception as e:
    print(f"   ❌ Failed to load config: {e}")
    sys.exit(1)

# Check 2: SSE Starlette
print("\n[2/5] Checking SSE streaming library...")
try:
    import sse_starlette
    print(f"   ✅ sse-starlette installed: {sse_starlette.__version__ if hasattr(sse_starlette, '__version__') else 'OK'}")
except ImportError:
    print("   ❌ sse-starlette NOT installed!")
    print("      Fix: pip install sse-starlette")
    sys.exit(1)

# Check 3: Google AI
print("\n[3/5] Checking Google AI library...")
try:
    import google.generativeai as genai
    print("   ✅ google-generativeai installed")
    
    # Try to list models (requires API key)
    api_key = os.getenv('GEMINI_API_KEY') or input("   Enter Gemini API key to test (or press Enter to skip): ").strip()
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Try gemini-1.5-pro first
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                print("   ✅ gemini-1.5-pro model available")
            except:
                print("   ⚠️ gemini-1.5-pro not available, trying fallback...")
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    print("   ✅ gemini-pro model available")
                except Exception as model_err:
                    print(f"   ❌ No models available: {model_err}")
        except Exception as api_err:
            print(f"   ❌ API key test failed: {api_err}")
    else:
        print("   ⚠️ API key test skipped")
        
except ImportError:
    print("   ❌ google-generativeai NOT installed!")
    sys.exit(1)

# Check 4: Database
print("\n[4/5] Checking database...")
try:
    from app.db.session import engine
    from app.models import Base
    
    # Try to create tables
    Base.metadata.create_all(bind=engine)
    print("   ✅ Database OK (SQLite)")
    print(f"      File: {settings.DATABASE_URL}")
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Check 5: Tools
print("\n[5/5] Checking scan tools...")
try:
    from app.tools.factory import ToolFactory
    
    tools = ['nmap', 'nuclei', 'whatweb', 'sslscan']
    for tool_name in tools:
        tool = ToolFactory.get_tool(tool_name)
        is_mock = 'Mock' in tool.__class__.__name__
        
        if is_mock:
            print(f"   🔧 {tool_name}: MOCK (fast, simulated)")
        else:
            print(f"   ⚡ {tool_name}: REAL (slow, actual scan)")
            
except Exception as e:
    print(f"   ❌ Tool check error: {e}")

# Summary
print("\n" + "=" * 60)
print("📋 CONFIGURATION SUMMARY")
print("=" * 60)
print(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
print(f"Mock Tools: {'YES (faster, for testing)' if settings.USE_MOCK_TOOLS else 'NO (real scanning)'}")
print(f"CORS Origins: {settings.CORS_ORIGINS}")
print()
print("TO START BACKEND:")
print("  cd backend")
print("  venv\\Scripts\\activate     (Windows)")
print("  uvicorn app.main:app --reload")
print()
print("VERIFY RUNNING:")
print("  Open: http://localhost:8000/health")
print("  Should see: {\"status\": \"healthy\"}")
print()
print("=" * 60)

