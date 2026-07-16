import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "pw12345"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["username"] == "alice"
    assert body["data"]["user"]["is_email_verified"] is False
    assert "access_token" not in body["data"]
    assert "refresh_token" not in body["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client, create_user):
    await create_user(username="bob", email="dup@example.com")
    response = await client.post(
        "/api/auth/register",
        json={"username": "bob2", "email": "dup@example.com", "password": "pw12345"},
    )
    assert response.status_code == 409
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_register_duplicate_username(client, create_user):
    await create_user(username="carol", email="carol@example.com")
    response = await client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "other@example.com", "password": "pw12345"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, create_user):
    await create_user(username="dave", email="dave@example.com", password="secret123")
    response = await client.post(
        "/api/auth/login", json={"email": "dave@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["user"]["username"] == "dave"


@pytest.mark.asyncio
async def test_login_wrong_password(client, create_user):
    await create_user(username="erin", email="erin@example.com", password="secret123")
    response = await client.post(
        "/api/auth/login", json={"email": "erin@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client, create_user):
    from app.core.security import create_refresh_token, decode_token

    user = await create_user(username="frank", email="frank@example.com")
    refresh_token = create_refresh_token(str(user.id))

    response = await client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert "access_token" in body
    assert "refresh_token" in body

    access_payload = decode_token(body["access_token"])
    refresh_payload = decode_token(body["refresh_token"])
    assert access_payload["sub"] == str(user.id)
    assert access_payload["type"] == "access"
    assert refresh_payload["sub"] == str(user.id)
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(client, auth_headers):
    headers, _ = await auth_headers(username="gina", email="gina@example.com")
    response = await client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_returns_current_user(client, auth_headers):
    headers, user = await auth_headers(username="henry", email="henry@example.com")
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == user.id
