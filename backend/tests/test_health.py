from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import health
from app.config import Settings
from app.main import add_cors, app

DEFAULT_ORIGINS = Settings.model_fields["cors_origins"].default


def cors_app(origins: list[str]) -> TestClient:
    # A fresh app with the same CORS setup as app.main, built from the given origins rather than
    # the developer's CORS_ORIGINS or .env, which app.main reads at import.
    test_app = FastAPI()
    add_cors(test_app, origins)
    test_app.include_router(health.router)
    return TestClient(test_app)


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_cors_default_allows_expo_web_origin():
    assert DEFAULT_ORIGINS == ["http://localhost:8081"]


def test_cors_preflight_allows_configured_origin():
    response = cors_app(DEFAULT_ORIGINS).options(
        "/health",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_cors_rejects_unknown_origin():
    response = cors_app(DEFAULT_ORIGINS).get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers
