#!/usr/bin/env bash
# Start NiceGUI website (development)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/website"
export PYTHONPATH="${ROOT}/shared:${ROOT}/website${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m app.main
