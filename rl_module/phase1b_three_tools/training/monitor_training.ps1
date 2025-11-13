# Phase 1B Training Monitor Script
# Run this to check training progress

Write-Host "=" * 70
Write-Host "PHASE 1B TRAINING MONITOR"
Write-Host "=" * 70

# Check if job is running
$job = Get-Job -Id 1 -ErrorAction SilentlyContinue
if ($job) {
    Write-Host "`n[Job Status]: $($job.State)"
    Write-Host "[Job ID]: $($job.Id)"
    Write-Host "[Has Data]: $($job.HasMoreData)"
    
    if ($job.State -eq "Running") {
        Write-Host "`n[INFO] Training is still running..."
    }
    elseif ($job.State -eq "Completed") {
        Write-Host "`n[SUCCESS] Training completed!"
        Write-Host "`nReceiving job output..."
        Receive-Job -Id 1
    }
    elseif ($job.State -eq "Failed") {
        Write-Host "`n[ERROR] Training failed!"
        Write-Host "`nJob output:"
        Receive-Job -Id 1
    }
}
else {
    Write-Host "`n[WARNING] No training job found (ID 1)"
}

# Check log file
Write-Host "`n" + ("=" * 70)
Write-Host "TRAINING LOG (Last 30 lines)"
Write-Host "=" * 70

$logPath = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training\training_job.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 30 -Encoding UTF8
}
else {
    Write-Host "[WARNING] Log file not found yet"
}

# Check for output directory
Write-Host "`n" + ("=" * 70)
Write-Host "OUTPUT DIRECTORIES"
Write-Host "=" * 70

$outputBase = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\outputs"
if (Test-Path $outputBase) {
    $runs = Get-ChildItem $outputBase -Directory | Sort-Object LastWriteTime -Descending
    if ($runs) {
        Write-Host "`n[Latest Run]: $($runs[0].Name)"
        Write-Host "[Last Modified]: $($runs[0].LastWriteTime)"
        
        # Check for checkpoints
        $checkpointsDir = Join-Path $runs[0].FullName "checkpoints"
        if (Test-Path $checkpointsDir) {
            $checkpoints = Get-ChildItem $checkpointsDir -Filter "*.zip"
            Write-Host "[Checkpoints]: $($checkpoints.Count) found"
            if ($checkpoints) {
                $latest = $checkpoints | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                Write-Host "[Latest Checkpoint]: $($latest.Name)"
            }
        }
        
        # Check TensorBoard
        Write-Host "`n[TensorBoard Command]:"
        Write-Host "tensorboard --logdir=`"$($runs[0].FullName)\tensorboard`""
        Write-Host "Open: http://localhost:6006"
    }
}

Write-Host "`n" + ("=" * 70)
Write-Host "MONITORING COMMANDS"
Write-Host "=" * 70
Write-Host "Get job status:     Get-Job -Id 1"
Write-Host "View log:           Get-Content training_job.log -Tail 50 -Wait"
Write-Host "Stop training:      Stop-Job -Id 1; Remove-Job -Id 1"
Write-Host "=" * 70
