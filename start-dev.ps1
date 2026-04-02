$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$backendPython = Join-Path $backendDir ".venv\\Scripts\\python.exe"

if (-not (Test-Path $backendPython)) {
  Write-Error "Backend virtual environment not found at $backendPython"
  exit 1
}

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$backendDir'; & '$backendPython' -m uvicorn app.main:app --reload"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$frontendDir'; npm run dev"
)
