#!/usr/bin/env python3
"""
Quick test script to verify backend setup for AI Pentesting Agent
Personal use - simple pragmatic checks
"""
import sys
import importlib.util

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 10:
        print("   ✅ Python version OK (3.10+)")
        return True
    else:
        print("   ❌ Python version too old (need 3.10+)")
        return False

def check_package(package_name, display_name=None):
    """Check if a package is installed"""
    display = display_name or package_name
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"   ✅ {display} installed")
        return True
    else:
        print(f"   ❌ {display} NOT installed")
        return False

def check_dependencies():
    """Check all critical dependencies"""
    print("\n📦 Checking dependencies...")
    
    deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("sse_starlette", "sse-starlette"),  # CRITICAL - was missing!
        ("google.generativeai", "Google Generative AI"),
        ("pydantic", "Pydantic"),
        ("loguru", "Loguru"),
    ]
    
    all_ok = True
    for package, display in deps:
        if not check_package(package, display):
            all_ok = False
    
    return all_ok

def check_env_config():
    """Check environment configuration"""
    print("\n⚙️ Checking configuration...")
    try:
        from app.config import settings
        print(f"   ✅ Config loaded")
        print(f"      - DEBUG: {settings.DEBUG}")
        print(f"      - USE_MOCK_TOOLS: {settings.USE_MOCK_TOOLS}")
        print(f"      - DATABASE_URL: {settings.DATABASE_URL}")
        print(f"      - CORS_ORIGINS: {settings.CORS_ORIGINS}")
        return True
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False

def check_database():
    """Check database"""
    print("\n💾 Checking database...")
    try:
        from app.db.session import engine
        from app.models import Base
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        print("   ✅ Database connection OK")
        print("   ✅ Tables created/verified")
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_tools():
    """Check scanning tools"""
    print("\n🔧 Checking scanning tools...")
    try:
        from app.tools.factory import ToolFactory
        
        tools = ['nmap', 'nuclei', 'whatweb', 'sslscan']
        for tool_name in tools:
            try:
                tool = ToolFactory.get_tool(tool_name)
                is_installed = tool.is_installed()
                is_mock = tool.__class__.__name__.startswith('Mock')
                
                if is_mock:
                    print(f"   ⚠️ {tool_name}: Using MOCK (real tool not installed)")
                else:
                    print(f"   ✅ {tool_name}: Real tool installed")
            except Exception as e:
                print(f"   ❌ {tool_name}: Error - {e}")
        
        return True
    except Exception as e:
        print(f"   ❌ Tool check error: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🔍 AI PENTESTING AGENT - BACKEND SETUP CHECK")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_env_config),
        ("Database", check_database),
        ("Tools", check_tools),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Backend ready to run!")
        print("   Run: uvicorn app.main:app --reload")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues above")
        print("\n💡 Quick fixes:")
        print("   - Missing packages: pip install -r requirements.txt")
        print("   - sse-starlette missing: pip install sse-starlette")
        print("   - Tools not installed: Set USE_MOCK_TOOLS=True in .env")
    print("=" * 60)

if __name__ == "__main__":
    main()

