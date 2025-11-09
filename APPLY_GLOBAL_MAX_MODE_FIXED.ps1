# GitHub Copilot Ultimate Max Agent Mode - Global Installer (Fixed)
# Applies settings globally to ALL VS Code workspaces

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$vscodeUserDir = "$env:APPDATA\Code\User"
$settingsPath = Join-Path $vscodeUserDir "settings.json"
$keybindingsPath = Join-Path $vscodeUserDir "keybindings.json"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GITHUB COPILOT MAX AGENT MODE" -ForegroundColor Cyan
Write-Host "  Global Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check VS Code
Write-Host "[1/7] Checking VS Code..." -ForegroundColor Yellow
if (-not (Test-Path $vscodeUserDir)) {
    Write-Host "  ERROR: VS Code not found at $vscodeUserDir" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  OK: VS Code found" -ForegroundColor Green

# Check Copilot extensions
Write-Host ""
Write-Host "[2/7] Checking extensions..." -ForegroundColor Yellow
$extensions = code --list-extensions
if ($extensions -notmatch "GitHub.copilot") {
    Write-Host "  Installing GitHub.copilot..." -ForegroundColor Yellow
    code --install-extension GitHub.copilot --force
}
if ($extensions -notmatch "GitHub.copilot-chat") {
    Write-Host "  Installing GitHub.copilot-chat..." -ForegroundColor Yellow
    code --install-extension GitHub.copilot-chat --force
}
Write-Host "  OK: Extensions ready" -ForegroundColor Green

# Create backup
Write-Host ""
Write-Host "[3/7] Creating backup..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path (Get-Location) "vscode_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

if (Test-Path $settingsPath) {
    Copy-Item $settingsPath (Join-Path $backupDir "settings.json")
}
if (Test-Path $keybindingsPath) {
    Copy-Item $keybindingsPath (Join-Path $keybindingsPath "keybindings.json")
}
Write-Host "  OK: Backup created at $backupDir" -ForegroundColor Green

# Load existing settings
Write-Host ""
Write-Host "[4/7] Loading current settings..." -ForegroundColor Yellow
$currentSettings = @{}
if (Test-Path $settingsPath) {
    $jsonContent = Get-Content $settingsPath -Raw | ConvertFrom-Json
    $jsonContent.PSObject.Properties | ForEach-Object {
        $currentSettings[$_.Name] = $_.Value
    }
}
Write-Host "  OK: Current settings loaded" -ForegroundColor Green

# New Max Agent Mode settings
Write-Host ""
Write-Host "[5/7] Applying Max Agent settings..." -ForegroundColor Yellow
$newSettings = @{
    # Copilot Core
    "github.copilot.enable"                                  = @{
        "*"         = $true
        "plaintext" = $true
        "markdown"  = $true
        "scminput"  = $true
        "yaml"      = $true
    }
    "github.copilot.advanced"                                = @{
        "debug.overrideEngine"       = "gpt-4"
        "debug.overrideProxyUrl"     = ""
        "debug.testOverrideProxyUrl" = ""
        "debug.filterLogCategories"  = @()
        "inlineSuggestCount"         = 10
        "length"                     = 8000
        "temperature"                = ""
        "top_p"                      = ""
        "stops"                      = @{
            "*"      = @("`n`n", "`n`r`n", "`r`n`r`n")
            "python" = @("`ndef ", "class ", "`nif ", "`n@")
        }
        "indentationMode"            = @{
            "*"        = $true
            "python"   = $false
            "markdown" = $true
        }
    }
    
    # Copilot Chat
    "github.copilot.chat.codeGeneration.useInstructionFiles" = $true
    "github.copilot.chat.terminalChatLocation"               = "quickChat"
    "github.copilot.chat.welcomeMessage"                     = "always"
    
    # Editor
    "editor.quickSuggestions"                                = @{
        "other"    = "on"
        "comments" = "on"
        "strings"  = "on"
    }
    "editor.quickSuggestionsDelay"                           = 0
    "editor.suggestOnTriggerCharacters"                      = $true
    "editor.acceptSuggestionOnCommitCharacter"               = $true
    "editor.acceptSuggestionOnEnter"                         = "on"
    "editor.tabCompletion"                                   = "on"
    "editor.inlineSuggest.enabled"                           = $true
    "editor.wordBasedSuggestions"                            = "matchingDocuments"
    "editor.parameterHints.enabled"                          = $true
    "editor.suggest.preview"                                 = $true
    "editor.suggest.showInlineDetails"                       = $true
    "editor.formatOnSave"                                    = $true
    "editor.formatOnPaste"                                   = $true
    "editor.codeActionsOnSave"                               = @{
        "source.fixAll"          = "explicit"
        "source.organizeImports" = "explicit"
    }
    
    # Files
    "files.autoSave"                                         = "afterDelay"
    "files.autoSaveDelay"                                    = 500
    
    # Python
    "python.analysis.typeCheckingMode"                       = "basic"
    "python.analysis.inlayHints.functionReturnTypes"         = $true
    "python.analysis.inlayHints.variableTypes"               = $true
    
    # TypeScript
    "typescript.inlayHints.parameterNames.enabled"           = "all"
    "typescript.inlayHints.functionLikeReturnTypes.enabled"  = $true
    "javascript.inlayHints.parameterNames.enabled"           = "all"
}

# Merge settings
foreach ($key in $newSettings.Keys) {
    $currentSettings[$key] = $newSettings[$key]
}

# Save settings
$currentSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
Write-Host "  OK: Settings applied" -ForegroundColor Green

# Apply keybindings
Write-Host ""
Write-Host "[6/7] Applying keyboard shortcuts..." -ForegroundColor Yellow
$keybindings = @(
    @{
        "key"     = "ctrl+k"
        "command" = "workbench.action.chat.open"
        "when"    = "!inChat"
    },
    @{
        "key"     = "ctrl+i"
        "command" = "editor.action.inlineSuggest.trigger"
        "when"    = "editorTextFocus && !editorReadonly"
    },
    @{
        "key"     = "ctrl+shift+i"
        "command" = "workbench.action.chat.openEditSession"
    },
    @{
        "key"     = "ctrl+alt+t"
        "command" = "workbench.action.terminal.chat.start"
    }
)

$keybindings | ConvertTo-Json -Depth 5 | Set-Content $keybindingsPath -Encoding UTF8
Write-Host "  OK: Keybindings applied" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "[7/7] Installation Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  INSTALLED FEATURES:" -ForegroundColor Cyan
Write-Host "  - 10 inline suggestions (max)" -ForegroundColor White
Write-Host "  - 8000 token context length" -ForegroundColor White
Write-Host "  - Auto-complete everywhere" -ForegroundColor White
Write-Host "  - Composer mode (Ctrl+Shift+I)" -ForegroundColor White
Write-Host "  - Terminal agent (Ctrl+Alt+T)" -ForegroundColor White
Write-Host "  - Auto-save + format" -ForegroundColor White
Write-Host "  - Python/TypeScript hints" -ForegroundColor White
Write-Host ""
Write-Host "  SHORTCUTS:" -ForegroundColor Cyan
Write-Host "  Ctrl+K            Agent Chat" -ForegroundColor White
Write-Host "  Ctrl+I            Inline Edit" -ForegroundColor White
Write-Host "  Ctrl+Shift+I      Composer Mode" -ForegroundColor White
Write-Host "  Ctrl+Alt+T        Terminal Agent" -ForegroundColor White
Write-Host ""

# Restart prompt
$restart = Read-Host "Restart VS Code now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "  Restarting VS Code..." -ForegroundColor Yellow
    Get-Process "Code" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Start-Process "code"
    Write-Host "  Done!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "  Please restart VS Code manually" -ForegroundColor Yellow
}

Write-Host ""
pause
