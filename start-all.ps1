<#
======================================================================
  NASA SPACE APPS CHALLENGE 2026: EARTH SYSTEMS TREND DETECTIVE
  Master Local Server Orchestration Script (start-all.ps1)
======================================================================
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EARTH SYSTEMS TREND DETECTIVE - LAUNCHING LOCAL MULTI-SERVICE STACK" -ForegroundColor Cyan
Write-Host "   NASA Space Apps Challenge 2026" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

# --- 1. ENVIRONMENT & PREREQUISITE CHECKS ---
Write-Host "[1/6] Verifying system prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  [OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Python is required but not found in PATH." -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = & node --version 2>&1
    Write-Host "  [OK] Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Node.js is required but not found in PATH." -ForegroundColor Red
    exit 1
}

# Check Checkpoints
$ckpts = Get-ChildItem -Path "$ScriptDir\model-service\models\production_reference\checkpoints\*.pt" -ErrorAction SilentlyContinue
if ($ckpts.Count -eq 15) {
    Write-Host "  [OK] Checkpoints verified: 15/15 PyTorch checkpoints present." -ForegroundColor Green
} else {
    Write-Host "  [WARN] Checkpoint warning: Found $($ckpts.Count) checkpoints (expected 15)." -ForegroundColor Yellow
}

# --- 2. PORT VERIFICATION & RECYCLING ---
Write-Host "`n[2/6] Checking port availability (8000, 5000, 3000)..." -ForegroundColor Yellow

$targetPorts = @(8000, 5000, 3000)

foreach ($port in $targetPorts) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $procId = $conn.OwningProcess
            if ($procId -gt 4) {
                Write-Host "  [WARN] Port $port is in use by PID $procId. Terminating previous instance..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
            }
        }
    }
}
Write-Host "  [OK] Ports 8000, 5000, 3000 ready." -ForegroundColor Green

# --- 3. START PYTHON ML MICROSERVICE (PORT 8000) ---
Write-Host "`n[3/6] Starting Python ML Inference Microservice on port 8000..." -ForegroundColor Yellow

$modelServiceDir = Join-Path $ScriptDir "model-service"
$pyProc = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $modelServiceDir `
    -PassThru `
    -WindowStyle Hidden

Write-Host "  [OK] Python ML Service started with PID $($pyProc.Id)." -ForegroundColor Green

# --- 4. START NODE.JS BACKEND (PORT 5000) ---
Write-Host "`n[4/6] Starting Node.js Express Backend on port 5000..." -ForegroundColor Yellow

$backendDir = Join-Path $ScriptDir "dashboard\backend"
$nodeProc = Start-Process -FilePath "node" `
    -ArgumentList "src/server.js" `
    -WorkingDirectory $backendDir `
    -PassThru `
    -WindowStyle Hidden

Write-Host "  [OK] Node.js Backend started with PID $($nodeProc.Id)." -ForegroundColor Green

# --- 5. START FRONTEND STATIC/DEV SERVER (PORT 3000) ---
Write-Host "`n[5/6] Starting Frontend Development Server on port 3000..." -ForegroundColor Yellow

$frontendDir = Join-Path $ScriptDir "dashboard\frontend"
$frontProc = Start-Process -FilePath "python" `
    -ArgumentList "-m", "http.server", "-d", "`"$frontendDir`"", "3000" `
    -WorkingDirectory $ScriptDir `
    -PassThru `
    -WindowStyle Hidden

Write-Host "  [OK] Frontend Server started with PID $($frontProc.Id)." -ForegroundColor Green

# Save PIDs to .service_pids.json for clean shutdown
$pidData = @{
    python_ml_pid = $pyProc.Id
    node_backend_pid = $nodeProc.Id
    frontend_pid = $frontProc.Id
    started_at = (Get-Date).ToString("o")
}
$pidData | ConvertTo-Json | Out-File -FilePath "$ScriptDir\.service_pids.json" -Encoding utf8

# --- 6. HEALTH PROBING & SERVICE READINESS ---
Write-Host "`n[6/6] Probing live health endpoints..." -ForegroundColor Yellow

function Test-Endpoint {
    param([string]$Url, [int]$MaxRetries=15, [int]$DelaySec=1)
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { return $true }
        } catch {
            Start-Sleep -Seconds $DelaySec
        }
    }
    return $false
}

$mlHealthy = Test-Endpoint "http://127.0.0.1:8000/health"
$nodeHealthy = Test-Endpoint "http://127.0.0.1:5000/api/health"
$frontHealthy = Test-Endpoint "http://127.0.0.1:3000/"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "   ALL LOCAL SERVICES ARE ONLINE AND RUNNING SIMULTANEOUSLY           " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if ($mlHealthy) {
    Write-Host "  [OK] Python ML Microservice:  http://localhost:8000/health (Docs: http://localhost:8000/docs)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Python ML Microservice failed health check." -ForegroundColor Red
}

if ($nodeHealthy) {
    Write-Host "  [OK] Node.js API Backend:     http://localhost:5000/api/health" -ForegroundColor Green
    Write-Host "  [OK] Unified Full-Stack App:  http://localhost:5000" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Node.js API Backend failed health check." -ForegroundColor Red
}

if ($frontHealthy) {
    Write-Host "  [OK] Frontend Dev Server:     http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Frontend Dev Server failed health check." -ForegroundColor Red
}

Write-Host "  [OK] Cloud Public Frontend:   https://earth-systems-trend-detective.netlify.app" -ForegroundColor Cyan
Write-Host "`nTo stop all local services at any time, run: .\stop-all.ps1`n" -ForegroundColor Gray
