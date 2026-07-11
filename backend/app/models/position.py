"""Position ORM model."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Position(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Election position."""

    __tablename__ = "positions"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    election_type: Mapped[str] = mapped_column(String(20), nullable=False)
    position_name: Mapped[str] = mapped_column(String(150), nullable=False)
    winner_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
