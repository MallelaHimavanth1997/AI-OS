"""Security helpers for password hashing and JWT handling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any

import jwt

from .config import AppSettings


@dataclass(slots=True)
class TokenData:
    """Parsed JWT claims relevant to application authorization."""

    subject: str
    role: str
    expires_at: datetime


class SecurityService:
    """Encapsulate password hashing and token creation."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def hash_password(self, password: str, *, salt: str | None = None) -> str:
        """Hash a password with PBKDF2 and a per-password salt."""

        if not password:
            raise ValueError("Password must not be empty.")

        salt_value = salt or secrets.token_hex(16)
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_value.encode("utf-8"),
            210_000,
        )
        return f"pbkdf2_sha256${salt_value}${derived_key.hex()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against a stored PBKDF2 hash."""

        try:
            algorithm, salt, digest = hashed_password.split("$", 2)
        except ValueError as exc:
            raise ValueError("Invalid password hash format.") from exc

        if algorithm != "pbkdf2_sha256":
            raise ValueError("Unsupported password hash algorithm.")

        recomputed = self.hash_password(password, salt=salt)
        return hmac.compare_digest(recomputed, hashed_password)

    def create_access_token(self, subject: str, *, role: str = "user", expires_delta: timedelta | None = None) -> str:
        """Create a signed JWT access token."""

        expire_at = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        )
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "exp": expire_at,
            "iat": datetime.now(timezone.utc),
            "iss": self.settings.app_name,
        }
        return jwt.encode(payload, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)

    def decode_access_token(self, token: str) -> TokenData:
        """Decode and validate a JWT access token."""

        payload = jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat", "iss"]},
        )
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        return TokenData(
            subject=str(payload["sub"]),
            role=str(payload.get("role", "user")),
            expires_at=expires_at,
        )
