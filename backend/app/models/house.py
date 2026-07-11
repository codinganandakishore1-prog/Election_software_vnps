"""House ORM model."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class House(Base, UUIDPrimaryKeyMixin):
    """School house."""

    __tablename__ = "houses"

    house_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
