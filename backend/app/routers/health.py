"""Health check router."""

from election_platform.schemas.response import APIResponse
from election_platform.schemas.websocket import WSChannel
from fastapi import APIRouter
from sqlalchemy import text

from app.config.settings import settings
from app.dependencies.auth import CurrentUser
from app.dependencies.providers import ServiceContainer
from app.schemas.node import NodeHealthResponse
from app.websocket.manager import manager

router = APIRouter()


def _storage_status() -> dict:
    """Check that media directories exist and are writable."""
    folders = {
        "uploads": settings.upload_folder,
        "reports": settings.report_folder,
        "backups": settings.backup_folder,
        "config_packages": settings.config_package_folder,
    }
    details: dict[str, dict] = {}
    writable = True
    for name, path in folders.items():
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        can_write = False
        if is_dir:
            probe = path / ".health_write_test"
            try:
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
                can_write = True
            except OSError:
                can_write = False
                writable = False
        else:
            writable = False
        details[name] = {
            "path": str(path),
            "exists": exists,
            "writable": can_write,
        }
    return {"writable": writable, "folders": details}


@router.get("/health")
async def health_check(container: ServiceContainer) -> APIResponse[dict]:
    """Public health endpoint."""
    database = await database_health(container)
    storage = _storage_status()
    db_connected = bool(database.data and database.data.get("connected"))
    healthy = db_connected and storage["writable"]
    status = "Healthy" if healthy else "Degraded"
    return APIResponse.ok(
        message="Service is healthy" if healthy else "Service degraded",
        data={
            "status": status,
            "database_connected": db_connected,
            "storage_writable": storage["writable"],
        },
    )


@router.get("/health/database")
async def database_health(container: ServiceContainer) -> APIResponse[dict]:
    """Database connectivity check."""
    try:
        container.db.execute(text("SELECT 1"))
        return APIResponse.ok(data={"connected": True})
    except Exception as exc:  # noqa: BLE001
        return APIResponse.ok(data={"connected": False, "error": str(exc)})


@router.get("/health/storage")
async def storage_health() -> APIResponse[dict]:
    """Verify upload/report directories are present and writable."""
    storage = _storage_status()
    return APIResponse.ok(
        message="Storage is healthy" if storage["writable"] else "Storage degraded",
        data=storage,
    )


@router.get("/health/websocket")
async def websocket_health() -> APIResponse[dict]:
    """WebSocket health check."""
    return APIResponse.ok(
        data={
            "connected_clients": manager.connected_count,
            "dashboard_clients": manager.connected_count_for(WSChannel.DASHBOARD),
            "live_clients": manager.connected_count_for(WSChannel.LIVE),
        }
    )


@router.get("/health/node/{node_id}")
async def node_health(
    node_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
) -> APIResponse[NodeHealthResponse]:
    """Return heartbeat metadata and online status for a voting node."""
    _ = current_user
    health = container.node_service.get_node_health(node_id)
    return APIResponse.ok(data=health)
