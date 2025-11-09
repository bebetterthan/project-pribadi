#!/usr/bin/env python3
"""
Comprehensive Protobuf Parsing Debugger
Captures detailed information about '\n description' error
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import google.generativeai as genai
from google.protobuf.json_format import MessageToDict
import json
from typing import Any, Dict

def test_protobuf_conversion():
    """Test protobuf Struct conversion with various scenarios"""
    
    print("="*80)
    print("PROTOBUF PARSING DEBUG TEST")
    print("="*80)
    print()
    
    # Test 1: Direct protobuf field access
    print("[TEST 1] Testing protobuf Struct with special characters")
    print("-" * 80)
    
    try:
        # Create a mock protobuf Struct with problematic keys
        from google.protobuf.struct_pb2 import Struct
        
        test_struct = Struct()
        
        # Test cases
        test_cases = [
            ("normal_key", "normal_value"),
            ("key_with_spaces", "value with spaces"),
            ("key\nwith\nnewlines", "value\nwith\nnewlines"),
            ("\n description", "This is the problematic key!"),
            ("description", "Normal description"),
        ]
        
        for key, value in test_cases:
            print(f"\nTesting key: {repr(key)}")
            try:
                test_struct.fields[key].string_value = value
                print(f"  ✅ Successfully added to Struct")
                
                # Try to access it back
                retrieved = test_struct.fields[key].string_value
                print(f"  ✅ Successfully retrieved: {repr(retrieved)}")
                
                # Try MessageToDict
                try:
                    as_dict = MessageToDict(test_struct, preserving_proto_field_name=True)
                    print(f"  ✅ MessageToDict successful")
                    print(f"     Keys in dict: {list(as_dict.keys())}")
                    
                    # Check if problematic key is in dict
                    if key in as_dict:
                        print(f"  ✅ Key '{repr(key)}' found in dict")
                    else:
                        print(f"  ⚠️ Key '{repr(key)}' NOT found in dict")
                        print(f"     Available keys: {list(as_dict.keys())}")
                        
                except KeyError as ke:
                    print(f"  ❌ KeyError in MessageToDict: {repr(str(ke))}")
                except Exception as e:
                    print(f"  ❌ Error in MessageToDict: {type(e).__name__}: {e}")
                
            except Exception as e:
                print(f"  ❌ Error: {type(e).__name__}: {e}")
        
        print("\n" + "-" * 80)
        print("[TEST 1 COMPLETE]")
        print()
        
    except Exception as e:
        print(f"❌ Test 1 failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Iteration over Struct
    print("\n[TEST 2] Testing iteration over Struct with special keys")
    print("-" * 80)
    
    try:
        for key in test_struct.fields:
            print(f"\nIterating key: {repr(key)}")
            try:
                value = test_struct.fields[key]
                print(f"  ✅ Value type: {type(value)}")
                print(f"  ✅ Value: {value}")
                
                # Try to clean key
                clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                print(f"  ✅ Cleaned key: {repr(clean_key)}")
                
            except KeyError as ke:
                print(f"  ❌ KeyError during iteration: {repr(str(ke))}")
            except Exception as e:
                print(f"  ❌ Error: {type(e).__name__}: {e}")
        
        print("\n" + "-" * 80)
        print("[TEST 2 COMPLETE]")
        print()
        
    except Exception as e:
        print(f"❌ Test 2 failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: JSON serialization
    print("\n[TEST 3] Testing JSON serialization")
    print("-" * 80)
    
    try:
        # Convert to dict
        as_dict = {}
        for key in test_struct.fields:
            clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
            value = test_struct.fields[key]
            
            # Extract string value
            if value.HasField('string_value'):
                as_dict[clean_key] = value.string_value
        
        print(f"Dictionary created: {len(as_dict)} keys")
        print(f"Keys: {list(as_dict.keys())}")
        
        # Try JSON dumps
        try:
            json_str = json.dumps(as_dict, indent=2)
            print(f"✅ JSON serialization successful")
            print(f"JSON output (first 500 chars):\n{json_str[:500]}")
        except Exception as e:
            print(f"❌ JSON serialization failed: {type(e).__name__}: {e}")
        
        print("\n" + "-" * 80)
        print("[TEST 3 COMPLETE]")
        print()
        
    except Exception as e:
        print(f"❌ Test 3 failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)


def analyze_gemini_function_call():
    """Analyze actual Gemini function call response structure"""
    
    print("\n" + "="*80)
    print("GEMINI FUNCTION CALL STRUCTURE ANALYSIS")
    print("="*80)
    print()
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment")
        print("   Skipping real API test")
        return
    
    print(f"✅ API Key found (length: {len(api_key)})")
    print()
    
    try:
        genai.configure(api_key=api_key)
        
        # Import tool definitions
        from app.tools.function_toolbox import SECURITY_TOOLS
        
        print(f"✅ Loaded {len(SECURITY_TOOLS)} tool definitions")
        print()
        
        # Create a simple test model
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools=SECURITY_TOOLS
        )
        
        print("✅ Model created successfully")
        print()
        
        # Send a test message that will trigger function call
        test_prompt = """
        Target: example.com
        
        Please scan the target for open ports. Use the appropriate tool.
        """
        
        print("📤 Sending test prompt to Gemini...")
        print(f"Prompt: {test_prompt[:100]}...")
        print()
        
        response = model.generate_content(test_prompt)
        
        print("📥 Response received")
        print()
        
        # Analyze response structure
        for idx, part in enumerate(response.parts):
            print(f"\n[PART {idx}]")
            print(f"  Type: {type(part)}")
            print(f"  Has function_call: {hasattr(part, 'function_call')}")
            
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                print(f"  Function name: {fc.name}")
                print(f"  Args type: {type(fc.args)}")
                print(f"  Has _pb: {hasattr(fc.args, '_pb')}")
                
                if hasattr(fc.args, '_pb'):
                    print(f"  _pb type: {type(fc.args._pb)}")
                    print(f"  _pb has DESCRIPTOR: {hasattr(fc.args._pb, 'DESCRIPTOR')}")
                
                # Try to iterate
                print(f"\n  Iterating over args:")
                try:
                    for key in fc.args:
                        print(f"    Key: {repr(key)}")
                        print(f"    Key type: {type(key)}")
                        print(f"    Key has newline: {'\\n' in str(key)}")
                        try:
                            value = fc.args[key]
                            print(f"    Value: {repr(str(value)[:100])}")
                        except Exception as e:
                            print(f"    ❌ Error accessing value: {e}")
                except Exception as e:
                    print(f"    ❌ Error iterating: {type(e).__name__}: {e}")
                
                # Try MessageToDict
                print(f"\n  Trying MessageToDict:")
                try:
                    from google.protobuf.json_format import MessageToDict
                    if hasattr(fc.args, '_pb') and hasattr(fc.args._pb, 'DESCRIPTOR'):
                        as_dict = MessageToDict(fc.args._pb, preserving_proto_field_name=True)
                        print(f"    ✅ Success")
                        print(f"    Keys: {list(as_dict.keys())}")
                    else:
                        print(f"    ⚠️ Cannot use MessageToDict (_pb lacks DESCRIPTOR)")
                except KeyError as ke:
                    print(f"    ❌ KeyError: {repr(str(ke))}")
                    print(f"       THIS IS THE '\n description' ERROR!")
                except Exception as e:
                    print(f"    ❌ Error: {type(e).__name__}: {e}")
        
        print("\n" + "="*80)
        print("GEMINI ANALYSIS COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error in Gemini analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "🔬 COMPREHENSIVE PROTOBUF PARSING DEBUG" + "\n")
    
    # Run all tests
    test_protobuf_conversion()
    analyze_gemini_function_call()
    
    print("\n" + "✅ DEBUG SCRIPT COMPLETE" + "\n")

