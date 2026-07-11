"""Password hashing utilities (placeholder)."""


class PasswordHasher:
    """Hash and verify passwords using bcrypt."""

    # Implementation deferred to authentication phase.

    @staticmethod
    def hash_password(password: str) -> str:
        raise NotImplementedError("Password hashing not implemented in scaffold phase.")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        raise NotImplementedError("Password verification not implemented in scaffold phase.")
