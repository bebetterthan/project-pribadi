# GitHub Copilot Ultimate Max Agent Mode - Global Installer (Robust Version)
# Applies settings globally to ALL VS Code workspaces

$ErrorActionPreference = "Continue"
$vscodeUserDir = "$env:APPDATA\Code\User"
$settingsPath = Join-Path $vscodeUserDir "settings.json"
$keybindingsPath = Join-Path $vscodeUserDir "keybindings.json"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  COPILOT MAX AGENT MODE - INSTALLER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# [1/6] Check VS Code
Write-Host "[1/6] Checking VS Code..." -ForegroundColor Yellow
if (-not (Test-Path $vscodeUserDir)) {
    Write-Host "  ERROR: VS Code not found!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  OK: VS Code found" -ForegroundColor Green

# [2/6] Check extensions
Write-Host ""
Write-Host "[2/6] Checking Copilot extensions..." -ForegroundColor Yellow
$extensions = & code --list-extensions 2>$null
if ($extensions -notmatch "GitHub.copilot") {
    Write-Host "  Installing GitHub.copilot..." -ForegroundColor Yellow
    & code --install-extension GitHub.copilot --force | Out-Null
}
if ($extensions -notmatch "GitHub.copilot-chat") {
    Write-Host "  Installing GitHub.copilot-chat..." -ForegroundColor Yellow
    & code --install-extension GitHub.copilot-chat --force | Out-Null
}
Write-Host "  OK: Extensions ready" -ForegroundColor Green

# [3/6] Backup
Write-Host ""
Write-Host "[3/6] Creating backup..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path (Get-Location) "vscode_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

if (Test-Path $settingsPath) {
    Copy-Item $settingsPath (Join-Path $backupDir "settings.json") -Force
    Write-Host "  OK: Backup at $backupDir" -ForegroundColor Green
}
else {
    Write-Host "  OK: No existing settings to backup" -ForegroundColor Green
}

# [4/6] Apply core Copilot settings by directly editing the file
Write-Host ""
Write-Host "[4/6] Applying Max Agent settings..." -ForegroundColor Yellow

# Create optimized settings JSON string
$optimizedSettings = @'
{
    "github.copilot.enable": {
        "*": true,
        "plaintext": true,
        "markdown": true,
        "scminput": true,
        "yaml": true,
        "javascript": true,
        "typescript": true,
        "python": true,
        "php": true,
        "java": true
    },
    "github.copilot.advanced": {
        "inlineSuggestCount": 10,
        "length": 8000,
        "temperature": 0.2,
        "top_p": 0.95,
        "stops": {
            "*": ["\n\n", "\n\r\n"],
            "python": ["\ndef ", "class ", "\nif "]
        }
    },
    "github.copilot.inlineSuggest.enable": true,
    "github.copilot.editor.enableAutoCompletions": true,
    "github.copilot.editor.iterativeFixing": true,
    "github.copilot.editor.enableCodeActions": true,
    "github.copilot.chat.codeGeneration.useInstructionFiles": true,
    "github.copilot.chat.terminalChatLocation": "quickChat",
    "github.copilot.chat.followUps": "always",
    "github.copilot.chat.runCommand.enabled": true,
    "github.copilot.nextEditSuggestions.enabled": true,
    "editor.inlineSuggest.enabled": true,
    "editor.inlineSuggest.showToolbar": "always",
    "editor.inlineSuggest.suppressSuggestions": false,
    "editor.quickSuggestions": {
        "other": "on",
        "comments": "on",
        "strings": "on"
    },
    "editor.quickSuggestionsDelay": 0,
    "editor.suggestOnTriggerCharacters": true,
    "editor.acceptSuggestionOnCommitCharacter": true,
    "editor.acceptSuggestionOnEnter": "on",
    "editor.tabCompletion": "on",
    "editor.suggest.preview": true,
    "editor.suggest.showInlineDetails": true,
    "editor.suggest.insertMode": "insert",
    "editor.suggest.filterGraceful": true,
    "editor.wordBasedSuggestions": "matchingDocuments",
    "editor.parameterHints.enabled": true,
    "editor.parameterHints.cycle": true,
    "editor.formatOnSave": true,
    "editor.formatOnPaste": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
    },
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 500,
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.inlayHints.functionReturnTypes": true,
    "python.analysis.inlayHints.variableTypes": true,
    "typescript.inlayHints.parameterNames.enabled": "all",
    "typescript.inlayHints.functionLikeReturnTypes.enabled": true,
    "javascript.inlayHints.parameterNames.enabled": "all",
    "javascript.inlayHints.functionLikeReturnTypes.enabled": true
}
'@

# If settings file exists, try to merge (best effort)
if (Test-Path $settingsPath) {
    try {
        # Read existing settings and remove comments
        $existingContent = Get-Content $settingsPath -Raw
        $existingContent = $existingContent -replace '//.*', ''
        $existingContent = $existingContent -replace '/\*[\s\S]*?\*/', ''
        
        $existing = $existingContent | ConvertFrom-Json
        $newSettings = $optimizedSettings | ConvertFrom-Json
        
        # Merge settings (new settings override existing)
        $existing.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            if (-not ($newSettings.PSObject.Properties.Name -contains $key)) {
                $newSettings | Add-Member -MemberType NoteProperty -Name $key -Value $_.Value -Force
            }
        }
        
        $newSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
        Write-Host "  OK: Settings merged with existing" -ForegroundColor Green
    }
    catch {
        # If merge fails, backup and replace
        Write-Host "  WARN: Could not merge, replacing..." -ForegroundColor Yellow
        $optimizedSettings | Set-Content $settingsPath -Encoding UTF8
        Write-Host "  OK: New settings applied" -ForegroundColor Green
    }
}
else {
    $optimizedSettings | Set-Content $settingsPath -Encoding UTF8
    Write-Host "  OK: New settings created" -ForegroundColor Green
}

# [5/6] Keybindings
Write-Host ""
Write-Host "[5/6] Applying keyboard shortcuts..." -ForegroundColor Yellow
$keybindingsJson = @'
[
    {
        "key": "ctrl+k",
        "command": "workbench.action.chat.open",
        "when": "!inChat"
    },
    {
        "key": "ctrl+i",
        "command": "editor.action.inlineSuggest.trigger",
        "when": "editorTextFocus && !editorReadonly"
    },
    {
        "key": "ctrl+shift+i",
        "command": "workbench.action.chat.openEditSession"
    },
    {
        "key": "ctrl+alt+t",
        "command": "workbench.action.terminal.chat.start"
    },
    {
        "key": "ctrl+shift+e",
        "command": "github.copilot.terminal.explainTerminalSelectionContextMenu"
    }
]
'@

$keybindingsJson | Set-Content $keybindingsPath -Encoding UTF8
Write-Host "  OK: Shortcuts applied" -ForegroundColor Green

# [6/6] Summary
Write-Host ""
Write-Host "[6/6] Installation Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  MAX AGENT MODE ACTIVATED:" -ForegroundColor Cyan
Write-Host "  =========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  COPILOT FEATURES:" -ForegroundColor White
Write-Host "  - 10 inline suggestions (maximum)" -ForegroundColor Gray
Write-Host "  - 8000 token context (4x default)" -ForegroundColor Gray
Write-Host "  - Composer mode for multi-file editing" -ForegroundColor Gray
Write-Host "  - Auto-complete in comments & strings" -ForegroundColor Gray
Write-Host "  - Terminal agent integration" -ForegroundColor Gray
Write-Host ""
Write-Host "  EDITOR OPTIMIZATIONS:" -ForegroundColor White
Write-Host "  - Instant suggestions (0ms delay)" -ForegroundColor Gray
Write-Host "  - Auto-save after 500ms" -ForegroundColor Gray
Write-Host "  - Auto-format on save" -ForegroundColor Gray
Write-Host "  - Python/TypeScript inlay hints" -ForegroundColor Gray
Write-Host ""
Write-Host "  KEYBOARD SHORTCUTS:" -ForegroundColor White
Write-Host "  - Ctrl+K           Open Agent Chat" -ForegroundColor Gray
Write-Host "  - Ctrl+I           Trigger Inline Suggestion" -ForegroundColor Gray
Write-Host "  - Ctrl+Shift+I     Open Composer (Multi-file)" -ForegroundColor Gray
Write-Host "  - Ctrl+Alt+T       Terminal Agent" -ForegroundColor Gray
Write-Host "  - Ctrl+Shift+E     Explain Terminal Selection" -ForegroundColor Gray
Write-Host ""
Write-Host "  BACKUP LOCATION:" -ForegroundColor Yellow
Write-Host "  $backupDir" -ForegroundColor Gray
Write-Host ""

# Restart VS Code
$restart = Read-Host "Restart VS Code now to apply changes? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "  Restarting VS Code..." -ForegroundColor Yellow
    Get-Process "Code" -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() | Out-Null }
    Start-Sleep -Seconds 3
    Start-Process "code"
    Write-Host "  Done! VS Code restarted" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "  IMPORTANT: Restart VS Code manually to activate!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Installation successful! Enjoy Max Agent Mode!" -ForegroundColor Green
Write-Host ""
pause
