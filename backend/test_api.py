#!/usr/bin/env python3
"""
Quick API test script - test backend endpoints
Personal use - pragmatic testing
"""
import requests
import time
import sys

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check OK")
            print(f"      Status: {data.get('status')}")
            print(f"      Mock tools: {data.get('mock_tools')}")
            print(f"      Debug mode: {data.get('debug_mode')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to backend at {API_BASE}")
        print(f"      Make sure backend is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_docs():
    """Test API documentation"""
    print("\n📚 Testing /api/v1/docs endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/v1/docs", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API docs accessible")
            print(f"      URL: {API_BASE}/api/v1/docs")
            return True
        else:
            print(f"   ❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_create_scan(api_key=None):
    """Test creating a scan"""
    print("\n🔬 Testing scan creation...")
    
    if not api_key:
        print("   ⚠️ Skipping (no API key provided)")
        print("      To test: python test_api.py YOUR_GEMINI_API_KEY")
        return None
    
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Gemini-API-Key": api_key
        }
        
        data = {
            "target": "scanme.nmap.org",
            "user_prompt": "Quick test scan to find open ports",
            "tools": ["nmap"],
            "profile": "quick",
            "enable_ai": True
        }
        
        print(f"   📤 Creating scan for {data['target']}...")
        response = requests.post(
            f"{API_BASE}/api/v1/scan/stream/create",
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            scan_id = result.get('scan_id')
            print(f"   ✅ Scan created successfully")
            print(f"      Scan ID: {scan_id}")
            print(f"      Stream URL: {result.get('stream_url')}")
            return scan_id
        else:
            print(f"   ❌ Scan creation failed: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_sse_stream(scan_id):
    """Test SSE streaming endpoint"""
    print(f"\n📡 Testing SSE stream for scan {scan_id}...")
    
    try:
        url = f"{API_BASE}/api/v1/scan/stream/{scan_id}"
        print(f"   📡 Connecting to {url}")
        print(f"   ⏳ Waiting for events (10 seconds)...")
        
        response = requests.get(url, stream=True, timeout=15)
        
        if response.status_code == 200:
            print(f"   ✅ SSE connection established")
            
            event_count = 0
            start_time = time.time()
            
            for line in response.iter_lines():
                if time.time() - start_time > 10:  # 10 second timeout
                    break
                
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        event_count += 1
                        event_data = decoded[6:]  # Remove 'data: ' prefix
                        print(f"      📨 Event {event_count}: {event_data[:80]}...")
            
            print(f"   ✅ Received {event_count} events in 10 seconds")
            if event_count == 0:
                print(f"      ⚠️ No events received - check backend logs")
            return True
        else:
            print(f"   ❌ SSE connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI PENTESTING AGENT - API TESTS")
    print("=" * 60)
    
    # Get API key from command line
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run tests
    results = []
    
    # Basic tests
    results.append(("Health Check", test_health()))
    results.append(("API Docs", test_api_docs()))
    
    # Scan tests (only if API key provided)
    if api_key:
        scan_id = test_create_scan(api_key)
        results.append(("Create Scan", scan_id is not None))
        
        if scan_id:
            time.sleep(2)  # Wait a bit for background task to start
            results.append(("SSE Stream", test_sse_stream(scan_id)))
    else:
        print("\n⚠️ Skipping scan tests (no API key)")
        print("   Usage: python test_api.py YOUR_GEMINI_API_KEY")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Backend working!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("=" * 60)

if __name__ == "__main__":
    main()

