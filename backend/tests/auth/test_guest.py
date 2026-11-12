from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import AppRole, ExpenseGroup, ExpenseGroupMember, User
from app.models.repayment import Repayment
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
async def test_guest_login_seeds_repayments_and_pending_expense(client, db_session):
    response = await client.post("/api/auth/guest")
    data = response.json()["data"]
    guest_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    group_result = await db_session.execute(
        select(ExpenseGroup).where(ExpenseGroup.created_by_id == guest_id)
    )
    group_id = group_result.scalar_one().id

    repayments_resp = await client.get(
        f"/api/expense-groups/{group_id}/repayments", headers=headers
    )
    assert repayments_resp.status_code == 200
    repayments = repayments_resp.json()["data"]
    assert [r["is_deleted"] for r in repayments] == [False, True]
    assert repayments[1]["deleted_note"] is not None

    settlement_resp = await client.get(
        f"/api/expense-groups/{group_id}/settlement", headers=headers
    )
    settlement = settlement_resp.json()["data"]
    assert len(settlement["pending_expenses"]) == 1
    # 100 owed for the split expenses - 40 resolved; the undone 30 is ignored.
    assert len(settlement["transactions"]) == 1
    transaction = settlement["transactions"][0]
    assert transaction["to_user_id"] == guest_id
    assert transaction["amount"] == pytest.approx(60.00)


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

    await guest_service.purge_expired_guests(db_session)

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
async def test_guest_logout_deletes_own_account_and_data(
    client, db_session, add_repayment
):
    login = await client.post("/api/auth/guest")
    data = login.json()["data"]
    guest_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    companion_result = await db_session.execute(
        select(User).where(User.username == guest_service.COMPANION_USERNAME)
    )
    companion_id = companion_result.scalar_one().id

    group_result = await db_session.execute(
        select(ExpenseGroup).where(ExpenseGroup.created_by_id == guest_id)
    )
    group_id = group_result.scalar_one().id

    repayment = await add_repayment(
        group_id,
        from_user_id=companion_id,
        to_user_id=guest_id,
        amount=20,
        created_by_id=guest_id,
    )

    response = await client.post("/api/auth/guest/logout", headers=headers)
    assert response.status_code == 200

    assert await db_session.get(User, guest_id) is None
    assert await db_session.get(ExpenseGroup, group_id) is None
    # Companion account survives - it's a shared, permanent fixture.
    assert await db_session.get(User, companion_id) is not None
    assert await db_session.get(Repayment, repayment.id) is None


@pytest.mark.asyncio
async def test_guest_logout_rejects_non_guest_account(client, auth_headers):
    headers, _ = await auth_headers(username="realuser2", email="real2@example.com")
    response = await client.post("/api/auth/guest/logout", headers=headers)
    assert response.status_code == 403
