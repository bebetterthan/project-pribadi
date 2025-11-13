# Real-time training monitor
$logFile = "training_v4_stdout.log"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "PHASE 1B V4 TRAINING - REAL-TIME MONITOR" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""
Write-Host "[CHANGES]:" -ForegroundColor Green
Write-Host "  1. Strategic bonuses amplified 5-10x (+400, +300, +200)" -ForegroundColor White
Write-Host "  2. Completion/efficiency bonus ONLY after nmap" -ForegroundColor White
Write-Host "  3. +300 bonus for completing all 3 tools" -ForegroundColor White
Write-Host "  4. Expected: 730 reward skip nmap, 1405 reward use nmap (92% diff)" -ForegroundColor White
Write-Host ""
Write-Host "[EXPECTED BEHAVIOR]:" -ForegroundColor Green
Write-Host "  - Agent MUST use nmap to get completion bonus" -ForegroundColor White
Write-Host "  - Infrastructure + service: ~1400-1600 reward" -ForegroundColor White
Write-Host "  - Web-only + quick/skip: ~1100-1300 reward" -ForegroundColor White
Write-Host "  - Skip nmap: ~700-900 reward (much lower!)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (training continues in background)" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Monitor log file
Get-Content $logFile -Tail 30 -Wait | ForEach-Object {
    $line = $_
    
    # Highlight important metrics
    if ($line -match "ep_rew_mean") {
        Write-Host $line -ForegroundColor Green
    }
    elseif ($line -match "nmap_usage|nmap_on_infra") {
        Write-Host $line -ForegroundColor Cyan
    }
    elseif ($line -match "total_timesteps") {
        Write-Host $line -ForegroundColor Yellow
    }
    elseif ($line -match "EVALUATION|Training complete") {
        Write-Host $line -ForegroundColor Magenta
    }
    elseif ($line -match "ERROR|Error|Traceback") {
        Write-Host $line -ForegroundColor Red
    }
    else {
        Write-Host $line
    }
}
