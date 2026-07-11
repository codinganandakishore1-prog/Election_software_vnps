#!/usr/bin/env bash
# Start desktop voting application
set -euo pipefail
cd "$(dirname "$0")/../../desktop"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
python -m app.main
