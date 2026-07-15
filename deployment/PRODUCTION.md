# Production deployment notes
#
# Docker (local production-like):
#   docker compose up --build
#   API health:     http://localhost:8000/health
#   Storage health: http://localhost:8000/health/storage
#   Static theme:   http://localhost:8000/static/default-theme/favicon.png
#   Website:        http://localhost:8080
#
# Render:
#   1. Connect this repo and apply render.yaml (Blueprint).
#   2. When prompted, set CORS_ORIGINS to the public website URL
#      (https://<election-website>.onrender.com).
#   3. Optionally set BACKEND_URL on the website service to the public API URL
#      if you need browser-side calls; server-side uses BACKEND_HOST automatically.
#   4. Keep election-api at 1 instance (WebSocket + rate limits are in-process).
#   5. Uploads/reports persist on the /data disk attached to election-api.
#
# Migrations run automatically on API container start (RUN_MIGRATIONS=true).
