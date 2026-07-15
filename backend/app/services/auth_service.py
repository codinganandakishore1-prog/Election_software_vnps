"""Authentication service."""

from datetime import datetime, timedelta, timezone
import secrets

from election_platform.enums.admin import LoginStatus, SessionStatus
from jose import JWTError

from app.config.settings import settings
from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import AuthenticationError, ForbiddenError
from app.models.audit_log import AuditLog
from app.models.node import NodeSession
from app.models.session import UserSession
from app.models.user import LoginHistory, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.node_repository import NodeRepository, NodeSessionRepository
from app.repositories.session_repository import UserSessionRepository, hash_token
from app.repositories.user_repository import LoginHistoryRepository, UserRepository
from app.schemas.auth import RefreshResponse, TokenResponse, VerifyResponse
from app.security.jwt import JWTHandler
from app.security.password import PasswordHasher
from app.services.base import BaseService


def _as_utc(value: datetime) -> datetime:
    """Normalize naive/aware datetimes for safe comparison (SQLite may strip tz)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AuthService(BaseService):
    """Handles login, logout, JWT, and node authentication."""

    def __init__(
        self,
        user_repository: UserRepository,
        login_history_repository: LoginHistoryRepository,
        user_session_repository: UserSessionRepository,
        node_repository: NodeRepository,
        node_session_repository: NodeSessionRepository,
        audit_log_repository: AuditLogRepository,
        jwt_handler: JWTHandler | None = None,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.login_history_repository = login_history_repository
        self.user_session_repository = user_session_repository
        self.node_repository = node_repository
        self.node_session_repository = node_session_repository
        self.audit_log_repository = audit_log_repository
        self.jwt_handler = jwt_handler or JWTHandler()
        self.password_hasher = password_hasher or PasswordHasher()

    def login(
        self,
        username: str,
        password: str,
        *,
        ip_address: str | None = None,
        browser: str | None = None,
    ) -> TokenResponse:
        user = self.user_repository.get_by_username(username)
        if user is None or not self.password_hasher.verify_password(password, user.password_hash):
            if user is not None:
                self._record_login_attempt(user.id, LoginStatus.FAILED, ip_address, browser)
                self.user_repository.commit()
            raise AuthenticationError("Invalid username or password")

        if not user.active or user.deleted_at is not None:
            self._record_login_attempt(user.id, LoginStatus.FAILED, ip_address, browser)
            self.user_repository.commit()
            raise ForbiddenError("Account is disabled")

        role_name = user.role.role_name if user.role else ""
        session_expires = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expiry_days)
        session_id = new_uuid()
        refresh_token, _refresh_jti = self.jwt_handler.create_refresh_token(
            user_id=user.id,
            session_id=session_id,
        )

        session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            login_time=utc_now(),
            expires_at=session_expires,
            session_status=SessionStatus.ACTIVE,
            ip_address=ip_address,
            browser=browser,
        )
        self.user_session_repository.add(session)
        self.user_session_repository.flush()

        access_token, access_jti, expires_in = self.jwt_handler.create_access_token(
            user_id=user.id,
            username=user.username,
            role=role_name,
            session_id=session.id,
        )
        session.access_token_jti = access_jti

        self.user_repository.update_last_login(user)
        self._record_login_attempt(user.id, LoginStatus.SUCCESS, ip_address, browser)
        self._audit(user.id, "Login", ip_address=ip_address, browser=browser)
        self.user_repository.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            role=role_name,
            username=user.username,
            full_name=user.full_name,
            user_id=user.id,
            email=user.email,
        )

    def logout(
        self,
        user: User,
        *,
        session_id: str | None = None,
        ip_address: str | None = None,
        browser: str | None = None,
    ) -> None:
        if session_id:
            session = self.user_session_repository.get_by_id(session_id)
            if session is not None and session.user_id == user.id:
                self.user_session_repository.revoke_session(session)
        else:
            self.user_session_repository.revoke_all_for_user(user.id)

        login_record = self.login_history_repository.get_latest_success(user.id)
        if login_record is not None and login_record.logout_time is None:
            login_record.logout_time = utc_now()

        self._audit(user.id, "Logout", ip_address=ip_address, browser=browser)
        self.user_repository.commit()

    def refresh(self, refresh_token: str) -> RefreshResponse:
        payload = self._decode_refresh_token(refresh_token)
        session = self.user_session_repository.get_by_refresh_token_hash(hash_token(refresh_token))
        if session is None:
            raise AuthenticationError("Session expired or revoked")

        if _as_utc(session.expires_at) <= utc_now():
            session.session_status = SessionStatus.EXPIRED
            self.user_session_repository.commit()
            raise AuthenticationError("Session expired")

        user = session.user
        if user is None or not user.active or user.deleted_at is not None:
            raise ForbiddenError("Account is disabled")

        role_name = user.role.role_name if user.role else ""
        access_token, access_jti, expires_in = self.jwt_handler.create_access_token(
            user_id=user.id,
            username=user.username,
            role=role_name,
            session_id=session.id,
        )
        session.access_token_jti = access_jti
        self.user_session_repository.commit()

        return RefreshResponse(access_token=access_token, expires_in=expires_in)

    def verify(self, token: str) -> VerifyResponse:
        payload = self.jwt_handler.decode_token_safe(token)
        if payload is None:
            return VerifyResponse(valid=False)

        try:
            self.jwt_handler.assert_token_type(payload, JWTHandler.TOKEN_TYPE_ACCESS)
        except JWTError:
            return VerifyResponse(valid=False)

        session_id = payload.get("sid")
        if not session_id:
            return VerifyResponse(valid=False)

        session = self.user_session_repository.get_active_session(session_id)
        if session is None:
            return VerifyResponse(valid=False)

        user = session.user
        if user is None or not user.active or user.deleted_at is not None:
            return VerifyResponse(valid=False)

        role_name = user.role.role_name if user.role else payload.get("role")
        return VerifyResponse(
            valid=True,
            expires_in=self.jwt_handler.get_remaining_seconds(payload),
            username=user.username,
            role=role_name,
        )

    def node_login(self, node_id: str, node_secret: str) -> TokenResponse:
        node = self.node_repository.get_by_id(node_id)
        if node is None or not node.active:
            raise AuthenticationError("Invalid node credentials")

        if not self._verify_node_secret(node_secret, node.node_secret):
            raise AuthenticationError("Invalid node credentials")

        session = NodeSession(
            id=new_uuid(),
            node_id=node.id,
            login_time=utc_now(),
            session_status=SessionStatus.ACTIVE,
        )
        self.node_session_repository.add(session)
        self.node_session_repository.flush()

        access_token, jti, expires_in = self.jwt_handler.create_node_token(
            node_id=node.id,
            session_id=session.id,
        )
        session.jwt_token_id = jti
        self.node_session_repository.commit()

        return TokenResponse(access_token=access_token, expires_in=expires_in)

    def validate_access_token(self, token: str) -> User:
        """Validate an access token and return the authenticated user."""
        try:
            payload = self.jwt_handler.decode_token(token)
            self.jwt_handler.assert_token_type(payload, JWTHandler.TOKEN_TYPE_ACCESS)
        except JWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc

        session_id = payload.get("sid")
        user_id = payload.get("sub")
        if not session_id or not user_id:
            raise AuthenticationError("Invalid token payload")

        session = self.user_session_repository.get_active_session(session_id)
        if session is None or session.user_id != user_id:
            raise AuthenticationError("Session expired or revoked")

        user = self.user_repository.get_by_id_with_role(user_id)
        if user is None:
            raise AuthenticationError("User not found")
        if not user.active or user.deleted_at is not None:
            raise ForbiddenError("Account is disabled")

        return user

    def _decode_refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = self.jwt_handler.decode_token(refresh_token)
            self.jwt_handler.assert_token_type(payload, JWTHandler.TOKEN_TYPE_REFRESH)
            return payload
        except JWTError as exc:
            raise AuthenticationError("Invalid or expired refresh token") from exc

    def _verify_node_secret(self, plain_secret: str, stored_secret: str) -> bool:
        if stored_secret.startswith("$2"):
            return self.password_hasher.verify_password(plain_secret, stored_secret)
        return secrets.compare_digest(stored_secret, plain_secret)

    def _record_login_attempt(
        self,
        user_id: str,
        status: LoginStatus,
        ip_address: str | None,
        browser: str | None,
    ) -> None:
        self.login_history_repository.add(
            LoginHistory(
                id=new_uuid(),
                user_id=user_id,
                login_time=utc_now(),
                ip_address=ip_address,
                browser=browser,
                login_status=status,
            )
        )

    def _audit(
        self,
        user_id: str,
        action: str,
        *,
        ip_address: str | None = None,
        browser: str | None = None,
    ) -> None:
        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=user_id,
                module="Authentication",
                action=action,
                ip_address=ip_address,
                browser=browser,
            )
        )
