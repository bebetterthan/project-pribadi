# Real-time training monitor with progress bar
$logFile = "training_v4_full.log"
$totalTimesteps = 150000
$lastTimesteps = 0
$lastReward = 0
$startTime = Get-Date

# Clear screen and show header
Clear-Host
Write-Host "╔" -NoNewline -ForegroundColor Cyan
Write-Host ("═" * 78) -NoNewline -ForegroundColor Cyan
Write-Host "╗" -ForegroundColor Cyan
Write-Host "║" -NoNewline -ForegroundColor Cyan
Write-Host " PHASE 1B V4 TRAINING - REAL-TIME MONITOR".PadRight(78) -NoNewline -ForegroundColor Yellow
Write-Host "║" -ForegroundColor Cyan
Write-Host "╚" -NoNewline -ForegroundColor Cyan
Write-Host ("═" * 78) -NoNewline -ForegroundColor Cyan
Write-Host "╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔧 CHANGES APPLIED:" -ForegroundColor Green
Write-Host "   • Strategic bonuses amplified 5-10x (+400, +300, +200)" -ForegroundColor White
Write-Host "   • Completion/efficiency bonus ONLY after nmap" -ForegroundColor White
Write-Host "   • +300 bonus for completing all 3 tools" -ForegroundColor White
Write-Host "   • Expected reward differential: 92% (1405 vs 730)" -ForegroundColor White
Write-Host ""
Write-Host "🎯 TARGET PERFORMANCE:" -ForegroundColor Green
Write-Host "   • Infrastructure + service: ~1400-1600 reward" -ForegroundColor White
Write-Host "   • Web-only + quick/skip: ~1100-1300 reward" -ForegroundColor White
Write-Host "   • Agent MUST use nmap to maximize reward!" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (training continues in background)" -ForegroundColor DarkGray
Write-Host ("─" * 80) -ForegroundColor DarkGray
Write-Host ""

# Function to draw progress bar
function Show-ProgressBar {
    param(
        [int]$Current,
        [int]$Total,
        [double]$Reward,
        [string]$Elapsed
    )
    
    $percent = [math]::Round(($Current / $Total) * 100, 1)
    $barLength = 40
    $filled = [math]::Round(($Current / $Total) * $barLength)
    $empty = $barLength - $filled
    
    $bar = "█" * $filled + "░" * $empty
    
    # Save cursor position
    $pos = $Host.UI.RawUI.CursorPosition
    $pos.X = 0
    $Host.UI.RawUI.CursorPosition = $pos
    
    Write-Host "📊 Progress: [" -NoNewline -ForegroundColor Cyan
    Write-Host $bar -NoNewline -ForegroundColor Green
    Write-Host "] " -NoNewline -ForegroundColor Cyan
    Write-Host "$percent%" -NoNewline -ForegroundColor Yellow
    Write-Host " ($Current/$Total steps)" -ForegroundColor White
    
    Write-Host "🏆 Reward:   " -NoNewline -ForegroundColor Cyan
    Write-Host ("{0:N1}" -f $Reward).PadLeft(8) -NoNewline -ForegroundColor Green
    Write-Host " | " -NoNewline -ForegroundColor DarkGray
    Write-Host "⏱️  Time: " -NoNewline -ForegroundColor Cyan
    Write-Host $Elapsed -ForegroundColor Yellow
    Write-Host ("─" * 80) -ForegroundColor DarkGray
}

# Monitor log file
$lineCount = 0
Get-Content $logFile -Tail 0 -Wait | ForEach-Object {
    $line = $_
    $lineCount++
    
    # Extract timesteps
    if ($line -match "total_timesteps\s+\|\s+(\d+)") {
        $lastTimesteps = [int]$matches[1]
        $elapsed = (Get-Date) - $startTime
        $elapsedStr = "{0:hh\:mm\:ss}" -f $elapsed
        
        # Update progress bar
        Show-ProgressBar -Current $lastTimesteps -Total $totalTimesteps -Reward $lastReward -Elapsed $elapsedStr
    }
    
    # Extract reward
    if ($line -match "ep_rew_mean\s+\|\s+([\d.e+-]+)") {
        $lastReward = [double]$matches[1]
    }
    
    # Show important lines below progress bar
    if ($line -match "nmap_usage|nmap_on_infra") {
        Write-Host "   🎯 " -NoNewline -ForegroundColor Cyan
        Write-Host $line.Trim() -ForegroundColor White
    }
    elseif ($line -match "Eval num_timesteps|mean_reward") {
        Write-Host "   📈 " -NoNewline -ForegroundColor Magenta
        Write-Host $line.Trim() -ForegroundColor White
    }
    elseif ($line -match "Training complete|EVALUATION") {
        Write-Host ""
        Write-Host "   ✅ " -NoNewline -ForegroundColor Green
        Write-Host $line.Trim() -ForegroundColor Green
        Write-Host ""
    }
    elseif ($line -match "ERROR|Error|Traceback|FAIL") {
        Write-Host "   ❌ " -NoNewline -ForegroundColor Red
        Write-Host $line.Trim() -ForegroundColor Red
    }
}
