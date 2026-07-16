# Run the Agentic Financial Advisor without Docker, on Windows (PowerShell).
#
# Prerequisites:
#   - PostgreSQL 16+ installed locally, with the pgvector extension available
#     (see README.md "Non-Docker setup" section for install steps)
#   - Python 3.12+
#   - Node.js 20+
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run_local_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "== Setting up backend ==" -ForegroundColor Cyan
Push-Location backend

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from example - edit it with your GROQ_API_KEY and DB settings." -ForegroundColor Yellow
}

Write-Host "Applying database migrations..." -ForegroundColor Cyan
alembic upgrade head

Write-Host "Ingesting sample RAG documents..." -ForegroundColor Cyan
python -m app.rag.ingest

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", ". .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Pop-Location

Write-Host "== Setting up frontend ==" -ForegroundColor Cyan
Push-Location frontend

if (-not (Test-Path "node_modules")) {
    npm install
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

Pop-Location

Write-Host "`nBoth servers are starting in separate windows." -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:5173"
