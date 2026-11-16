$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { throw 'Run scripts/setup.ps1 first.' }
$SafePython = $Python.Replace("'", "''")
Start-Process powershell -WorkingDirectory "$Root\backend" -ArgumentList '-NoExit', '-Command', "& '$SafePython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -WorkingDirectory "$Root\frontend" -ArgumentList '-NoExit', '-Command', 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort'
Write-Host 'Open http://localhost:5173. Close the two server windows to stop YEP.'
