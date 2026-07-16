from datetime import datetime, timedelta, timezone

import pytest

from app.services.auth_service import _hash_token


@pytest.fixture(autouse=True)
def mock_email_send(monkeypatch):
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.email_service._send", _noop)


@pytest.mark.asyncio
async def test_forgot_password_known_email(client, create_user, db_session):
    from sqlalchemy import select

    from app.models import User

    await create_user(username="nina", email="nina@example.com")
    response = await client.post(
        "/api/auth/forgot-password", json={"email": "nina@example.com"}
    )
    assert response.status_code == 200

    result = await db_session.execute(select(User).where(User.username == "nina"))
    user = result.scalar_one()
    assert user.password_reset_token_hash is not None


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(client):
    response = await client.post(
        "/api/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_success(client, create_user, db_session):
    user = await create_user(
        username="oscar", email="oscar@example.com", password="oldpassword"
    )
    token = "reset-token"
    user.password_reset_token_hash = _hash_token(token)
    user.password_reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=30
    )
    await db_session.commit()

    response = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200

    old_login = await client.post(
        "/api/auth/login",
        json={"email": "oscar@example.com", "password": "oldpassword"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/auth/login",
        json={"email": "oscar@example.com", "password": "newpassword123"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    response = await client.post(
        "/api/auth/reset-password",
        json={"token": "bogus", "new_password": "whatever123"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_expired_token(client, create_user, db_session):
    user = await create_user(username="pam", email="pam@example.com")
    token = "expired-reset-token"
    user.password_reset_token_hash = _hash_token(token)
    user.password_reset_token_expires_at = datetime.now(timezone.utc) - timedelta(
        minutes=1
    )
    await db_session.commit()

    response = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "whatever123"},
    )
    assert response.status_code == 400
