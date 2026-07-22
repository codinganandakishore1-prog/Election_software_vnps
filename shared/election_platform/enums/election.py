"""Election-related enumerations."""

from enum import Enum


class ElectionType(str, Enum):
    """Supported election types."""

    REGULAR = "Regular"
    HOUSE = "House"


class ElectionStatus(str, Enum):
    """Election lifecycle statuses."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    LIVE = "Live"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class CandidateStatus(str, Enum):
    """Candidate record statuses."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PUBLISHED = "Published"


class PositionStatus(str, Enum):
    """Position record statuses."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PUBLISHED = "Published"
