$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host 'YEP local setup - Python 3.12+, Node 22+ and MongoDB Community must be installed.'
if (!(Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python virtual environment.' }
}
& "$Root\.venv\Scripts\python.exe" -m pip install -r "$Root\backend\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
if (!(Test-Path 'backend\.env')) { Copy-Item 'backend\.env.example' 'backend\.env' }
Push-Location frontend
try { npm ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' } } finally { Pop-Location }
Push-Location backend
try {
    & "$Root\.venv\Scripts\python.exe" seed.py
    if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed. Ensure the MongoDB Windows service is running and check backend/.env.' }
} finally { Pop-Location }
Write-Host 'Setup complete. Run .\scripts\start.ps1 and open http://localhost:5173'
