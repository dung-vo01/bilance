import pytest

from app.core.config import settings
from app.core.limiter import limiter


@pytest.fixture
def rate_limiting():
    """Turn the limiter back on for one test, with clean counters."""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.reset()


async def test_default_limit_returns_429_envelope(client, rate_limiting):
    origin = settings.cors_origins_list[0]

    for _ in range(120):
        response = await client.get("/api/auth/me")
        assert response.status_code != 429

    response = await client.get("/api/auth/me", headers={"Origin": origin})

    assert response.status_code == 429
    body = response.json()
    assert body["success"] is False
    assert "error" in body
    assert "retry-after" in response.headers
    # 429s must still pass through CORS, or browsers hide the message
    assert response.headers["access-control-allow-origin"] == origin


async def test_health_is_exempt(client, rate_limiting):
    for _ in range(130):
        response = await client.get("/health")
        assert response.status_code != 429


async def test_forgot_password_rate_limit(client, rate_limiting):
    for _ in range(5):
        response = await client.post(
            "/api/auth/forgot-password", json={"email": "nonuser@example.com"}
        )
        assert response.status_code == 200

    response = await client.post(
        "/api/auth/forgot-password", json={"email": "nonuser@example.com"}
    )
    assert response.status_code == 429
    assert response.json()["success"] is False
    assert "retry-after" in response.headers


async def test_login_rate_limit(client, rate_limiting):
    payload = {"email": "nonuser@example.com", "password": "wrong-password"}

    for _ in range(10):
        response = await client.post("/api/auth/login", json=payload)
        assert response.status_code != 429

    response = await client.post("/api/auth/login", json=payload)
    assert response.status_code == 429


async def test_limits_are_per_route(client, rate_limiting):
    payload = {"email": "nonuser@example.com"}
    for _ in range(6):
        await client.post("/api/auth/forgot-password", json=payload)

    response = await client.post(
        "/api/auth/login", json={"email": "nonuser@example.com", "password": "x"}
    )
    assert response.status_code != 429
