@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║    GITHUB COPILOT ULTIMATE MAX AGENT MODE - GLOBAL INSTALLER            ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
echo    This will install CURSOR-LIKE settings GLOBALLY to VS Code
echo    Settings will apply to ALL workspaces and projects
echo.
echo    📋 What will be installed:
echo    ├─ 10 inline suggestions (max)
echo    ├─ Composer mode (multi-file editing)
echo    ├─ Terminal agent integration
echo    ├─ Auto-complete everywhere
echo    ├─ Auto-save + Auto-format
echo    ├─ Python + TypeScript optimizations
echo    ├─ Cursor-like keyboard shortcuts
echo    └─ Maximum context awareness
echo.
echo    ⚠️  WARNING: This will modify your global VS Code settings!
echo    Your current settings will be backed up automatically.
echo.

set /p confirm="Continue with installation? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo    → Running PowerShell installer...
echo.

REM Run PowerShell script with execution policy bypass
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0APPLY_GLOBAL_MAX_MODE.ps1"

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                     INSTALLATION SCRIPT COMPLETED                        ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.
pause
