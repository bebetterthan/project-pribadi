# GitHub Copilot Max Mode - Additional Optimizations
# Run after main installation for extra productivity features

$vscodeUserDir = "$env:APPDATA\Code\User"
$snippetsDir = Join-Path $vscodeUserDir "snippets"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ADVANCED OPTIMIZATIONS INSTALLER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create snippets directory
if (-not (Test-Path $snippetsDir)) {
    New-Item -ItemType Directory -Path $snippetsDir -Force | Out-Null
}

# [1/4] Install recommended extensions for max productivity
Write-Host "[1/4] Installing recommended extensions..." -ForegroundColor Yellow
$extensions = @(
    "eamodio.gitlens",                    # Git supercharged
    "ms-python.python",                    # Python IntelliSense
    "ms-python.vscode-pylance",           # Python language server
    "dbaeumer.vscode-eslint",             # JavaScript/TypeScript linting
    "esbenp.prettier-vscode",             # Code formatter
    "visualstudioexptteam.vscodeintellicode",  # AI-assisted IntelliSense
    "usernamehw.errorlens",               # Inline error messages
    "aaron-bond.better-comments",         # Enhanced comment highlighting
    "gruntfuggly.todo-tree",              # TODO/FIXME highlighting
    "streetsidesoftware.code-spell-checker"  # Spell checker
)

foreach ($ext in $extensions) {
    Write-Host "  - Installing $ext..." -ForegroundColor Gray
    & code --install-extension $ext --force 2>&1 | Out-Null
}
Write-Host "  OK: Extensions installed" -ForegroundColor Green

# [2/4] Create productivity snippets
Write-Host ""
Write-Host "[2/4] Creating smart snippets..." -ForegroundColor Yellow

# Python snippets
$pythonSnippets = @'
{
    "Copilot Comment": {
        "prefix": "cop",
        "body": [
            "# Copilot: $0"
        ],
        "description": "Ask Copilot to generate code"
    },
    "Function with Docstring": {
        "prefix": "deff",
        "body": [
            "def ${1:function_name}(${2:params}):",
            "    \"\"\"",
            "    ${3:Description}",
            "    ",
            "    Args:",
            "        ${4:param}: ${5:description}",
            "    ",
            "    Returns:",
            "        ${6:return_type}: ${7:description}",
            "    \"\"\"",
            "    $0"
        ],
        "description": "Function with comprehensive docstring"
    },
    "Class with Docstring": {
        "prefix": "classd",
        "body": [
            "class ${1:ClassName}:",
            "    \"\"\"",
            "    ${2:Class description}",
            "    ",
            "    Attributes:",
            "        ${3:attribute}: ${4:description}",
            "    \"\"\"",
            "    ",
            "    def __init__(self, ${5:params}):",
            "        \"\"\"Initialize ${1:ClassName}\"\"\"",
            "        $0"
        ],
        "description": "Class with docstring"
    },
    "Try-Except Block": {
        "prefix": "tryf",
        "body": [
            "try:",
            "    $1",
            "except ${2:Exception} as e:",
            "    ${3:# Handle error}",
            "    raise",
            "finally:",
            "    ${4:# Cleanup}",
            "    $0"
        ],
        "description": "Try-except-finally block"
    }
}
'@
$pythonSnippets | Set-Content (Join-Path $snippetsDir "python.json") -Encoding UTF8

# TypeScript snippets
$typescriptSnippets = @'
{
    "Copilot Comment": {
        "prefix": "cop",
        "body": [
            "// Copilot: $0"
        ],
        "description": "Ask Copilot to generate code"
    },
    "React Functional Component": {
        "prefix": "rfc",
        "body": [
            "interface ${1:Component}Props {",
            "  $2",
            "}",
            "",
            "export const ${1:Component}: React.FC<${1:Component}Props> = ({ $3 }) => {",
            "  $0",
            "  return (",
            "    <div>",
            "      ${1:Component}",
            "    </div>",
            "  )",
            "}"
        ],
        "description": "React functional component with TypeScript"
    },
    "Async Function": {
        "prefix": "afn",
        "body": [
            "async function ${1:functionName}(${2:params}): Promise<${3:void}> {",
            "  try {",
            "    $0",
            "  } catch (error) {",
            "    console.error('Error in ${1:functionName}:', error)",
            "    throw error",
            "  }",
            "}"
        ],
        "description": "Async function with error handling"
    }
}
'@
$typescriptSnippets | Set-Content (Join-Path $snippetsDir "typescript.json") -Encoding UTF8

Write-Host "  OK: Snippets created" -ForegroundColor Green

# [3/4] Update settings with advanced features
Write-Host ""
Write-Host "[3/4] Applying advanced settings..." -ForegroundColor Yellow

$settingsPath = Join-Path $vscodeUserDir "settings.json"
if (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    
    # Add advanced settings
    $settings | Add-Member -MemberType NoteProperty -Name "workbench.colorTheme" -Value "Default Dark Modern" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "workbench.iconTheme" -Value "vs-seti" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.fontFamily" -Value "Cascadia Code, Consolas, monospace" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.fontLigatures" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.fontSize" -Value 14 -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.lineHeight" -Value 22 -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.bracketPairColorization.enabled" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.guides.bracketPairs" -Value "active" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.stickyScroll.enabled" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.smoothScrolling" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.cursorBlinking" -Value "smooth" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "editor.cursorSmoothCaretAnimation" -Value "on" -Force
    $settings | Add-Member -MemberType NoteProperty -Name "workbench.list.smoothScrolling" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "terminal.integrated.smoothScrolling" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "errorLens.enabled" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "errorLens.delay" -Value 500 -Force
    $settings | Add-Member -MemberType NoteProperty -Name "git.autofetch" -Value $true -Force
    $settings | Add-Member -MemberType NoteProperty -Name "git.confirmSync" -Value $false -Force
    $settings | Add-Member -MemberType NoteProperty -Name "git.enableSmartCommit" -Value $true -Force
    
    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
    Write-Host "  OK: Advanced settings applied" -ForegroundColor Green
}

# [4/4] Create workspace settings template
Write-Host ""
Write-Host "[4/4] Creating workspace template..." -ForegroundColor Yellow

$workspaceTemplate = @'
{
  "folders": [
    {
      "path": "."
    }
  ],
  "settings": {
    "github.copilot.enable": {
      "*": true
    },
    "github.copilot.advanced": {
      "inlineSuggestCount": 10,
      "length": 8000
    },
    "editor.formatOnSave": true,
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 500
  },
  "extensions": {
    "recommendations": [
      "github.copilot",
      "github.copilot-chat",
      "eamodio.gitlens",
      "visualstudioexptteam.vscodeintellicode",
      "usernamehw.errorlens"
    ]
  }
}
'@

$workspaceTemplate | Set-Content "copilot-workspace-template.code-workspace" -Encoding UTF8
Write-Host "  OK: Workspace template created" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ADVANCED OPTIMIZATIONS COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  INSTALLED:" -ForegroundColor White
Write-Host "  - 10 productivity extensions" -ForegroundColor Gray
Write-Host "  - Smart code snippets (Python, TypeScript)" -ForegroundColor Gray
Write-Host "  - Enhanced UI settings (smooth animations)" -ForegroundColor Gray
Write-Host "  - Bracket colorization & sticky scroll" -ForegroundColor Gray
Write-Host "  - Git auto-fetch & smart commit" -ForegroundColor Gray
Write-Host "  - Error lens (inline diagnostics)" -ForegroundColor Gray
Write-Host "  - Workspace template file" -ForegroundColor Gray
Write-Host ""
Write-Host "  NEW SNIPPETS:" -ForegroundColor White
Write-Host "  - 'cop'    -> Copilot comment prompt" -ForegroundColor Gray
Write-Host "  - 'deff'   -> Python function with docstring" -ForegroundColor Gray
Write-Host "  - 'classd' -> Python class with docstring" -ForegroundColor Gray
Write-Host "  - 'rfc'    -> React functional component" -ForegroundColor Gray
Write-Host "  - 'afn'    -> Async function with error handling" -ForegroundColor Gray
Write-Host ""
Write-Host "  Restart VS Code to activate all features!" -ForegroundColor Yellow
Write-Host ""
pause
