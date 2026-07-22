"""User session repository."""

import hashlib

from election_platform.enums.admin import SessionStatus
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.base import utc_now
from app.models.session import UserSession
from app.models.user import User
from app.repositories.base import BaseRepository


def hash_token(token: str) -> str:
    """Return SHA-256 hex digest of a token."""
    return hashlib.sha256(token.encode()).hexdigest()


class UserSessionRepository(BaseRepository[UserSession]):
    """Data access for user authentication sessions."""

    model = UserSession

    def get_active_session(self, session_id: str) -> UserSession | None:
        stmt = (
            select(UserSession)
            .options(joinedload(UserSession.user).joinedload(User.role))
            .where(
                UserSession.id == session_id,
                UserSession.session_status == SessionStatus.ACTIVE,
                UserSession.expires_at > utc_now(),
            )
        )
        return self.db.scalar(stmt)

    def get_by_refresh_token_hash(self, token_hash: str) -> UserSession | None:
        stmt = (
            select(UserSession)
            .options(joinedload(UserSession.user).joinedload(User.role))
            .where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.session_status == SessionStatus.ACTIVE,
            )
        )
        return self.db.scalar(stmt)

    def revoke_session(self, session: UserSession) -> UserSession:
        session.session_status = SessionStatus.LOGGED_OUT
        session.logout_time = utc_now()
        return session

    def revoke_all_for_user(self, user_id: str) -> int:
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.session_status == SessionStatus.ACTIVE,
        )
        sessions = list(self.db.scalars(stmt).all())
        now = utc_now()
        for session in sessions:
            session.session_status = SessionStatus.LOGGED_OUT
            session.logout_time = now
        return len(sessions)

    def expire_stale_sessions(self) -> int:
        """Mark expired active sessions. Returns count updated."""
        stmt = select(UserSession).where(
            UserSession.session_status == SessionStatus.ACTIVE,
            UserSession.expires_at <= utc_now(),
        )
        sessions = list(self.db.scalars(stmt).all())
        for session in sessions:
            session.session_status = SessionStatus.EXPIRED
        return len(sessions)
