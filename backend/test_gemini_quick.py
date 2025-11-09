#!/usr/bin/env python3
"""
Quick Gemini API test - verify connectivity
Run: python test_gemini_quick.py
"""
import os
import sys

print("=" * 60)
print("🧪 QUICK GEMINI API TEST")
print("=" * 60)
print()

# Test 1: Import
print("[1/4] Testing imports...")
try:
    import google.generativeai as genai
    print("   ✅ google-generativeai imported")
except ImportError as e:
    print(f"   ❌ Failed to import: {e}")
    print("   Fix: pip install google-generativeai")
    sys.exit(1)

# Test 2: API Key
print("\n[2/4] Checking API key...")
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    api_key = input("   Enter your Gemini API key: ").strip()

if not api_key or len(api_key) < 20:
    print("   ❌ Invalid API key")
    sys.exit(1)

print(f"   ✅ API key present (length: {len(api_key)})")

# Test 3: Configure
print("\n[3/4] Configuring Gemini...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ Configuration successful")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    sys.exit(1)

# Test 4: Quick Generation
print("\n[4/4] Testing API call...")
try:
    # Try latest model first
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("   Using: gemini-2.0-flash-exp")
    except:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("   Using fallback: gemini-1.5-flash-latest")
    
    response = model.generate_content("Say 'Hello!' in one word only.")
    print(f"   ✅ API call successful!")
    print(f"   📝 Response: {response.text[:100]}")
    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED - Gemini API is working!")
    print("=" * 60)
except Exception as e:
    print(f"   ❌ API call failed: {e}")
    print()
    print("   Possible issues:")
    print("   - Invalid API key")
    print("   - No internet connection")
    print("   - API quota exceeded")
    print("   - Firewall blocking Google API")
    sys.exit(1)

