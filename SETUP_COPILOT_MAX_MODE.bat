@echo off
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║       GITHUB COPILOT MAX AGENT MODE - SETUP VERIFICATION                ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

echo [1/5] Checking VS Code installation...
where code >nul 2>&1
if %errorlevel% equ 0 (
    echo    ✓ VS Code found
) else (
    echo    ✗ VS Code not found in PATH
    echo    └─ Please add VS Code to PATH or install it
    pause
    exit /b 1
)

echo.
echo [2/5] Checking configuration files...
if exist ".vscode\settings.json" (
    echo    ✓ settings.json
) else (
    echo    ✗ settings.json missing
)

if exist ".vscode\keybindings.json" (
    echo    ✓ keybindings.json
) else (
    echo    ✗ keybindings.json missing
)

if exist ".vscode\tasks.json" (
    echo    ✓ tasks.json
) else (
    echo    ✗ tasks.json missing
)

if exist ".vscode\extensions.json" (
    echo    ✓ extensions.json
) else (
    echo    ✗ extensions.json missing
)

if exist ".vscode\launch.json" (
    echo    ✓ launch.json
) else (
    echo    ✗ launch.json missing
)

echo.
echo [3/5] Checking required extensions...
echo    → Checking GitHub Copilot...
code --list-extensions | findstr "GitHub.copilot" >nul 2>&1
if %errorlevel% equ 0 (
    echo       ✓ GitHub Copilot installed
) else (
    echo       ✗ GitHub Copilot NOT installed
    echo       └─ Install: code --install-extension GitHub.copilot
)

code --list-extensions | findstr "GitHub.copilot-chat" >nul 2>&1
if %errorlevel% equ 0 (
    echo       ✓ GitHub Copilot Chat installed
) else (
    echo       ✗ GitHub Copilot Chat NOT installed
    echo       └─ Install: code --install-extension GitHub.copilot-chat
)

echo.
echo [4/5] Configuration Summary...
echo.
echo    📁 Config Location: .vscode\
echo    ├─ settings.json       Core agent settings
echo    ├─ keybindings.json    Cursor-like shortcuts
echo    ├─ tasks.json          Quick commands
echo    ├─ extensions.json     Recommended extensions
echo    └─ launch.json         Debug configs
echo.

echo [5/5] Quick Test Commands...
echo.
echo    💡 TRY THESE IN VS CODE:
echo    ├─ Ctrl + Shift + I    Open Composer Mode (multi-file)
echo    ├─ Ctrl + K            Agent Chat at cursor
echo    ├─ Ctrl + I            Inline quick edit
echo    ├─ F1 → Tasks          Run quick tasks
echo    └─ Ctrl + Shift + P    Command Palette
echo.

echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                        VERIFICATION COMPLETE                             ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo    🚀 NEXT STEPS:
echo    1. Restart VS Code to apply settings
echo    2. Install missing extensions (if any)
echo    3. Open any file and press Ctrl + K to test agent
echo    4. Read: COPILOT_MAX_MODE_SETUP.md for full guide
echo.
echo    📚 DOCUMENTATION:
echo    └─ COPILOT_MAX_MODE_SETUP.md   Complete guide
echo.

set /p launch="Open VS Code in this workspace now? (Y/N): "
if /i "%launch%"=="Y" (
    echo.
    echo    → Launching VS Code...
    code .
    echo    ✓ VS Code opened
) else (
    echo.
    echo    Manual launch: Run "code ." in this directory
)

echo.
pause
