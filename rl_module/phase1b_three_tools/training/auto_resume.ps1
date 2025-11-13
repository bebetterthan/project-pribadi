# Auto-Resume Training Script
# Checks if training is running, if not, resumes from latest checkpoint

param(
    [switch]$Monitor = $false,
    [int]$CheckIntervalSeconds = 300  # Check every 5 minutes
)

$trainingDir = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\training"
$pythonExe = "d:\Project pribadi\AI_Pentesting\backend\venv\Scripts\python.exe"

function Get-TrainingProcess {
    # Check if training process is running
    $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*train_phase1b*"
    }
    return $processes
}

function Get-LatestCheckpoint {
    $outputsDir = "d:\Project pribadi\AI_Pentesting\rl_module\phase1b_three_tools\outputs"
    $latestRun = Get-ChildItem -Path $outputsDir -Directory | 
                 Sort-Object LastWriteTime -Descending | 
                 Select-Object -First 1
    
    if (-not $latestRun) {
        return $null
    }
    
    $checkpointDir = Join-Path $latestRun.FullName "checkpoints"
    if (-not (Test-Path $checkpointDir)) {
        return $null
    }
    
    $checkpoints = Get-ChildItem -Path $checkpointDir -Filter "rl_model_*_steps.zip" |
                   Sort-Object { [int]($_.BaseName -split '_')[2] } -Descending |
                   Select-Object -First 1
    
    if ($checkpoints) {
        $steps = [int](($checkpoints.BaseName -split '_')[2])
        return @{
            Path = $checkpoints.FullName
            Steps = $steps
            Remaining = 150000 - $steps
        }
    }
    
    return $null
}

function Start-Training {
    param([bool]$IsResume = $false)
    
    Set-Location $trainingDir
    
    if ($IsResume) {
        Write-Host "`n[RESUMING TRAINING FROM CHECKPOINT]" -ForegroundColor Yellow
        $script = "resume_training.py"
    } else {
        Write-Host "`n[STARTING NEW TRAINING]" -ForegroundColor Green
        $script = "train_phase1b_local.py"
    }
    
    # Start as separate process
    $process = Start-Process -FilePath $pythonExe `
                             -ArgumentList "-u", $script `
                             -WorkingDirectory $trainingDir `
                             -RedirectStandardOutput "training_stdout.log" `
                             -RedirectStandardError "training_stderr.log" `
                             -NoNewWindow `
                             -PassThru
    
    Write-Host "[Process Started]: PID $($process.Id)" -ForegroundColor Green
    return $process
}

function Show-Status {
    Write-Host "`n======================================================================" -ForegroundColor Cyan
    Write-Host "PHASE 1B TRAINING AUTO-RESUME STATUS" -ForegroundColor Cyan
    Write-Host "======================================================================`n" -ForegroundColor Cyan
    
    $runningProcess = Get-TrainingProcess
    
    if ($runningProcess) {
        Write-Host "[Training Status]: RUNNING" -ForegroundColor Green
        Write-Host "[PID]: $($runningProcess.Id)"
        Write-Host "[CPU Time]: $($runningProcess.CPU) seconds"
        Write-Host "[Memory]: $([math]::Round($runningProcess.WorkingSet64 / 1MB, 2)) MB"
        
        if ($runningProcess.StartTime) {
            $elapsed = (Get-Date) - $runningProcess.StartTime
            Write-Host "[Running Time]: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s"
        }
    } else {
        Write-Host "[Training Status]: NOT RUNNING" -ForegroundColor Yellow
        
        $checkpoint = Get-LatestCheckpoint
        if ($checkpoint) {
            Write-Host "`n[Latest Checkpoint Found]:" -ForegroundColor Cyan
            Write-Host "   Steps Completed: $($checkpoint.Steps:N0)"
            Write-Host "   Steps Remaining: $($checkpoint.Remaining:N0)"
            Write-Host "   Progress: $([math]::Round($checkpoint.Steps / 150000 * 100, 1))%"
            Write-Host "`n[Action]: Can resume training" -ForegroundColor Yellow
        } else {
            Write-Host "`n[No checkpoints found]: Will start new training" -ForegroundColor Yellow
        }
    }
    
    # Battery status
    $battery = Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue
    if ($battery) {
        Write-Host "`n[Battery Status]:" -ForegroundColor Cyan
        $status = switch ($battery.BatteryStatus) {
            1 { "Discharging" }
            2 { "AC Power" }
            3 { "Fully Charged" }
            default { "Unknown" }
        }
        Write-Host "   Status: $status"
        Write-Host "   Charge: $($battery.EstimatedChargeRemaining)%"
        
        if ($battery.BatteryStatus -eq 1) {
            Write-Host "   [WARNING]: Running on battery! Please connect charger!" -ForegroundColor Red
        }
    }
    
    Write-Host "`n======================================================================"
}

# Main logic
if ($Monitor) {
    Write-Host "Starting monitoring mode (checking every $CheckIntervalSeconds seconds)..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop monitoring`n"
    
    while ($true) {
        Show-Status
        
        $runningProcess = Get-TrainingProcess
        if (-not $runningProcess) {
            Write-Host "`n[Training not running, attempting auto-resume]..." -ForegroundColor Yellow
            
            $checkpoint = Get-LatestCheckpoint
            $isResume = $checkpoint -ne $null -and $checkpoint.Steps -lt 150000
            
            Start-Training -IsResume $isResume
        }
        
        Write-Host "`nNext check in $CheckIntervalSeconds seconds..."
        Start-Sleep -Seconds $CheckIntervalSeconds
    }
} else {
    # Single check and resume if needed
    Show-Status
    
    $runningProcess = Get-TrainingProcess
    if (-not $runningProcess) {
        Write-Host "`nTraining is not running. Resume? (Y/N): " -ForegroundColor Yellow -NoNewline
        $response = Read-Host
        
        if ($response -eq 'Y' -or $response -eq 'y') {
            $checkpoint = Get-LatestCheckpoint
            $isResume = $checkpoint -ne $null -and $checkpoint.Steps -lt 150000
            Start-Training -IsResume $isResume
        }
    }
}
