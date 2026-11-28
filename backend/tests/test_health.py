import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_cors_default_allows_expo_web_origin():
    assert Settings.model_fields["cors_origins"].default == ["http://localhost:8081"]


def test_cors_preflight_allows_configured_origin():
    # The middleware is built from the settings at import, which a developer's CORS_ORIGINS or
    # .env can change, so test against whatever origin is configured.
    origins = get_settings().cors_origins
    if not origins:
        pytest.skip("CORS_ORIGINS is empty")
    response = TestClient(app).options(
        "/me",
        headers={
            "Origin": origins[0],
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origins[0]


def test_cors_rejects_unknown_origin():
    response = TestClient(app).get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers
