from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import AppRole, ExpenseGroup, ExpenseGroupMember, User
from app.services import guest_service


@pytest.mark.asyncio
async def test_guest_login_creates_verified_guest_with_tokens(client):
    response = await client.post("/api/auth/guest")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["user"]["is_guest"] is True
    assert body["user"]["is_email_verified"] is True
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_guest_login_seeds_sample_data(client, db_session):
    response = await client.post("/api/auth/guest")
    guest_id = response.json()["data"]["user"]["id"]

    expenses_resp = await client.get(
        "/api/expenses",
        headers={"Authorization": f"Bearer {response.json()['data']['access_token']}"},
    )
    assert expenses_resp.status_code == 200
    assert len(expenses_resp.json()["data"]) > 0

    group_result = await db_session.execute(
        select(ExpenseGroup).where(ExpenseGroup.created_by_id == guest_id)
    )
    group = group_result.scalar_one()

    members_result = await db_session.execute(
        select(ExpenseGroupMember).where(
            ExpenseGroupMember.expense_group_id == group.id
        )
    )
    assert len(members_result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_guest_login_reuses_companion_account(client, db_session):
    await client.post("/api/auth/guest")
    await client.post("/api/auth/guest")

    result = await db_session.execute(
        select(User).where(User.username == guest_service.COMPANION_USERNAME)
    )
    companions = result.scalars().all()
    assert len(companions) == 1


@pytest.mark.asyncio
async def test_cleanup_removes_expired_guests_but_not_companion_or_fresh_guest(
    client, db_session
):
    old_response = await client.post("/api/auth/guest")
    old_guest_id = old_response.json()["data"]["user"]["id"]

    old_guest = await db_session.get(User, old_guest_id)
    old_guest.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
    await db_session.commit()

    fresh_response = await client.post("/api/auth/guest")
    fresh_guest_id = fresh_response.json()["data"]["user"]["id"]

    await guest_service._cleanup_expired_guests(db_session)

    assert await db_session.get(User, old_guest_id) is None
    assert await db_session.get(User, fresh_guest_id) is not None

    companion_result = await db_session.execute(
        select(User).where(User.username == guest_service.COMPANION_USERNAME)
    )
    assert companion_result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_get_users_excludes_guests(client, auth_headers):
    headers, _ = await auth_headers(
        username="realuser", email="real@example.com", role=AppRole.ADMIN
    )
    await client.post("/api/auth/guest")

    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 200
    usernames = [u["username"] for u in response.json()["data"]]
    assert not any(u.startswith("guest_") for u in usernames)


@pytest.mark.asyncio
async def test_guest_logout_deletes_own_account_and_data(client, db_session):
    login = await client.post("/api/auth/guest")
    data = login.json()["data"]
    guest_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    group_result = await db_session.execute(
        select(ExpenseGroup).where(ExpenseGroup.created_by_id == guest_id)
    )
    group_id = group_result.scalar_one().id

    response = await client.post("/api/auth/guest/logout", headers=headers)
    assert response.status_code == 200

    assert await db_session.get(User, guest_id) is None
    assert await db_session.get(ExpenseGroup, group_id) is None

    # Companion account survives - it's a shared, permanent fixture.
    companion_result = await db_session.execute(
        select(User).where(User.username == guest_service.COMPANION_USERNAME)
    )
    assert companion_result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_guest_logout_rejects_non_guest_account(client, auth_headers):
    headers, _ = await auth_headers(username="realuser2", email="real2@example.com")
    response = await client.post("/api/auth/guest/logout", headers=headers)
    assert response.status_code == 403
