#!/usr/bin/env bash
# Start NiceGUI website
set -euo pipefail
cd "$(dirname "$0")/../../website"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
python -m app.main
