# Keep Laptop Awake During Training
# Prevents sleep/hibernate while training is running

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "KEEP LAPTOP AWAKE - TRAINING GUARD" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

# Check battery first
$battery = Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue
if ($battery) {
    Write-Host "[Battery Check]:" -ForegroundColor Yellow
    Write-Host "   Charge: $($battery.EstimatedChargeRemaining)%"
    Write-Host "   Status: $(switch ($battery.BatteryStatus) { 1 {'Discharging'} 2 {'AC Power'} 3 {'Fully Charged'} })"
    
    if ($battery.BatteryStatus -eq 1 -and $battery.EstimatedChargeRemaining -lt 50) {
        Write-Host "`n   [CRITICAL WARNING]: Battery below 50% and discharging!" -ForegroundColor Red
        Write-Host "   Please connect charger NOW or training will stop!`n" -ForegroundColor Red
        
        $response = Read-Host "Continue anyway? (Y/N)"
        if ($response -ne 'Y' -and $response -ne 'y') {
            exit
        }
    }
}

Write-Host "`n[Configuring power settings]..." -ForegroundColor Cyan

# Disable sleep and hibernate when plugged in
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0

# Keep monitor on longer (30 minutes)
powercfg /change monitor-timeout-ac 30

Write-Host "[OK] Power settings configured:" -ForegroundColor Green
Write-Host "   - Sleep: DISABLED (when plugged in)"
Write-Host "   - Hibernate: DISABLED (when plugged in)"
Write-Host "   - Disk timeout: DISABLED"
Write-Host "   - Monitor: 30 minutes`n"

# Use PowerShell to keep system awake
Write-Host "[Starting keep-awake loop]..." -ForegroundColor Cyan
Write-Host "This will prevent sleep while training runs" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop (only stop after training completes!)`n" -ForegroundColor Yellow

# Import required type for preventing sleep
Add-Type @'
using System;
using System.Runtime.InteropServices;

public class PowerManager {
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
    
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;
    
    public static void PreventSleep() {
        SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED);
    }
    
    public static void AllowSleep() {
        SetThreadExecutionState(ES_CONTINUOUS);
    }
}
'@

# Prevent sleep
[PowerManager]::PreventSleep()
Write-Host "[ACTIVE] System will not sleep automatically" -ForegroundColor Green

$checkCount = 0
try {
    while ($true) {
        $checkCount++
        
        # Check if training is still running every 60 seconds
        Start-Sleep -Seconds 60
        
        $trainingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*train_phase1b*"
        }
        
        if ($trainingProcess) {
            Write-Host "[Check $checkCount] Training RUNNING (PID: $($trainingProcess.Id)) - Keeping awake..." -ForegroundColor Green
            
            # Refresh prevent sleep
            [PowerManager]::PreventSleep()
            
            # Battery check
            if ($battery) {
                $battery = Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue
                if ($battery.BatteryStatus -eq 1 -and $battery.EstimatedChargeRemaining -lt 20) {
                    Write-Host "   [WARNING] Battery at $($battery.EstimatedChargeRemaining)%!" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "[Check $checkCount] Training NOT RUNNING - Stopping keep-awake..." -ForegroundColor Yellow
            break
        }
    }
} finally {
    # Re-allow sleep when done
    [PowerManager]::AllowSleep()
    Write-Host "`n[STOPPED] System can sleep again" -ForegroundColor Yellow
}
