# Live training monitor with real-time progress bar
param(
    [string]$LogFile = ""
)

# Find log file if not specified
if ($LogFile -eq "" -or !(Test-Path $LogFile)) {
    $LogFile = Get-ChildItem -Filter "training_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object -ExpandProperty FullName
    if (!$LogFile) {
        Write-Host "❌ No log file found!" -ForegroundColor Red
        Write-Host "Usage: .\monitor_live.ps1 [logfile.log]" -ForegroundColor Yellow
        exit 1
    }
}

$totalSteps = 150000
$startTime = Get-Date
$lastSteps = 0
$lastReward = "0"

# Clear screen and show header
Clear-Host
Write-Host "╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           PHASE 1B V4 TRAINING - LIVE MONITOR (150,000 timesteps)             ║" -ForegroundColor Yellow
Write-Host "╠════════════════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ Log file: $($LogFile.PadRight(68))║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (training continues)" -ForegroundColor DarkGray
Write-Host "────────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$progressLine = [Console]::CursorTop

# Monitor log file
try {
    Get-Content $LogFile -Tail 0 -Wait | ForEach-Object {
        $line = $_
        
        # Extract timesteps
        if ($line -match "total_timesteps\s+\|\s+(\d+)") {
            $steps = [int]$matches[1]
            if ($steps -ne $lastSteps) {
                $lastSteps = $steps
                $percent = [math]::Round(($steps / $totalSteps) * 100, 1)
                $filled = [math]::Floor($percent / 2.5)
                $bar = "█" * $filled + "░" * (40 - $filled)
                
                $elapsed = (Get-Date) - $startTime
                $stepsPerSec = if ($elapsed.TotalSeconds -gt 0) { $steps / $elapsed.TotalSeconds } else { 0 }
                $etaSec = if ($stepsPerSec -gt 0) { ($totalSteps - $steps) / $stepsPerSec } else { 0 }
                $eta = [TimeSpan]::FromSeconds($etaSec)
                
                # Update progress display
                [Console]::SetCursorPosition(0, $progressLine)
                Write-Host "📊 Progress: [$bar] $percent%                    " -ForegroundColor Green
                Write-Host "🔢 Steps: $steps / $totalSteps | Speed: $([math]::Round($stepsPerSec, 0)) steps/s           " -ForegroundColor Cyan
                Write-Host "🏆 Reward: $lastReward                                   " -ForegroundColor Yellow
                Write-Host "⏱️  Elapsed: $($elapsed.ToString('hh\:mm\:ss')) | ETA: $($eta.ToString('hh\:mm\:ss'))                    " -ForegroundColor White
                Write-Host "────────────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
            }
        }
        
        # Extract reward
        if ($line -match "ep_rew_mean\s+\|\s+([\d.e+-]+)") {
            $lastReward = "{0:N0}" -f [double]$matches[1]
        }
        
        # Show important events
        if ($line -match "Eval num_timesteps") {
            Write-Host ""
            Write-Host "   📈 Evaluation checkpoint" -ForegroundColor Magenta
        }
        elseif ($line -match "Training complete|FINAL EVALUATION") {
            Write-Host ""
            Write-Host "   ✅ $line" -ForegroundColor Green
            Write-Host ""
            break
        }
        elseif ($line -match "ERROR|FAIL") {
            Write-Host ""
            Write-Host "   ❌ $line" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host ""
    Write-Host "⚠️  Monitoring stopped: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Monitoring ended" -ForegroundColor Green
