"""Desktop application exceptions."""


class DuplicateVoteError(Exception):
    """Raised when a vote UUID is already persisted or queued."""
