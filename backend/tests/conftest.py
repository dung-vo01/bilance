import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app import models  # noqa: F401 -- populate Base.metadata
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.models import AppRole, User
from main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_user(db_session):
    async def _create(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "password123",
        role: AppRole = AppRole.MEMBER,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=await hash_password(password),
            role=role,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def auth_headers(create_user):
    async def _headers(**kwargs) -> tuple[dict, User]:
        user = await create_user(**kwargs)
        token = create_access_token(str(user.id))
        return {"Authorization": f"Bearer {token}"}, user

    return _headers
