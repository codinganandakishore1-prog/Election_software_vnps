"""SQLAlchemy enum column helpers."""

from enum import Enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

EnumT = TypeVar("EnumT", bound=Enum)


def enum_column(enum_cls: type[EnumT], *, name: str) -> SAEnum:
    """Create a VARCHAR-backed enum column for MySQL portability."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        values_callable=lambda members: [member.value for member in members],
        length=50,
    )
