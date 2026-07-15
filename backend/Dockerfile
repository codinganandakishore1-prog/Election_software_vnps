# Build from repository root:
#   docker build -f backend/Dockerfile -t election-backend .
#   docker run --env-file .env -p 8000:8000 election-backend

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/shared:/app \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home /app --shell /usr/sbin/nologin app

# Shared requirements first so backend's `-r ../shared/requirements.txt` resolves in the image.
COPY shared/requirements.txt /tmp/shared-requirements.txt
COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN sed 's|-r ../shared/requirements.txt|-r /tmp/shared-requirements.txt|' \
        /tmp/backend-requirements.txt > /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/shared-requirements.txt /tmp/backend-requirements.txt /tmp/requirements.txt

COPY shared ./shared
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh \
    && mkdir -p /data/uploads /data/reports /data/backups /data/config_packages /data/logs \
    && chown -R app:app /app /data

USER app

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
