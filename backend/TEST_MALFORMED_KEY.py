#!/usr/bin/env python3
"""
Test to reproduce '\n  description' error
Simulates Gemini API returning malformed protobuf keys
"""
import sys

print("="*80)
print("TEST: Reproducing '\n  description' error")
print("="*80)

# Simulate protobuf Struct with malformed keys
class MockStruct:
    """Mock protobuf Struct with malformed keys"""
    
    def __init__(self):
        # Store with malformed keys (newline + spaces)
        self._data = {
            '\n  description': 'Scan 100 port teratas',
            'target_placeholder': 'TARGET_HOST',
            'scan_profile': 'normal'
        }
    
    def __iter__(self):
        """Allow iteration over keys"""
        return iter(self._data.keys())
    
    def __getitem__(self, key):
        """Allow dictionary-like access"""
        # THIS might raise KeyError if key doesn't match exactly
        if key in self._data:
            return self._data[key]
        else:
            # Try with cleaned key
            for stored_key in self._data:
                clean_stored = stored_key.strip().replace('\n', '').replace('\r', '').replace('\t', '')
                clean_requested = key.strip().replace('\n', '').replace('\r', '').replace('\t', '')
                if clean_stored == clean_requested:
                    return self._data[stored_key]
            raise KeyError(repr(key))  # This will show as KeyError: "'description'"

# Test the iteration and access pattern
mock_args = MockStruct()

print("\nTest 1: Iterating over keys")
print("-" * 40)
for key in mock_args:
    print(f"  Raw key: {repr(key)}")
    clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
    print(f"  Clean key: {repr(clean_key)}")
    
    # Try to access with ORIGINAL key (this should work)
    try:
        value = mock_args[key]  # Use original key
        print(f"  Access with original key: SUCCESS")
        print(f"  Value: {value}")
    except KeyError as e:
        print(f"  Access with original key: FAILED - {e}")
    
    # Try to access with CLEAN key (this might fail!)
    try:
        value = mock_args[clean_key]  # Use clean key
        print(f"  Access with clean key: SUCCESS")
    except KeyError as e:
        print(f"  Access with clean key: FAILED - {e}")
        print(f"  ERROR MESSAGE: {repr(str(e))}")
    print()

print("="*80)
print("KEY FINDING: If KeyError message is '\\n  description',")
print("then we're trying to ACCESS with CLEANED key instead of ORIGINAL!")
print("="*80)

# Test correct approach
print("\nTest 2: CORRECT approach - access with ORIGINAL, store with CLEAN")
print("-" * 40)
arguments = {}
for key in mock_args:
    clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
    value = mock_args[key]  # Access with ORIGINAL
    arguments[clean_key] = value  # Store with CLEAN
    print(f"  Stored: {repr(clean_key)} = {value}")

print(f"\nFinal arguments: {arguments}")
print("\nSUCCESS! This approach works!")

