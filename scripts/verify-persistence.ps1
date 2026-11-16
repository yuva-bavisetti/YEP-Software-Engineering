$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (!$env:MONGO_TEST_URL) {
    Push-Location "$Root\backend"
    try {
        $env:MONGO_TEST_URL = & "$Root\.venv\Scripts\python.exe" -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print(os.getenv('MONGO_URL', 'mongodb://127.0.0.1:27017'))"
        if ($LASTEXITCODE -ne 0) { throw 'Could not read local MongoDB configuration.' }
    } finally { Pop-Location }
}
& "$Root\.venv\Scripts\python.exe" -m pytest backend/tests -q
if ($LASTEXITCODE -ne 0) { throw 'MongoDB integration verification failed.' }
