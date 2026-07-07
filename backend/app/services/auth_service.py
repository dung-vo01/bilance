from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import is_app_admin
from app.core.exceptions import AppError, ConflictError, UnauthenticatedError
from app.core.security import hash_password, verify_password
from app.models import AppRole, User
from app.schemas.auth import RegisterRequest


async def register(
    db: AsyncSession, data: RegisterRequest, current_user_id: int | None = None
) -> User:
    if not data.email:
        raise AppError("Email is required")
    if not data.username:
        raise AppError("Username is required")

    existing_email = await db.execute(select(User).where(User.email == data.email))
    if existing_email.scalar_one_or_none():
        raise ConflictError("Email already taken")

    existing_username = await db.execute(
        select(User).where(User.username == data.username)
    )
    if existing_username.scalar_one_or_none():
        raise ConflictError("Username already taken")

    password = data.password or "password123"
    password_hash = await hash_password(password)

    user = User(
        username=data.username,
        email=data.email,
        password_hash=password_hash,
        firstname=data.firstname,
        lastname=data.lastname,
        phone_number=data.phone_number,
    )

    # Case when admin creates a new user
    if data.role and current_user_id and await is_app_admin(db, current_user_id):
        user.role = AppRole(data.role.lower())

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def login(db: AsyncSession, email: str | None, password: str | None) -> User:
    if not email:
        raise AppError("Email is required")
    if not password:
        raise AppError("Password is required")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not await verify_password(password, user.password_hash):
        raise UnauthenticatedError("Invalid credentials")

    return user
