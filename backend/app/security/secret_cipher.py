"""Symmetric encryption for stored secrets (e.g. MySQL passwords)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import settings


class SecretCipher:
    """Encrypt and decrypt reversible secrets using Fernet."""

    def __init__(self, secret_key: str | None = None) -> None:
        source = secret_key or settings.jwt_secret
        digest = hashlib.sha256(source.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt stored secret") from exc
