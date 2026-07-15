"""House ORM model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.node import VotingNode
    from app.models.sync import Vote


class House(Base, UUIDPrimaryKeyMixin):
    """School house."""

    __tablename__ = "houses"
    __table_args__ = (Index("ix_houses_house_name", "house_name"),)

    house_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="house")
    voting_nodes: Mapped[list["VotingNode"]] = relationship(back_populates="house")
    votes: Mapped[list["Vote"]] = relationship(back_populates="house")
