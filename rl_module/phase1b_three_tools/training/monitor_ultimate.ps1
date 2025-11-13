# V16 ULTIMATE Training Monitor
# Real-time tracking dengan all key metrics

param(
    [string]$LogFile = "training_20251113_220409.log"
)

$logPath = Join-Path $PSScriptRoot $LogFile

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           V16 ULTIMATE TRAINING MONITOR                       ║" -ForegroundColor Cyan  
Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Target: >4726 reward (30% above baseline)                    ║" -ForegroundColor Yellow
Write-Host "║  Nmap Usage: 50-90% (conditional learning)                    ║" -ForegroundColor Yellow
Write-Host "║  V13 Best: 4321 reward, 65% nmap (BENCHMARK)                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    Clear-Host
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           V16 ULTIMATE TRAINING MONITOR                       ║" -ForegroundColor Cyan  
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path $logPath) {
        # Get latest metrics
        $content = Get-Content $logPath -Raw
        
        # Extract key metrics using regex
        if ($content -match 'total_timesteps\s+\|\s+(\d+)') {
            $timesteps = $matches[1]
            $progress = [math]::Round(($timesteps / 300000) * 100, 1)
            
            Write-Host "📊 PROGRESS: $timesteps / 300,000 ($progress%)" -ForegroundColor Cyan
            
            # Progress bar
            $barLength = 50
            $filled = [math]::Floor($barLength * $progress / 100)
            $bar = "█" * $filled + "░" * ($barLength - $filled)
            Write-Host "[$bar]" -ForegroundColor Green
            Write-Host ""
        }
        
        # Extract rollout metrics
        if ($content -match 'ep_rew_mean\s+\|\s+([\d.e+-]+)') {
            $epRewMean = $matches[1]
            Write-Host "🎯 Rollout Reward Mean: $epRewMean" -ForegroundColor Yellow
            
            # Compare with V13
            $v13Rollout = 3630
            if ($epRewMean -match '([\d.]+)e\+(\d+)') {
                $value = [double]$matches[1] * [math]::Pow(10, [int]$matches[2])
                if ($value -gt $v13Rollout) {
                    Write-Host "   ✅ ABOVE V13 ($v13Rollout)!" -ForegroundColor Green
                }
                else {
                    $diff = $v13Rollout - $value
                    Write-Host "   ⚠️  Below V13 by $([math]::Round($diff, 0))" -ForegroundColor Yellow
                }
            }
        }
        
        # Extract nmap usage
        if ($content -match 'nmap_usage_rate\s+\|\s+([\d.]+)') {
            $nmapRate = [double]$matches[1] * 100
            Write-Host "🔍 Nmap Usage Rate: $([math]::Round($nmapRate, 1))%" -ForegroundColor Magenta
            
            if ($nmapRate -ge 50 -and $nmapRate -le 90) {
                Write-Host "   ✅ IN TARGET RANGE (50-90%)!" -ForegroundColor Green
            }
            elseif ($nmapRate -lt 50) {
                Write-Host "   ⚠️  Below target (need 50-90%)" -ForegroundColor Yellow
            }
            else {
                Write-Host "   ⚠️  Above target (too aggressive)" -ForegroundColor Yellow
            }
        }
        
        # Extract entropy
        if ($content -match 'entropy_loss\s+\|\s+([-\d.]+)') {
            $entropy = $matches[1]
            Write-Host "🎲 Entropy Loss: $entropy" -ForegroundColor Blue
        }
        
        # Extract episode metrics
        if ($content -match 'subdomains_found\s+\|\s+(\d+)') {
            $subdomains = $matches[1]
            Write-Host "📍 Discoveries:" -ForegroundColor White
            Write-Host "   Subdomains: $subdomains" -ForegroundColor Gray
        }
        
        if ($content -match 'endpoints_found\s+\|\s+(\d+)') {
            $endpoints = $matches[1]
            Write-Host "   Endpoints: $endpoints" -ForegroundColor Gray
        }
        
        if ($content -match 'ports_found\s+\|\s+(\d+)') {
            $ports = $matches[1]
            Write-Host "   Ports: $ports" -ForegroundColor Gray
        }
        
        if ($content -match 'services_found\s+\|\s+(\d+)') {
            $services = $matches[1]
            Write-Host "   Services: $services" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor DarkGray
        Write-Host "Last update: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
        
    }
    else {
        Write-Host "⏳ Waiting for log file to be created..." -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds 2
}
