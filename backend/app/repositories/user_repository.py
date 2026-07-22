"""User repository."""

from election_platform.enums.admin import LoginStatus
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.models.user import LoginHistory, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for user records."""

    model = User

    def get_by_username(self, username: str) -> User | None:
        from sqlalchemy.orm import joinedload

        stmt = select(User).options(joinedload(User.role)).where(User.username == username)
        return self.db.scalar(stmt)

    def get_by_id_with_role(self, user_id: str) -> User | None:
        from sqlalchemy.orm import joinedload

        return self.db.scalar(
            select(User).options(joinedload(User.role)).where(User.id == user_id)
        )

    def update_last_login(self, user: User) -> User:
        user.last_login = utc_now()
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.get_by_field("email", email)

    def list_by_role(self, role_id: str) -> list[User]:
        return self.list_by_field("role_id", role_id)


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    """Data access for login history."""

    model = LoginHistory

    def list_for_user(self, user_id: str, *, limit: int | None = None) -> list[LoginHistory]:
        stmt = (
            select(LoginHistory)
            .where(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.login_time.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_latest_success(self, user_id: str) -> LoginHistory | None:
        stmt = (
            select(LoginHistory)
            .where(
                LoginHistory.user_id == user_id,
                LoginHistory.login_status == LoginStatus.SUCCESS,
                LoginHistory.logout_time.is_(None),
            )
            .order_by(LoginHistory.login_time.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
