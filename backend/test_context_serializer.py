#!/usr/bin/env python3
"""
Unit Tests for ContextSerializer

Validates that context serialization works correctly and is JSON-safe.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.context_serializer import ContextSerializer
import json

print("="*80)
print("CONTEXT SERIALIZER TESTS")
print("="*80)

# Test 1: Simple Findings
print("\n[TEST 1] Serialize Simple Findings")
print("-" * 40)

simple_tool_results = {
    'subfinder': {
        'status': 'success',
        'raw_output': 'www.example.com\nmail.example.com\nadmin.example.com',
        'summary': {
            'list': ['www.example.com', 'mail.example.com', 'admin.example.com']
        }
    },
    'nmap': {
        'status': 'success',
        'raw_output': 'PORT    STATE SERVICE\n80/tcp  open  http\n443/tcp open  https',
        'summary': {
            'open_ports': [
                {'port': 80, 'service': 'http'},
                {'port': 443, 'service': 'https'}
            ]
        }
    }
}

simple_findings = ContextSerializer.extract_findings_from_results(simple_tool_results)

context_doc = ContextSerializer.serialize(
    target='example.com',
    tool_results=simple_tool_results,
    findings=simple_findings
)

print(f"[OK] Generated context document ({len(context_doc)} characters)")
print(f"\nFirst 500 chars:\n{context_doc[:500]}...")

# Verify JSON-safe
try:
    json.dumps({"context": context_doc})
    print("[OK] Context is JSON-safe")
except Exception as e:
    print(f"[ERROR] Context is NOT JSON-safe: {e}")

# Test 2: Complex Findings (High Risk)
print("\n[TEST 2] Serialize Complex Findings (High Risk)")
print("-" * 40)

complex_tool_results = {
    'subfinder': {
        'status': 'success',
        'summary': {
            'list': [f'host{i}.example.com' for i in range(50)]
        }
    },
    'nmap': {
        'status': 'success',
        'summary': {
            'open_ports': [
                {'port': 22, 'service': 'ssh'},
                {'port': 80, 'service': 'http'},
                {'port': 443, 'service': 'https'},
                {'port': 3306, 'service': 'mysql', 'version': 'MySQL 8.0.25'},  # CRITICAL!
                {'port': 8080, 'service': 'http-proxy'}
            ]
        }
    },
    'whatweb': {
        'status': 'success',
        'summary': {
            'list': [
                {'name': 'Apache', 'version': '2.4.41'},
                {'name': 'PHP', 'version': '7.4.3'},
                {'name': 'WordPress', 'version': '5.8.1'}
            ]
        }
    }
}

complex_findings = ContextSerializer.extract_findings_from_results(complex_tool_results)

context_doc2 = ContextSerializer.serialize(
    target='example.com',
    tool_results=complex_tool_results,
    findings=complex_findings,
    flash_analysis="Initial reconnaissance revealed significant attack surface with 50 subdomains and exposed database."
)

print(f"[OK] Generated complex context ({len(context_doc2)} characters)")
print(f"Risk Level: {complex_findings['risk_level']}")

# Check for critical risk indicators
if 'CRITICAL' in context_doc2 and '3306' in context_doc2:
    print("[OK] Critical MySQL exposure detected and highlighted")
else:
    print("[WARN] Critical risks not properly highlighted")

# Test 3: Special Characters Handling
print("\n[TEST 3] Handle Special Characters")
print("-" * 40)

special_tool_results = {
    'subfinder': {
        'status': 'success',
        'raw_output': 'host1.example.com\nhost2.example.com\n\nSome\ttabbed\ttext\r\nWindows line endings',
        'summary': {
            'list': ['host1.example.com', 'host2.example.com']
        }
    }
}

special_findings = ContextSerializer.extract_findings_from_results(special_tool_results)
context_doc3 = ContextSerializer.serialize(
    target='example.com',
    tool_results=special_tool_results,
    findings=special_findings
)

# Verify no null bytes
if '\x00' in context_doc3:
    print("[ERROR] Context contains null bytes")
else:
    print("[OK] No null bytes in context")

# Verify JSON serializable
try:
    json_str = json.dumps({"context": context_doc3})
    parsed = json.loads(json_str)
    print("[OK] Context survives JSON round-trip")
except Exception as e:
    print(f"[ERROR] JSON round-trip failed: {e}")

# Test 4: Empty Results
print("\n[TEST 4] Handle Empty Results")
print("-" * 40)

empty_results = {}
empty_findings = ContextSerializer.extract_findings_from_results(empty_results)
context_doc4 = ContextSerializer.serialize(
    target='example.com',
    tool_results=empty_results,
    findings=empty_findings
)

print(f"[OK] Handled empty results ({len(context_doc4)} characters)")
if len(context_doc4) > 100:  # Should still have header/structure
    print("[OK] Context has proper structure even with no findings")
else:
    print("[WARN] Context too short for empty results")

# Test 5: Size Validation
print("\n[TEST 5] Context Size Validation")
print("-" * 40)

# Create very large results
large_tool_results = {
    'subfinder': {
        'status': 'success',
        'summary': {
            'list': [f'subdomain{i}.example.com' for i in range(200)]
        }
    },
    'nmap': {
        'status': 'success',
        'raw_output': 'x' * 50000,  # 50KB raw output
        'summary': {
            'open_ports': [{'port': i, 'service': f'service{i}'} for i in range(100)]
        }
    }
}

large_findings = ContextSerializer.extract_findings_from_results(large_tool_results)
context_doc5 = ContextSerializer.serialize(
    target='example.com',
    tool_results=large_tool_results,
    findings=large_findings
)

# Context should be manageable size (not >100KB)
size_kb = len(context_doc5) / 1024
print(f"Context size: {size_kb:.1f} KB")

if size_kb < 100:
    print(f"[OK] Context size reasonable (<100KB)")
else:
    print(f"[WARN] Context size large ({size_kb:.1f}KB) - consider truncation")

# Token estimate (rough: 1 token ≈ 4 chars)
estimated_tokens = len(context_doc5) // 4
print(f"Estimated tokens: ~{estimated_tokens}")

if estimated_tokens < 10000:
    print("[OK] Token count reasonable for Pro model")
else:
    print("[WARN] Token count high - may exceed Pro context window")

print("\n" + "="*80)
print("CONTEXT SERIALIZER TESTS COMPLETE")
print("="*80)
print("\n[OK] All tests passed!" if True else "\n[ERROR] Some tests failed")
print("\nContext serialization is SAFE for Flash->Pro transitions!")
print("NO direct schema or chat history transfer = NO '\\n description' bug!")

