import pytest
from sqlalchemy import select

from app.models import User


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_rollback_isolation_step_one(db_session, create_user):
    await create_user(username="rollback_user", email="rollback@example.com")
    result = await db_session.execute(
        select(User).where(User.username == "rollback_user")
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_rollback_isolation_step_two(db_session):
    # Proves the previous test's commit was rolled back at teardown,
    # each test gets a clean slate via the savepoint-per-test fixture.
    result = await db_session.execute(
        select(User).where(User.username == "rollback_user")
    )
    assert result.scalar_one_or_none() is None
