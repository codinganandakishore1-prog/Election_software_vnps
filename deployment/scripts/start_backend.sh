#!/usr/bin/env bash
# Start FastAPI backend
set -euo pipefail
cd "$(dirname "$0")/../../backend"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
