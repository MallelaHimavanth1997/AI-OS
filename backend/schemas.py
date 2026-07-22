"""Shared API schemas for the AI-OS backend."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health probe response payload."""

    status: str = Field(default="ok")
    app_name: str
    environment: str
    timestamp: datetime


class TokenResponse(BaseModel):
    """JWT token response payload."""

    access_token: str
    token_type: str = Field(default="bearer")


class LoginRequest(BaseModel):
    """Minimal login request for issuing a JWT token."""

    username: str
    password: str
