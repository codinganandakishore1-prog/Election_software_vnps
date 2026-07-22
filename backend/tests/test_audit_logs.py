"""Audit log service tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.models.audit_log import AuditLog
from app.services.audit_log_service import AuditLogService


def _sample_log(
    *,
    log_id: str = "log-1",
    user_id: str | None = "user-1",
    module: str = "Elections",
    action: str = "Election Published",
) -> AuditLog:
    return AuditLog(
        id=log_id,
        user_id=user_id,
        module=module,
        action=action,
        old_value=None,
        new_value={"election_id": "election-1"},
        ip_address="127.0.0.1",
        browser="pytest",
        created_at=datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc),
    )


def test_list_audit_logs_returns_paginated_response() -> None:
    audit_repo = MagicMock()
    user_repo = MagicMock()
    row = _sample_log()
    audit_repo.search.return_value = ([row], 1)

    user = MagicMock()
    user.full_name = "Admin User"
    user.username = "admin"
    user_repo.get_by_id.return_value = user

    service = AuditLogService(audit_repo, user_repo)
    result = service.list_audit_logs(module="Elections", search="publish", page=1, page_size=25)

    assert result.total == 1
    assert result.page == 1
    assert result.page_size == 25
    assert len(result.items) == 1
    assert result.items[0].user_name == "Admin User"
    assert result.items[0].module == "Elections"
    audit_repo.search.assert_called_once_with(
        module="Elections",
        user_id=None,
        action=None,
        search="publish",
        from_date=None,
        to_date=None,
        offset=0,
        limit=25,
    )


def test_list_audit_logs_uses_system_label_for_missing_user() -> None:
    audit_repo = MagicMock()
    user_repo = MagicMock()
    row = _sample_log(user_id=None, module="Synchronization", action="Vote Upload")
    audit_repo.search.return_value = ([row], 1)

    service = AuditLogService(audit_repo, user_repo)
    result = service.list_audit_logs()

    assert result.items[0].user_id is None
    assert result.items[0].user_name is None
    user_repo.get_by_id.assert_not_called()


def test_list_modules_returns_known_modules() -> None:
    service = AuditLogService(MagicMock(), MagicMock())
    modules = service.list_modules()
    assert "Elections" in modules
    assert "Synchronization" in modules
    assert "Reports" in modules
