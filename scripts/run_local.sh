#!/usr/bin/env bash
# Run the Agentic Financial Advisor without Docker, on Linux/macOS.
#
# Prerequisites:
#   - PostgreSQL 16+ installed locally, with the pgvector extension available
#   - Python 3.12+
#   - Node.js 20+
#
# Usage: ./scripts/run_local.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Setting up backend =="
cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created backend/.env from example - edit it with your GROQ_API_KEY and DB settings."
fi

echo "Applying database migrations..."
alembic upgrade head

echo "Ingesting sample RAG documents..."
python -m app.rag.ingest

echo "Starting backend on http://localhost:8000 ..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  npm install
fi
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

echo "Starting frontend on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend PID:  $BACKEND_PID  (http://localhost:8000/docs)"
echo "Frontend PID: $FRONTEND_PID (http://localhost:5173)"
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
