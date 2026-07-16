from datetime import datetime, timedelta, timezone

import pytest

from app.services.auth_service import _hash_token


@pytest.fixture(autouse=True)
def mock_email_send(monkeypatch):
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.email_service._send", _noop)


@pytest.mark.asyncio
async def test_register_creates_unverified_user(client, db_session):
    from sqlalchemy import select

    from app.models import User

    response = await client.post(
        "/api/auth/register",
        json={"username": "iris", "email": "iris@example.com", "password": "pw12345"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["user"]["is_email_verified"] is False

    result = await db_session.execute(select(User).where(User.username == "iris"))
    user = result.scalar_one()
    assert user.is_email_verified is False
    assert user.email_verification_token_hash is not None


@pytest.mark.asyncio
async def test_login_blocked_when_unverified(client, create_user):
    await create_user(
        username="jack",
        email="jack@example.com",
        password="secret123",
        is_email_verified=False,
    )
    response = await client.post(
        "/api/auth/login", json={"email": "jack@example.com", "password": "secret123"}
    )
    assert response.status_code == 403
    assert "verify" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_login_succeeds_after_verification(client, create_user, db_session):
    user = await create_user(
        username="kate",
        email="kate@example.com",
        password="secret123",
        is_email_verified=False,
    )
    token = "plaintext-token"
    user.email_verification_token_hash = _hash_token(token)
    user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
        hours=1
    )
    await db_session.commit()

    verify_response = await client.post(f"/api/auth/verify-email/{token}")
    assert verify_response.status_code == 200
    assert verify_response.json()["data"]["user"]["is_email_verified"] is True

    login_response = await client.post(
        "/api/auth/login", json={"email": "kate@example.com", "password": "secret123"}
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client):
    response = await client.post("/api/auth/verify-email/not-a-real-token")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_expired_token(client, create_user, db_session):
    user = await create_user(
        username="liam", email="liam@example.com", is_email_verified=False
    )
    token = "expired-token"
    user.email_verification_token_hash = _hash_token(token)
    user.email_verification_token_expires_at = datetime.now(timezone.utc) - timedelta(
        hours=1
    )
    await db_session.commit()

    response = await client.post(f"/api/auth/verify-email/{token}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_resend_verification_unknown_email(client):
    response = await client.post(
        "/api/auth/resend-verification", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 200
    assert "message" in response.json()["data"]


@pytest.mark.asyncio
async def test_resend_verification_already_verified(client, create_user):
    await create_user(username="mona", email="mona@example.com", is_email_verified=True)
    response = await client.post(
        "/api/auth/resend-verification", json={"email": "mona@example.com"}
    )
    assert response.status_code == 200
