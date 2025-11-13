# Keep Awake - Simplified version that checks for any python training process

Write-Host "`n[KEEP LAPTOP AWAKE - TRAINING GUARD]`n" -ForegroundColor Cyan

# Configure power
powercfg /change standby-timeout-ac 0 2>$null
powercfg /change hibernate-timeout-ac 0 2>$null
powercfg /change monitor-timeout-ac 30 2>$null

Write-Host "[Power Settings]: Sleep DISABLED, Monitor 30min" -ForegroundColor Green

# Prevent sleep
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class PowerManager {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
}
'@

[PowerManager]::SetThreadExecutionState([PowerManager]::ES_CONTINUOUS -bor [PowerManager]::ES_SYSTEM_REQUIRED)
Write-Host "[System]: Will NOT sleep automatically`n" -ForegroundColor Green

$checkCount = 0
try {
    while ($true) {
        $checkCount++
        Start-Sleep -Seconds 60
        
        # Check ANY python in training dir
        $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            $_.Path -like "*venv*python.exe"
        }
        
        if ($pythonProcesses) {
            $pids = ($pythonProcesses | ForEach-Object { $_.Id }) -join ", "
            Write-Host "[Check $checkCount] Training ACTIVE (PIDs: $pids)" -ForegroundColor Green
            [PowerManager]::SetThreadExecutionState([PowerManager]::ES_CONTINUOUS -bor [PowerManager]::ES_SYSTEM_REQUIRED)
        } else {
            Write-Host "[Check $checkCount] No training detected, stopping..." -ForegroundColor Yellow
            break
        }
    }
} finally {
    [PowerManager]::SetThreadExecutionState([PowerManager]::ES_CONTINUOUS)
    Write-Host "`n[System]: Can sleep again" -ForegroundColor Yellow
}
