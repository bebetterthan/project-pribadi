"""Test all Fase 3.6 tools"""
import os
from app.tools.subfinder_tool import SubfinderTool
from app.tools.httpx_tool import HttpxTool
from app.tools.whatweb_tool import WhatWebTool
from app.tools.ffuf_tool import FfufTool

print("=" * 70)
print("🔧 FASE 3.6: ALL TOOLS CHECK")
print("=" * 70)
print()

# Test each tool
tools = [
    ("Subfinder", SubfinderTool()),
    ("httpx", HttpxTool()),
    ("WhatWeb", WhatWebTool()),
    ("ffuf", FfufTool()),
]

for name, tool in tools:
    installed = tool.is_installed()
    icon = "✅" if installed else "❌"
    print(f"{icon} {name}: {'Installed' if installed else 'NOT INSTALLED'}")

print()

# Check wordlist
ffuf = FfufTool()
wordlist_path = ffuf._get_wordlist_path('quick')
if wordlist_path and os.path.exists(wordlist_path):
    with open(wordlist_path) as f:
        count = len(f.readlines())
    print(f"✅ Wordlist: {count} entries at {wordlist_path}")
else:
    print(f"❌ Wordlist: NOT FOUND")

print("=" * 70)

