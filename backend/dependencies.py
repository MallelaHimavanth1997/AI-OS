"""FastAPI dependencies for settings, security, and request context."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Header, HTTPException, status

from .config import AppSettings, get_settings
from .security import SecurityService, TokenData


@lru_cache(maxsize=1)
def get_security_service() -> SecurityService:
    """Return a cached security service instance."""

    return SecurityService(get_settings())


def get_current_token_data(authorization: str | None = Header(default=None)) -> TokenData:
    """Validate a bearer token and return parsed claims."""

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header.")

    prefix, _, token = authorization.partition(" ")
    if prefix.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme.")

    try:
        return get_security_service().decode_access_token(token)
    except Exception as exc:  # pragma: no cover - translated to API error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.") from exc


def get_settings_dependency() -> AppSettings:
    """Expose settings as a FastAPI dependency."""

    return get_settings()
