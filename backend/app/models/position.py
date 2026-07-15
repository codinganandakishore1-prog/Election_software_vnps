"""Position ORM model."""

from typing import TYPE_CHECKING

from election_platform.enums.election import ElectionType
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.enums import enum_column

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.election import Election
    from app.models.sync import Vote


class Position(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Election position."""

    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint("winner_count > 0", name="ck_positions_winner_count_positive"),
        CheckConstraint("display_order >= 1", name="ck_positions_display_order_min"),
        Index("ix_positions_election_id", "election_id"),
        Index("ix_positions_display_order", "display_order"),
        Index("ix_positions_election_type", "election_type"),
        Index("ix_positions_position_name", "position_name"),
        Index("ix_positions_election_id_position_id", "election_id", "id"),
        Index("ix_positions_position_id_display_order", "id", "display_order"),
        Index("ix_positions_election_type_active", "election_type", "active"),
    )

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
    )
    election_type: Mapped[ElectionType] = mapped_column(
        enum_column(ElectionType, name="position_election_type"),
        nullable=False,
    )
    position_name: Mapped[str] = mapped_column(String(150), nullable=False)
    winner_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    election: Mapped["Election"] = relationship(back_populates="positions")
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="position",
        cascade="all, delete-orphan",
    )
    votes: Mapped[list["Vote"]] = relationship(back_populates="position")
