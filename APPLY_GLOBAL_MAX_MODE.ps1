# ============================================================================
# APPLY GITHUB COPILOT MAX AGENT MODE - GLOBAL SETTINGS
# This script will backup and update your VS Code global settings
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    GITHUB COPILOT ULTIMATE MAX AGENT MODE - GLOBAL INSTALLER            ║" -ForegroundColor Cyan
Write-Host "║    Apply Cursor-like settings to ALL VS Code workspaces                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Paths
$vscodeUserDir = "$env:APPDATA\Code\User"
$settingsPath = Join-Path $vscodeUserDir "settings.json"
$keybindingsPath = Join-Path $vscodeUserDir "keybindings.json"
$backupDir = Join-Path $PSScriptRoot "vscode_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Check if VS Code is installed
Write-Host "[1/7] Checking VS Code installation..." -ForegroundColor Yellow
if (-not (Test-Path $vscodeUserDir)) {
    Write-Host "   ✗ VS Code user directory not found: $vscodeUserDir" -ForegroundColor Red
    Write-Host "   └─ Please run VS Code at least once to initialize" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "   ✓ VS Code found" -ForegroundColor Green

# Check Copilot extensions
Write-Host ""
Write-Host "[2/7] Checking GitHub Copilot extensions..." -ForegroundColor Yellow
$copilotInstalled = code --list-extensions | Select-String "GitHub.copilot" -Quiet
$copilotChatInstalled = code --list-extensions | Select-String "GitHub.copilot-chat" -Quiet

if (-not $copilotInstalled) {
    Write-Host "   ⚠ GitHub Copilot not installed" -ForegroundColor Yellow
    Write-Host "   └─ Installing..." -ForegroundColor Yellow
    code --install-extension GitHub.copilot --force
}
Write-Host "   ✓ GitHub.copilot" -ForegroundColor Green

if (-not $copilotChatInstalled) {
    Write-Host "   ⚠ GitHub Copilot Chat not installed" -ForegroundColor Yellow
    Write-Host "   └─ Installing..." -ForegroundColor Yellow
    code --install-extension GitHub.copilot-chat --force
}
Write-Host "   ✓ GitHub.copilot-chat" -ForegroundColor Green

# Create backup
Write-Host ""
Write-Host "[3/7] Creating backup..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "   → Backup location: $backupDir" -ForegroundColor Gray

if (Test-Path $settingsPath) {
    Copy-Item $settingsPath "$backupDir\settings.json" -Force
    Write-Host "   ✓ Backed up: settings.json" -ForegroundColor Green
}

if (Test-Path $keybindingsPath) {
    Copy-Item $keybindingsPath "$backupDir\keybindings.json" -Force
    Write-Host "   ✓ Backed up: keybindings.json" -ForegroundColor Green
}

# Read existing settings
Write-Host ""
Write-Host "[4/7] Reading existing settings..." -ForegroundColor Yellow
$existingSettings = @{}
if (Test-Path $settingsPath) {
    try {
        $existingSettings = Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable
        Write-Host "   ✓ Loaded existing settings" -ForegroundColor Green
    }
    catch {
        Write-Host "   ⚠ Could not parse existing settings, will create new" -ForegroundColor Yellow
        $existingSettings = @{}
    }
}
else {
    Write-Host "   → No existing settings found, creating new" -ForegroundColor Gray
}

# Prepare new settings (merging with existing)
Write-Host ""
Write-Host "[5/7] Preparing ULTIMATE MAX AGENT MODE settings..." -ForegroundColor Yellow

# New Copilot settings
$newSettings = @{
    # Copilot Core
    "github.copilot.enable"                                 = @{
        "*"          = $true
        "plaintext"  = $true
        "markdown"   = $true
        "yaml"       = $true
        "json"       = $true
        "jsonc"      = $true
        "python"     = $true
        "javascript" = $true
        "typescript" = $true
        "scminput"   = $false
    }

    # Copilot Chat - ULTRA Agent Mode
    "github.copilot.chat.followUps"                         = "on"
    "github.copilot.chat.localeOverride"                    = "en"
    "github.copilot.chat.runCommand.enabled"                = $true
    "github.copilot.chat.terminalChatLocation"              = "quickChat"
    "github.copilot.chat.useProjectTemplates"               = $true
    "github.copilot.chat.scopeSelection"                    = $true
    "github.copilot.chat.workspaceContext"                  = "auto"

    # Copilot Edits - Composer Mode
    "github.copilot.editor.enableAutoCompletions"           = $true
    "github.copilot.editor.iterativeFixing"                 = $true
    "github.copilot.editor.enableCodeActions"               = $true

    # Copilot Advanced - MAXIMUM Context (Optimized for GPT-4 Turbo)
    "github.copilot.advanced"                               = @{
        "inlineSuggestCount" = 10
        "listCount"          = 20
        "temperature"        = 0
        "top_p"              = 1
        "length"             = 8000
        "debug.showScores"   = $false
    }

    # Copilot Rename
    "github.copilot.renameSuggestions.triggerAutomatically" = $true

    # Editor - Aggressive Auto-Complete
    "editor.inlineSuggest.enabled"                          = $true
    "editor.inlineSuggest.suppressSuggestions"              = $false
    "editor.inlineSuggest.showToolbar"                      = "always"
    "editor.quickSuggestions"                               = @{
        "other"    = "on"
        "comments" = "on"
        "strings"  = "on"
    }
    "editor.suggest.preview"                                = $true
    "editor.suggest.showInlineDetails"                      = $true
    "editor.suggest.snippetsPreventQuickSuggestions"        = $false
    "editor.suggest.localityBonus"                          = $true
    "editor.suggestOnTriggerCharacters"                     = $true
    "editor.acceptSuggestionOnEnter"                        = "on"
    "editor.acceptSuggestionOnCommitCharacter"              = $true
    "editor.tabCompletion"                                  = "on"
    "editor.wordBasedSuggestions"                           = "allDocuments"
    "editor.wordBasedSuggestionsMode"                       = "allDocuments"
    "editor.parameterHints.enabled"                         = $true
    "editor.parameterHints.cycle"                           = $true
    "editor.quickSuggestionsDelay"                          = 0
    "editor.suggest.insertMode"                             = "replace"

    # Auto-save & Auto-format
    "files.autoSave"                                        = "afterDelay"
    "files.autoSaveDelay"                                   = 500
    "editor.formatOnSave"                                   = $true
    "editor.formatOnPaste"                                  = $true
    "editor.formatOnType"                                   = $false
    "editor.codeActionsOnSave"                              = @{
        "source.fixAll"          = "explicit"
        "source.organizeImports" = "explicit"
    }

    # Terminal Integration
    "terminal.integrated.suggest.enabled"                   = $true
    "terminal.integrated.suggest.quickSuggestions"          = $true
    "terminal.integrated.shellIntegration.enabled"          = $true
    "terminal.integrated.shellIntegration.suggestEnabled"   = $true

    # Python
    "python.analysis.typeCheckingMode"                      = "standard"
    "python.analysis.autoImportCompletions"                 = $true
    "python.analysis.completeFunctionParens"                = $true
    "python.analysis.autoFormatStrings"                     = $true
    "python.analysis.autoSearchPaths"                       = $true
    "python.analysis.diagnosticMode"                        = "workspace"
    "python.analysis.indexing"                              = $true
    "python.analysis.inlayHints.functionReturnTypes"        = $true
    "python.analysis.inlayHints.variableTypes"              = $true
    "python.analysis.inlayHints.callArgumentNames"          = "all"

    # TypeScript/JavaScript
    "typescript.suggest.autoImports"                        = $true
    "typescript.suggest.completeFunctionCalls"              = $true
    "typescript.updateImportsOnFileMove.enabled"            = "always"
    "typescript.inlayHints.parameterNames.enabled"          = "all"
    "typescript.inlayHints.functionLikeReturnTypes.enabled" = $true
    "javascript.suggest.autoImports"                        = $true
    "javascript.suggest.completeFunctionCalls"              = $true
    "javascript.updateImportsOnFileMove.enabled"            = "always"
    "javascript.inlayHints.parameterNames.enabled"          = "all"

    # Git
    "git.enableSmartCommit"                                 = $true
    "git.autofetch"                                         = $true
    "git.autoStash"                                         = $true
    "git.confirmSync"                                       = $false

    # Workspace Trust
    "security.workspace.trust.enabled"                      = $true
    "security.workspace.trust.startupPrompt"                = "never"
    "security.workspace.trust.banner"                       = "never"

    # UI
    "editor.minimap.enabled"                                = $false
    "editor.cursorSmoothCaretAnimation"                     = "on"
    "editor.smoothScrolling"                                = $true
    "workbench.editor.enablePreview"                        = $false
    "workbench.list.smoothScrolling"                        = $true
    "workbench.enableExperiments"                           = $true

    # Code Lens & Inlay Hints
    "editor.codeLens"                                       = $true
    "editor.inlayHints.enabled"                             = "on"
    "editor.lightbulb.enabled"                              = "on"

    # Search
    "search.smartCase"                                      = $true
    "search.quickOpen.includeSymbols"                       = $true

    # Breadcrumbs
    "breadcrumbs.enabled"                                   = $true
    "breadcrumbs.filePath"                                  = "on"
    "breadcrumbs.symbolPath"                                = "on"
}

# Merge settings
foreach ($key in $newSettings.Keys) {
    $existingSettings[$key] = $newSettings[$key]
}

Write-Host "   ✓ Settings prepared ($($ newSettings.Count) Copilot settings)" -ForegroundColor Green

# Write settings
Write-Host ""
Write-Host "[6/7] Writing global settings..." -ForegroundColor Yellow
try {
    $existingSettings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "   ✓ Settings written to: $settingsPath" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Failed to write settings: $_" -ForegroundColor Red
    pause
    exit 1
}

# Copy keybindings
Write-Host ""
Write-Host "[7/7] Applying Cursor-like keybindings..." -ForegroundColor Yellow
$localKeybindings = Join-Path $PSScriptRoot ".vscode\keybindings.json"
if (Test-Path $localKeybindings) {
    Copy-Item $localKeybindings $keybindingsPath -Force
    Write-Host "   ✓ Keybindings applied" -ForegroundColor Green
}
else {
    Write-Host "   ⚠ Local keybindings not found, skipping" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  ✓ INSTALLATION COMPLETE!                                ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  📋 WHAT WAS APPLIED:" -ForegroundColor Cyan
Write-Host "  ├─ Global Settings:     $settingsPath" -ForegroundColor Gray
Write-Host "  ├─ Keybindings:         $keybindingsPath" -ForegroundColor Gray
Write-Host "  └─ Backup Location:     $backupDir" -ForegroundColor Gray
Write-Host ""
Write-Host "  🚀 FEATURES ENABLED:" -ForegroundColor Cyan
Write-Host "  ├─ ✓ Copilot Max Agent Mode (10 suggestions)" -ForegroundColor Green
Write-Host "  ├─ ✓ Composer Mode (Ctrl + Shift + I)" -ForegroundColor Green
Write-Host "  ├─ ✓ Terminal Agent (Ctrl + Alt + T)" -ForegroundColor Green
Write-Host "  ├─ ✓ Auto-complete everywhere (comments, strings)" -ForegroundColor Green
Write-Host "  ├─ ✓ Auto-save (500ms delay)" -ForegroundColor Green
Write-Host "  ├─ ✓ Auto-format on save" -ForegroundColor Green
Write-Host "  ├─ ✓ Cursor-like shortcuts" -ForegroundColor Green
Write-Host "  ├─ ✓ Python inlay hints" -ForegroundColor Green
Write-Host "  ├─ ✓ TypeScript inlay hints" -ForegroundColor Green
Write-Host "  └─ ✓ Maximum context awareness" -ForegroundColor Green
Write-Host ""
Write-Host "  ⌨️  KEYBOARD SHORTCUTS:" -ForegroundColor Cyan
Write-Host "  ├─ Ctrl + K              Agent Chat at cursor" -ForegroundColor White
Write-Host "  ├─ Ctrl + L              Agent Sidebar" -ForegroundColor White
Write-Host "  ├─ Ctrl + I              Inline quick edit" -ForegroundColor White
Write-Host "  ├─ Ctrl + Shift + I      Composer (multi-file)" -ForegroundColor White
Write-Host "  ├─ Tab                   Accept suggestion" -ForegroundColor White
Write-Host "  ├─ Ctrl + Y              Force accept" -ForegroundColor White
Write-Host "  └─ Alt + [ / ]           Navigate suggestions" -ForegroundColor White
Write-Host ""
Write-Host "  💡 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Restart VS Code (CTRL + Q then reopen)" -ForegroundColor Yellow
Write-Host "  2. Open any file and press Ctrl + K to test" -ForegroundColor Yellow
Write-Host "  3. Try Ctrl + Shift + I for multi-file composer" -ForegroundColor Yellow
Write-Host "  4. All settings now apply to ALL workspaces!" -ForegroundColor Yellow
Write-Host ""
Write-Host "  📚 DOCUMENTATION:" -ForegroundColor Cyan
Write-Host "  └─ Read: COPILOT_MAX_MODE_SETUP.md for full guide" -ForegroundColor Gray
Write-Host ""
Write-Host "  🔙 ROLLBACK (if needed):" -ForegroundColor Cyan
Write-Host "  └─ Restore from: $backupDir" -ForegroundColor Gray
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  🎉 ENJOY YOUR CURSOR-LIKE MAX AGENT MODE IN VS CODE!                   ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Offer to restart VS Code
$restart = Read-Host "Restart VS Code now to apply changes? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "   → Closing VS Code..." -ForegroundColor Yellow
    Get-Process "Code" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   → Launching VS Code..." -ForegroundColor Yellow
    Start-Process "code" -ArgumentList "."
    Write-Host "   ✓ VS Code restarted" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "   Please restart VS Code manually to apply all changes" -ForegroundColor Yellow
}

Write-Host ""
pause
