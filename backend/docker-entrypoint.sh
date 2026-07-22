#!/bin/sh
set -eu

echo "Starting Election API (environment=${ENVIRONMENT:-development})"

# Ensure writable media / log directories exist (persistent disk or local volume).
UPLOAD_FOLDER="${UPLOAD_FOLDER:-/data/uploads}"
REPORT_FOLDER="${REPORT_FOLDER:-/data/reports}"
BACKUP_FOLDER="${BACKUP_FOLDER:-/data/backups}"
CONFIG_PACKAGE_FOLDER="${CONFIG_PACKAGE_FOLDER:-/data/config_packages}"
LOG_FOLDER="${LOG_FOLDER:-/data/logs}"

mkdir -p \
  "${UPLOAD_FOLDER}" \
  "${REPORT_FOLDER}" \
  "${BACKUP_FOLDER}" \
  "${CONFIG_PACKAGE_FOLDER}" \
  "${LOG_FOLDER}"

# Wait for MySQL when DATABASE_HOST is set (Compose / Render private network).
if [ -n "${DATABASE_HOST:-}" ] && [ "${WAIT_FOR_DB:-true}" = "true" ]; then
  echo "Waiting for database at ${DATABASE_HOST}:${DATABASE_PORT:-3306}..."
  python - <<'PY'
import os, sys, time
import pymysql

host = os.environ.get("DATABASE_HOST", "localhost")
port = int(os.environ.get("DATABASE_PORT", "3306"))
user = os.environ.get("DATABASE_USER", "root")
password = os.environ.get("DATABASE_PASSWORD", "")
database = os.environ.get("DATABASE_NAME", "election_db")
deadline = time.time() + int(os.environ.get("DB_WAIT_SECONDS", "60"))

last_error = None
while time.time() < deadline:
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=3,
        )
        conn.close()
        print("Database is ready", flush=True)
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        time.sleep(2)

print(f"Database not ready: {last_error}", file=sys.stderr)
sys.exit(1)
PY
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec "$@"
