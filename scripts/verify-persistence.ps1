$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:MONGO_TEST_URL = if ($env:MONGO_URL) { $env:MONGO_URL } else { 'mongodb://127.0.0.1:27017' }
& "$Root\.venv\Scripts\python.exe" -m pytest backend/tests -q
if ($LASTEXITCODE -ne 0) { throw 'MongoDB integration verification failed.' }
