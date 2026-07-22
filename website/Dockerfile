# Build from repository root:
#   docker build -f website/Dockerfile -t election-website .
#   docker run --env-file .env -p 8080:8080 election-website

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/shared:/app \
    PORT=8080 \
    WEBSITE_HOST=0.0.0.0 \
    WEBSITE_RELOAD=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home /app --shell /usr/sbin/nologin app

COPY shared/requirements.txt /tmp/shared-requirements.txt
COPY website/requirements.txt /tmp/website-requirements.txt
RUN sed 's|-r ../shared/requirements.txt|-r /tmp/shared-requirements.txt|' \
        /tmp/website-requirements.txt > /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/shared-requirements.txt /tmp/website-requirements.txt /tmp/requirements.txt

COPY shared ./shared
COPY website/app ./app

RUN mkdir -p /app/logs && chown -R app:app /app

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/" || exit 1

CMD ["sh", "-c", "python -m app.main"]
