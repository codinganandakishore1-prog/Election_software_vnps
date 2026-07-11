"""JWT token handling (placeholder)."""

from app.config.settings import settings


class JWTHandler:
    """Generate and validate JWT tokens."""

    def __init__(self) -> None:
        self.secret = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm

    # Implementation deferred to authentication phase.
