"""Tests for the backend FastAPI application factory."""

from backend.app import create_app
from backend.config import AppSettings


def test_app_exposes_health_and_root_routes() -> None:
    app = create_app(AppSettings(jwt_secret_key="test-secret"))

    route_paths = {route.path for route in app.routes}

    assert "/health" in route_paths
    assert "/" in route_paths
    assert "/auth/token" in route_paths