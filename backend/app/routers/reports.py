"""Report generation router."""

from datetime import datetime

from election_platform.enums.admin import NotificationType, ReportType
from election_platform.enums.roles import UserRole
from election_platform.schemas.response import APIResponse
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse

from app.dependencies.auth import CurrentUser, require_roles
from app.dependencies.providers import ServiceContainer
from app.schemas.report import ReportGenerateRequest, ReportResponse

router = APIRouter()

AdminUser = Depends(require_roles(UserRole.SUPER_ADMINISTRATOR, UserRole.ADMINISTRATOR))
ViewerUser = Depends(
    require_roles(
        UserRole.SUPER_ADMINISTRATOR,
        UserRole.ADMINISTRATOR,
        UserRole.VIEWER,
    )
)


@router.get("")
async def list_reports(
    current_user: CurrentUser,
    container: ServiceContainer,
    election_id: str | None = Query(default=None),
    report_type: ReportType | None = Query(default=None),
    generated_after: datetime | None = Query(default=None),
    generated_before: datetime | None = Query(default=None),
    _: None = ViewerUser,
) -> APIResponse[list[ReportResponse]]:
    """List generated reports."""
    _ = current_user
    reports = container.report_service.list_reports(
        election_id=election_id,
        report_type=report_type,
    )
    if generated_after is not None or generated_before is not None:
        reports = [
            report
            for report in reports
            if (generated_after is None or report.generated_at >= generated_after)
            and (generated_before is None or report.generated_at <= generated_before)
        ]
    return APIResponse.ok(data=reports)


@router.post("/generate")
async def generate_report(
    payload: ReportGenerateRequest,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[ReportResponse]:
    """Generate a new report."""
    generated_by_name = current_user.full_name or current_user.username
    report = container.report_service.generate_report(
        payload.election_id,
        payload.format,
        user_id=current_user.id,
        generated_by_name=generated_by_name,
    )
    return APIResponse.ok(message="Report generated successfully", data=report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    request: Request,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = ViewerUser,
) -> FileResponse:
    """Download a generated report file."""
    file_path, media_type, filename = container.report_service.get_download_path(report_id)
    client_host = request.client.host if request.client else None
    container.report_service.record_download(
        report_id,
        user_id=current_user.id,
        ip_address=client_host,
    )
    report = container.report_service.get_report(report_id)
    downloader = current_user.full_name or current_user.username
    await container.notification_service.create_and_broadcast(
        title="Report downloaded",
        message=f'"{report.report_name}" downloaded by {downloader}.',
        notification_type=NotificationType.REPORT_DOWNLOADED.value,
    )
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: CurrentUser,
    container: ServiceContainer,
    _: None = AdminUser,
) -> APIResponse[None]:
    """Soft-delete a generated report and remove its file."""
    container.report_service.delete_report(report_id, user_id=current_user.id)
    return APIResponse.ok(message="Report deleted successfully")
