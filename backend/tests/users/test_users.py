import pytest
from app.core.security import create_access_token
from app.models import AppRole


@pytest.mark.asyncio
async def test_only_admin_can_create_user(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    response = await client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "pw123456",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_only_admin_can_list_users(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(client, auth_headers):
    headers, _ = await auth_headers(
        username="admin", email="admin@example.com", role=AppRole.ADMIN
    )
    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_create_user(client, auth_headers):
    headers, _ = await auth_headers(
        username="admin", email="admin@example.com", role=AppRole.ADMIN
    )
    response = await client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "pw123456",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_user_can_edit_own_profile_not_role(client, auth_headers):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    response = await client.patch(
        f"/api/users/{user.id}",
        headers=headers,
        json={"firstname": "Alicia", "role": "admin"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["firstname"] == "Alicia"
    assert data["role"] == "member"  # role edit ignored for non-admin


@pytest.mark.asyncio
async def test_cannot_deactivate_last_admin(client, auth_headers):
    headers, user = await auth_headers(
        username="admin", email="admin@example.com", role=AppRole.ADMIN
    )
    response = await client.patch(
        f"/api/users/{user.id}", headers=headers, json={"is_active": False}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_delete_active_user(client, auth_headers, create_user):
    headers, _ = await auth_headers(
        username="admin", email="admin@example.com", role=AppRole.ADMIN
    )
    target = await create_user(username="bob", email="bob@example.com")

    response = await client.delete(f"/api/users/{target.id}", headers=headers)
    assert response.status_code == 400
