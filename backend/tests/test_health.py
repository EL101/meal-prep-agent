from fastapi.testclient import TestClient

from app.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_cors_preflight_allows_expo_web_origin():
    response = TestClient(app).options(
        "/me",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_cors_rejects_unknown_origin():
    response = TestClient(app).get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers
