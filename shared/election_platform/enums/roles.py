"""User role enumerations."""

from enum import Enum


class UserRole(str, Enum):
    """Administrator and node roles."""

    SUPER_ADMINISTRATOR = "Super Administrator"
    ADMINISTRATOR = "Administrator"
    VIEWER = "Viewer"
    VOTING_NODE = "Voting Node"
