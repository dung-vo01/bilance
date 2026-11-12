from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User

INTERNAL_API_SECRET = "test-internal-secret"


@pytest.fixture
def internal_secret(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_API_SECRET", INTERNAL_API_SECRET)
    return {"X-Internal-Secret": INTERNAL_API_SECRET}


@pytest.mark.asyncio
async def test_internal_cleanup_expired_guest_accounts(client, db_session, internal_secret):
    await client.post("/api/auth/guest")
    await client.post("/api/auth/guest")
    await client.post("/api/auth/guest")

    guests_result = await db_session.execute(select(User).where(User.is_guest))

    guests = guests_result.scalars().all()

    assert len(guests) == 3
    
    remain_guest_id = guests[2].id
    expired_ids = [guest.id for guest in guests[0:2]]
    
    # Make the first 2 guest accounts expire
    for guest in guests[0:2]:
        guest.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
    
    await db_session.commit()

    # Call internal cleanup route to remove expired guest accounts
    cleanup_response = await client.post("/api/internal/cleanup-guests", headers=internal_secret)
    
    assert cleanup_response.status_code == 200
    assert cleanup_response.json()["data"]["deleted"] == 2
    
    # Only 1 guest remains
    assert await db_session.get(User, remain_guest_id) is not None
    
    for gid in expired_ids:
        assert await db_session.get(User, gid) is None


@pytest.mark.asyncio
async def test_internal_cleanup_expired_guest_accounts_without_secret(client, db_session, internal_secret):
    await client.post("/api/auth/guest")
    await client.post("/api/auth/guest")

    guests_result = await db_session.execute(select(User).where(User.is_guest))

    guests = guests_result.scalars().all()

    assert len(guests) == 2
    
    # Make the 2 guest accounts expire
    for guest in guests:
        guest.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
    
    await db_session.commit()

    # Call internal cleanup route without "X-Internal-Secret" header
    cleanup_response = await client.post("/api/internal/cleanup-guests")
    
    assert cleanup_response.status_code == 403
    
    guests_result = await db_session.execute(select(User).where(User.is_guest))
    
    guests = guests_result.scalars().all()

    # Guest accounts are still here
    assert len(guests) == 2


@pytest.mark.asyncio
async def test_internal_cleanup_expired_guest_accounts_with_wrong_secret(client, db_session, internal_secret):
    wrong_headers = {"X-Internal-Secret": "Wrong_header"}
    await client.post("/api/auth/guest")
    await client.post("/api/auth/guest")

    guests_result = await db_session.execute(select(User).where(User.is_guest))

    guests = guests_result.scalars().all()

    assert len(guests) == 2
    
    # Make the 2 guest accounts expire
    for guest in guests:
        guest.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
    
    await db_session.commit()

    # Call internal cleanup route with wrong "X-Internal-Secret" header
    cleanup_response = await client.post("/api/internal/cleanup-guests", headers=wrong_headers)
    
    assert cleanup_response.status_code == 403
    
    guests_result = await db_session.execute(select(User).where(User.is_guest))
    
    guests = guests_result.scalars().all()

    # Guest accounts are still here
    assert len(guests) == 2


@pytest.mark.asyncio
async def test_internal_cleanup_rejects_when_secret_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_API_SECRET", "")
    response = await client.post(
        "/api/internal/cleanup-guests", headers={"X-Internal-Secret": ""}
    )
    assert response.status_code == 403