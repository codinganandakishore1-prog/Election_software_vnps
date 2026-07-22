#!/usr/bin/env bash
# Start desktop voting application
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}/desktop"
export PYTHONPATH="${ROOT}/shared:${ROOT}/desktop${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m app.main
