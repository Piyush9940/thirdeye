<#
======================================================================
  NASA SPACE APPS CHALLENGE 2026: EARTH SYSTEMS TREND DETECTIVE
  Master Local Server Shutdown Script (stop-all.ps1)
======================================================================
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EARTH SYSTEMS TREND DETECTIVE - STOPPING LOCAL SERVICES" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

$pidFile = Join-Path $ScriptDir ".service_pids.json"

if (Test-Path $pidFile) {
    try {
        $pidData = Get-Content $pidFile -Raw | ConvertFrom-Json
        $pids = @($pidData.python_ml_pid, $pidData.node_backend_pid, $pidData.frontend_pid)
        
        foreach ($pidToKill in $pids) {
            if ($pidToKill -and $pidToKill -gt 4) {
                try {
                    $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "  Stopping process: $($proc.ProcessName) (PID $pidToKill)..." -ForegroundColor Yellow
                        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                        Write-Host "  [OK] Stopped PID $pidToKill." -ForegroundColor Green
                    }
                } catch {
                    # Process might already be closed
                }
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  [WARN] Warning parsing PID file: $_" -ForegroundColor Yellow
    }
}

# Also ensure target ports 8000, 5000, 3000 are completely cleared
$targetPorts = @(8000, 5000, 3000)
foreach ($port in $targetPorts) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $p = $conn.OwningProcess
            if ($p -gt 4) {
                Write-Host "  Clearing remaining listener on port $port (PID $p)..." -ForegroundColor Yellow
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Host "`n[OK] All Earth Systems Trend Detective services stopped cleanly.`n" -ForegroundColor Green
