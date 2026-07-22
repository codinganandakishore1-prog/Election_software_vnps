"""JWT token generation and validation."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.config.settings import settings


class JWTHandler:
    """Generate and validate JWT tokens."""

    TOKEN_TYPE_ACCESS = "access"
    TOKEN_TYPE_REFRESH = "refresh"
    TOKEN_TYPE_NODE = "node"

    def __init__(self) -> None:
        self.secret = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm

    def create_access_token(
        self,
        *,
        user_id: str,
        username: str,
        role: str,
        session_id: str,
    ) -> tuple[str, str, int]:
        """Return (token, jti, expires_in_seconds)."""
        jti = str(uuid4())
        expires_delta = timedelta(minutes=settings.jwt_access_expiry_minutes)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "sid": session_id,
            "type": self.TOKEN_TYPE_ACCESS,
            "jti": jti,
            "exp": expire,
        }
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, jti, int(expires_delta.total_seconds())

    def create_refresh_token(self, *, user_id: str, session_id: str) -> tuple[str, str]:
        """Return (token, jti)."""
        jti = str(uuid4())
        expires_delta = timedelta(days=settings.jwt_refresh_expiry_days)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": user_id,
            "sid": session_id,
            "type": self.TOKEN_TYPE_REFRESH,
            "jti": jti,
            "exp": expire,
        }
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, jti

    def create_node_token(self, *, node_id: str, session_id: str) -> tuple[str, str, int]:
        """Return (token, jti, expires_in_seconds)."""
        jti = str(uuid4())
        expires_delta = timedelta(hours=settings.node_jwt_expiry_hours)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": node_id,
            "sid": session_id,
            "type": self.TOKEN_TYPE_NODE,
            "jti": jti,
            "exp": expire,
        }
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token, jti, int(expires_delta.total_seconds())

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])

    def decode_token_safe(self, token: str) -> dict | None:
        try:
            return self.decode_token(token)
        except JWTError:
            return None

    def get_remaining_seconds(self, payload: dict) -> int:
        exp = payload.get("exp")
        if exp is None:
            return 0
        if isinstance(exp, datetime):
            expires_at = exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)
        else:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        return max(remaining, 0)

    @staticmethod
    def assert_token_type(payload: dict, expected_type: str) -> None:
        if payload.get("type") != expected_type:
            raise JWTError("Invalid token type")
