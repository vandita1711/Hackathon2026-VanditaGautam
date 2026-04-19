$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot "..\venv\Scripts\python.exe"
$pythonExe = [System.IO.Path]::GetFullPath($pythonExe)
$uiApp = Join-Path $projectRoot "ui_app.py"

if (-not (Test-Path $pythonExe)) {
throw "Virtual environment Python not found at $pythonExe"
}

$existing = Get-NetTCPConnection -LocalPort 7860 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
Write-Host "Stopping existing process on port 7860 (PID $($existing.OwningProcess))..."
Stop-Process -Id $existing.OwningProcess -Force
Start-Sleep -Seconds 2
}

Write-Host "Starting ShopWave UI with $pythonExe"
Write-Host "Keep this PowerShell window open while using the UI."
Write-Host "Open http://127.0.0.1:7860"

Set-Location $projectRoot
& $pythonExe $uiApp

