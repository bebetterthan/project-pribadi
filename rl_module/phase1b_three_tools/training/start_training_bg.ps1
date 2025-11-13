# Start training as detached background process
Write-Host "╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              🚀 STARTING PHASE 1B V4 TRAINING (BACKGROUND MODE)               ║" -ForegroundColor Yellow
Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ ✅ Training will run in background - safe to close this window                ║" -ForegroundColor Green
Write-Host "║ ✅ Monitor progress with: .\monitor_live.ps1                                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Kill any existing training processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*train_phase1b*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Start training as background process with Start-Process (detached)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "training_$timestamp.log"

Write-Host "📝 Log file: $logFile" -ForegroundColor Cyan
Write-Host "🔄 Starting training process..." -ForegroundColor Yellow

$process = Start-Process -FilePath "d:\Project pribadi\AI_Pentesting\backend\venv\Scripts\python.exe" `
    -ArgumentList "train_phase1b_local.py" `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError "training_$timestamp`_error.log" `
    -WindowStyle Hidden `
    -PassThru

Write-Host ""
Write-Host "✅ Training started!" -ForegroundColor Green
Write-Host "   Process ID: $($process.Id)" -ForegroundColor White
Write-Host "   Log file: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "📊 To monitor progress, run:" -ForegroundColor Cyan
Write-Host "   .\monitor_live.ps1 $logFile" -ForegroundColor White
Write-Host ""
Write-Host "⏹️  To stop training:" -ForegroundColor Yellow
Write-Host "   Stop-Process -Id $($process.Id)" -ForegroundColor White
Write-Host ""

# Save PID for later
$process.Id | Out-File "training.pid" -Force

Write-Host "💾 Process ID saved to training.pid" -ForegroundColor Green
Write-Host ""
