import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import is_app_admin
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    ConflictError,
    EmailNotVerifiedError,
    InvalidTokenError,
    UnauthenticatedError,
)
from app.core.security import hash_password, verify_password
from app.models import AppRole, User
from app.schemas.auth import RegisterRequest


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def register(
    db: AsyncSession, data: RegisterRequest, current_user_id: int | None = None
) -> tuple[User, str]:
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

    token = _generate_token()

    user = User(
        username=data.username,
        email=data.email,
        password_hash=password_hash,
        firstname=data.firstname,
        lastname=data.lastname,
        phone_number=data.phone_number,
        email_verification_token_hash=_hash_token(token),
        email_verification_token_expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
    )

    # Case when admin creates a new user
    if data.role and current_user_id and await is_app_admin(db, current_user_id):
        user.role = AppRole(data.role.lower())

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user, token


async def login(db: AsyncSession, email: str | None, password: str | None) -> User:
    if not email:
        raise AppError("Email is required")
    if not password:
        raise AppError("Password is required")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not await verify_password(password, user.password_hash):
        raise UnauthenticatedError("Invalid credentials")

    if not user.is_email_verified:
        raise EmailNotVerifiedError()

    return user


async def verify_email(db: AsyncSession, token: str) -> User:
    token_hash = _hash_token(token)
    result = await db.execute(
        select(User).where(User.email_verification_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.email_verification_token_expires_at
        or user.email_verification_token_expires_at < datetime.now(timezone.utc)
    ):
        raise InvalidTokenError()

    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token_hash = None
    user.email_verification_token_expires_at = None

    await db.commit()
    await db.refresh(user)
    return user


async def resend_verification(
    db: AsyncSession, email: str | None
) -> tuple[User, str] | None:
    if not email:
        raise AppError("Email is required")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or user.is_email_verified:
        return None

    token = _generate_token()
    user.email_verification_token_hash = _hash_token(token)
    user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
    )
    await db.commit()
    return user, token


async def forgot_password(db: AsyncSession, email: str | None) -> tuple[User, str] | None:
    if not email:
        raise AppError("Email is required")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    token = _generate_token()
    user.password_reset_token_hash = _hash_token(token)
    user.password_reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )
    await db.commit()
    return user, token


async def reset_password(db: AsyncSession, token: str, new_password: str | None) -> User:
    if not new_password:
        raise AppError("Password is required")

    token_hash = _hash_token(token)
    result = await db.execute(
        select(User).where(User.password_reset_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.password_reset_token_expires_at
        or user.password_reset_token_expires_at < datetime.now(timezone.utc)
    ):
        raise InvalidTokenError()

    user.password_hash = await hash_password(new_password)
    user.password_reset_token_hash = None
    user.password_reset_token_expires_at = None

    await db.commit()
    await db.refresh(user)
    return user
