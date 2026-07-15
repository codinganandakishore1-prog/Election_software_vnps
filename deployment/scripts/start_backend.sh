#!/usr/bin/env bash
# Start FastAPI backend (development — auto-reload)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/backend"
export PYTHONPATH="${ROOT}/shared:${ROOT}/backend${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
