"""Tests for backend security helpers."""

from datetime import timedelta

from backend.config import AppSettings
from backend.security import SecurityService


def test_password_hash_round_trip() -> None:
    settings = AppSettings(jwt_secret_key="test-secret")
    security = SecurityService(settings)

    hashed = security.hash_password("correct horse battery staple")

    assert security.verify_password("correct horse battery staple", hashed) is True
    assert security.verify_password("wrong password", hashed) is False


def test_access_token_round_trip() -> None:
    settings = AppSettings(jwt_secret_key="test-secret")
    security = SecurityService(settings)

    token = security.create_access_token("alice", role="admin", expires_delta=timedelta(minutes=5))
    claims = security.decode_access_token(token)

    assert claims.subject == "alice"
    assert claims.role == "admin"