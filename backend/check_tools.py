# Test script to verify tool installations
import subprocess
import sys


def check_tool(tool_name, commands):
    """Check if a tool is installed - try multiple paths"""
    # If commands is a list of strings, convert to list of lists
    if isinstance(commands[0], str):
        commands = [commands]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=5,
                shell=False
            )
            if result.returncode == 0:
                print(f"✅ {tool_name} is installed")
                return True
        except FileNotFoundError:
            continue
        except Exception:
            continue

    print(f"❌ {tool_name} is not installed")
    return False


def main():
    print("🔍 Checking pentesting tools installation...\n")

    tools = [
        ("Nmap", [
            ["nmap", "--version"],
            ["C:\\Program Files (x86)\\Nmap\\nmap.exe", "--version"],
            ["C:\\Program Files\\Nmap\\nmap.exe", "--version"]
        ]),
        ("Nuclei", [
            ["nuclei", "-version"],
            ["C:\\PentestTools\\nuclei.exe", "-version"],
            ["D:\\Project pribadi\\AI_Pentesting\\tools\\nuclei.exe", "-version"]
        ]),
        ("WhatWeb", [["whatweb", "--version"]]),
        ("SSLScan", [["sslscan", "--version"]]),
    ]

    results = []
    for tool_name, command in tools:
        results.append(check_tool(tool_name, command))

    print("\n" + "="*50)
    if all(results):
        print("✅ All tools are installed correctly!")
        sys.exit(0)
    else:
        print("❌ Some tools are missing. Please install them before running scans.")
        print("\nRefer to README.md for installation instructions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
