# Boot Orchestrix locally (Windows). API :8000, Web :3000. Keyless.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

Push-Location "$root\apps\api"
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--port","8000"
Pop-Location

Push-Location "$root\apps\web"
if (-not (Test-Path node_modules)) { npm install }
Write-Host "API on http://localhost:8000  ·  Web starting on http://localhost:3000"
npm run dev
Pop-Location
