#!/usr/bin/env bash
# Boot the backend and frontend together. Ctrl+C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ ! -f backend/.env ]; then
  echo "backend/.env not found — copying from .env.example"
  cp backend/.env.example backend/.env
  echo "Edit backend/.env to set OPENAI_API_KEY, then re-run."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating venv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r backend/requirements.txt

if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
fi

cleanup() {
  echo
  echo "Stopping..."
  [ -n "${BACK_PID:-}" ] && kill "$BACK_PID" 2>/dev/null || true
  [ -n "${FRONT_PID:-}" ] && kill "$FRONT_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

PYTHONPATH="$ROOT" uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload &
BACK_PID=$!

(cd frontend && npm run dev) &
FRONT_PID=$!

echo
echo "Backend  → http://localhost:8000"
echo "Frontend → http://localhost:5173"
wait
