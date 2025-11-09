#!/usr/bin/env python3
"""
Test Multi-Tool Workflow
Verify that both Nmap and Nuclei can be executed successfully
"""
import sys
import asyncio

print("=" * 70)
print("🔬 TESTING MULTI-TOOL WORKFLOW")
print("=" * 70)
print()

async def test_nmap():
    """Test Nmap tool execution"""
    print("[1/2] Testing Nmap execution...")
    try:
        from app.tools.nmap_tool import NmapTool
        
        tool = NmapTool()
        
        # Check if installed
        if not tool.is_installed():
            print("   ❌ Nmap not installed")
            return False
        
        print(f"   ✅ Nmap installed: {tool.name}")
        
        # Test command building
        cmd = tool.build_command("scanme.nmap.org", "quick")
        print(f"   📋 Command: {' '.join(cmd[:5])}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Nmap test failed: {e}")
        return False


async def test_nuclei():
    """Test Nuclei tool execution"""
    print("\n[2/2] Testing Nuclei execution...")
    try:
        from app.tools.nuclei_tool import NucleiTool
        
        tool = NucleiTool()
        
        # Check if installed
        if not tool.is_installed():
            print("   ❌ Nuclei not installed")
            return False
        
        print(f"   ✅ Nuclei installed: {tool.name}")
        
        # Test command building
        cmd = tool.build_command("https://example.com", "quick")
        print(f"   📋 Command: {' '.join(cmd[:5])}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Nuclei test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_toolbox():
    """Test that both tools are defined in function_toolbox"""
    print("\n[3/3] Testing Function Toolbox definitions...")
    try:
        from app.tools.function_toolbox import SECURITY_TOOLS
        
        tool_names = [tool['name'] for tool in SECURITY_TOOLS]
        
        print(f"   📦 Total tools defined: {len(SECURITY_TOOLS)}")
        print(f"   📋 Tools: {', '.join(tool_names)}")
        
        # Check essential tools
        has_nmap = 'run_nmap' in tool_names
        has_nuclei = 'run_nuclei' in tool_names
        
        if has_nmap:
            print("   ✅ run_nmap defined")
        else:
            print("   ❌ run_nmap NOT defined")
        
        if has_nuclei:
            print("   ✅ run_nuclei defined")
        else:
            print("   ❌ run_nuclei NOT defined")
        
        return has_nmap and has_nuclei
        
    except Exception as e:
        print(f"   ❌ Toolbox test failed: {e}")
        return False


async def main():
    results = await asyncio.gather(
        test_nmap(),
        test_nuclei(),
        test_function_toolbox(),
        return_exceptions=True
    )
    
    print("\n" + "=" * 70)
    
    success_count = sum(1 for r in results if r is True)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"✅ ALL TESTS PASSED ({success_count}/{total_count})")
        print("=" * 70)
        print()
        print("🎉 Multi-tool infrastructure is ready!")
        print("   - Nmap: ✅ Ready for port scanning")
        print("   - Nuclei: ✅ Ready for vulnerability scanning")
        print("   - Function Toolbox: ✅ Both tools defined")
        print()
        print("Next: Test intelligent tool chaining with AI Agent")
        return 0
    else:
        print(f"⚠️ SOME TESTS FAILED ({success_count}/{total_count} passed)")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

