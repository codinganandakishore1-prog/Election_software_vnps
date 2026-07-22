"""API router aggregation."""

from fastapi import APIRouter

from app.routers import (
    analytics,
    audit_logs,
    auth,
    candidates,
    configuration,
    elections,
    health,
    houses,
    images,
    nodes,
    notifications,
    positions,
    reports,
    settings,
    sync,
    themes,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(elections.router, prefix="/elections", tags=["Elections"])
api_router.include_router(positions.router, prefix="/positions", tags=["Positions"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
api_router.include_router(images.router, prefix="/images", tags=["Images"])
api_router.include_router(houses.router, prefix="/houses", tags=["Houses"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["Nodes"])
api_router.include_router(sync.router, prefix="/sync", tags=["Synchronization"])
api_router.include_router(configuration.router, prefix="/configuration", tags=["Configuration"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(themes.router, prefix="/themes", tags=["Themes"])
