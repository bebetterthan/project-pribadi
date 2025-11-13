# Phase 1B Training Monitor - Live Progress
# Check process and show latest metrics

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "PHASE 1B TRAINING MONITOR - LIVE" -ForegroundColor Cyan  
Write-Host "======================================================================`n" -ForegroundColor Cyan

# Check if python process is running
$process = Get-Process -Id 10412 -ErrorAction SilentlyContinue

if ($process) {
    Write-Host "[Process Status]: RUNNING" -ForegroundColor Green
    Write-Host "[PID]: $($process.Id)"
    Write-Host "[CPU Time]: $($process.CPU) seconds"
    Write-Host "[Memory]: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB"
    Write-Host "[Start Time]: $($process.StartTime)"
    $elapsed = (Get-Date) - $process.StartTime
    Write-Host "[Elapsed]: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s"
}
else {
    Write-Host "[Process Status]: NOT RUNNING or COMPLETED" -ForegroundColor Yellow
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "LATEST TRAINING METRICS (stdout - last 50 lines)" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$stdout_file = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training\training_stdout.log"
if (Test-Path $stdout_file) {
    Get-Content $stdout_file | Select-Object -Last 50
}
else {
    Write-Host "[WARNING] stdout log not found" -ForegroundColor Yellow
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "ERRORS (stderr - last 20 lines)" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$stderr_file = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training\training_stderr.log"
if (Test-Path $stderr_file) {
    $errors = Get-Content $stderr_file | Select-Object -Last 20
    if ($errors.Length -eq 0) {
        Write-Host "[No errors]" -ForegroundColor Green
    }
    else {
        Write-Host $errors -ForegroundColor Red
    }
}
else {
    Write-Host "[WARNING] stderr log not found" -ForegroundColor Yellow
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "CHECKPOINTS" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$output_dir = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\outputs"
$latest_run = Get-ChildItem -Path $output_dir -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latest_run) {
    Write-Host "[Latest Run]: $($latest_run.Name)"
    Write-Host "[Last Modified]: $($latest_run.LastWriteTime)"
    
    $checkpoint_dir = Join-Path $latest_run.FullName "checkpoints"
    if (Test-Path $checkpoint_dir) {
        $checkpoints = Get-ChildItem -Path $checkpoint_dir -Filter "*.zip"
        Write-Host "[Checkpoints]: $($checkpoints.Count) found"
        if ($checkpoints.Count -gt 0) {
            foreach ($cp in $checkpoints) {
                Write-Host "   - $($cp.Name) ($([math]::Round($cp.Length / 1MB, 2)) MB)"
            }
        }
    }
    else {
        Write-Host "[Checkpoints]: Directory not found" -ForegroundColor Yellow
    }
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "TENSORBOARD" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

if ($latest_run) {
    $tensorboard_dir = Join-Path $latest_run.FullName "tensorboard"
    Write-Host "[Command]: tensorboard --logdir=`"$tensorboard_dir`""
    Write-Host "[URL]: http://localhost:6006"
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "MONITORING COMMANDS" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

Write-Host "Refresh this monitor:"
Write-Host "  .\monitor_live_training.ps1`n"

Write-Host "Watch logs in real-time:"
Write-Host "  Get-Content training_stdout.log -Wait -Tail 20`n"

Write-Host "Kill training (if needed):"
Write-Host "  Stop-Process -Id 10412`n"
