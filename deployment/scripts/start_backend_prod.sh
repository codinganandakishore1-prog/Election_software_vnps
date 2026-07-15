#!/usr/bin/env bash
# Start FastAPI backend (production — no reload)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/backend"
export PYTHONPATH="${ROOT}/shared:${ROOT}/backend${PYTHONPATH:+:${PYTHONPATH}}"
export ENVIRONMENT="${ENVIRONMENT:-production}"
export LOG_TO_FILE="${LOG_TO_FILE:-false}"

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  python3 -m alembic upgrade head
fi

exec python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
