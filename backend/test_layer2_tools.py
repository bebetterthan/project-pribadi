"""
Layer 2 Integration Test
Tool Execution System Test

Tests:
- Tool wrapper interface
- Tool registry
- Subprocess execution
- Output parsing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.strix.tools.base import ToolParameters, ToolStatus
from app.strix.tools.wrappers import SubfinderTool, NmapTool
from app.strix.tools.registry import get_tool_registry


def test_tool_registration():
    """Test 2.1: Tool registration and discovery"""
    print("\n" + "="*60)
    print("TEST 2.1: Tool Registration")
    print("="*60)
    
    registry = get_tool_registry()
    
    # Register tools
    registry.register(SubfinderTool)
    registry.register(NmapTool)
    
    # Check registration
    assert registry.get_tool("subfinder") is not None, "Subfinder not registered"
    assert registry.get_tool("nmap") is not None, "Nmap not registered"
    
    # Get by category
    from app.strix.tools.base import ToolCategory
    recon_tools = registry.get_tools_by_category(ToolCategory.RECONNAISSANCE)
    enum_tools = registry.get_tools_by_category(ToolCategory.ENUMERATION)
    
    print(f"✅ Registered tools: {len(registry._tools)}")
    print(f"✅ Reconnaissance tools: {len(recon_tools)}")
    print(f"✅ Enumeration tools: {len(enum_tools)}")
    
    print("\n✅ TEST 2.1 PASSED")


def test_subfinder_command_building():
    """Test 2.2: Subfinder command construction"""
    print("\n" + "="*60)
    print("TEST 2.2: Subfinder Command Building")
    print("="*60)
    
    tool = SubfinderTool()
    
    # Basic command
    params = ToolParameters(
        target="example.com",
        options={"silent": True, "recursive": False},
        timeout=120
    )
    
    command = tool._build_command(params)
    print(f"Command: {' '.join(command)}")
    
    assert "subfinder" in command[0], "Missing subfinder binary"
    assert "-d" in command, "Missing domain flag"
    assert "example.com" in command, "Missing target domain"
    assert "-silent" in command, "Missing silent flag"
    assert "-json" in command, "Missing JSON output"
    
    print("✅ TEST 2.2 PASSED")


def test_target_validation():
    """Test 2.3: Target validation"""
    print("\n" + "="*60)
    print("TEST 2.3: Target Validation")
    print("="*60)
    
    subfinder = SubfinderTool()
    nmap = NmapTool()
    
    # Valid targets
    valid, _ = subfinder._validate_target("example.com")
    assert valid, "Valid domain rejected"
    print(f"✅ Valid domain: example.com")
    
    valid, _ = nmap._validate_target("192.168.1.1")
    assert valid, "Valid IP rejected"
    print(f"✅ Valid IP: 192.168.1.1")
    
    # Invalid targets
    valid, error = subfinder._validate_target("not a domain!")
    assert not valid, "Invalid domain accepted"
    print(f"✅ Invalid domain rejected: {error}")
    
    valid, error = nmap._validate_target("test; rm -rf /")
    assert not valid, "Dangerous command accepted"
    print(f"✅ Dangerous command rejected: {error}")
    
    print("✅ TEST 2.3 PASSED")


def test_output_parsing():
    """Test 2.4: Output parsing"""
    print("\n" + "="*60)
    print("TEST 2.4: Output Parsing")
    print("="*60)
    
    # Test subfinder JSON parsing
    subfinder = SubfinderTool()
    
    mock_output = '''{"host":"www.example.com","source":"crtsh"}
{"host":"api.example.com","source":"virustotal"}
{"host":"mail.example.com","source":"crtsh"}'''
    
    parsed = subfinder._parse_output(mock_output, "")
    
    assert parsed is not None, "Parser returned None"
    assert "subdomains" in parsed, "Missing subdomains field"
    assert "count" in parsed, "Missing count field"
    assert parsed["count"] == 3, f"Expected 3 subdomains, got {parsed['count']}"
    assert "www.example.com" in parsed["subdomains"], "Missing www subdomain"
    
    print(f"✅ Parsed subdomains: {parsed['count']}")
    print(f"✅ Sources: {parsed['sources']}")
    
    print("✅ TEST 2.4 PASSED")


def test_simple_execution():
    """Test 2.5: Simple tool execution (echo command)"""
    print("\n" + "="*60)
    print("TEST 2.5: Simple Execution (Echo Test)")
    print("="*60)
    
    # Create a simple test tool that runs echo
    from app.strix.tools.base import BaseTool, ToolCategory
    
    class EchoTool(BaseTool):
        def __init__(self):
            super().__init__(
                tool_name="echo",
                category=ToolCategory.AUXILIARY,
                description="Echo test tool",
                required_params=[]
            )
        
        def _build_command(self, params: ToolParameters):
            return ["echo", params.target]
        
        def _parse_output(self, stdout: str, stderr: str):
            return {"output": stdout.strip()}
        
        def _validate_target(self, target: str):
            return True, None
    
    tool = EchoTool()
    params = ToolParameters(
        target="Hello from Layer 2!",
        options={},
        timeout=5
    )
    
    result = tool.execute(params)
    
    print(f"Status: {result.status.value}")
    print(f"Exit code: {result.exit_code}")
    print(f"Stdout: {result.stdout.strip()}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    assert result.status == ToolStatus.COMPLETED, f"Execution failed: {result.error_message}"
    assert result.exit_code == 0, "Non-zero exit code"
    assert "Hello from Layer 2!" in result.stdout, "Wrong output"
    
    print("✅ TEST 2.5 PASSED")


def run_all_tests():
    """Run all Layer 2 tests"""
    print("\n" + "="*60)
    print("STRIX LAYER 2 - TOOL EXECUTION SYSTEM TEST")
    print("="*60)
    
    try:
        test_tool_registration()
        test_subfinder_command_building()
        test_target_validation()
        test_output_parsing()
        test_simple_execution()
        
        print("\n" + "="*60)
        print("🎉 ALL LAYER 2 TESTS PASSED!")
        print("="*60)
        print("\n✅ Tool Wrapper Interface: Working")
        print("✅ Tool Registry: Working")
        print("✅ Command Building: Working")
        print("✅ Target Validation: Working")
        print("✅ Output Parsing: Working")
        print("✅ Subprocess Execution: Working")
        print("\n🚀 Ready for Layer 3 (LLM Integration)")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
