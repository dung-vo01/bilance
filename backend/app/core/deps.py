from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.core import security
from app.core.exceptions import UnauthenticatedError
from app.db.session import get_db
from app.models import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = security.decode_token(creds.credentials)
    except JWTError:
        raise UnauthenticatedError("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthenticatedError("Invalid token type")

    user = await db.get(User, int(payload["sub"]))
    if not user:
        raise UnauthenticatedError("User not found")

    # For logging purpose
    request.state.user_id = user.id
    
    return user


async def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    return user.id


async def get_refresh_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    try:
        payload = security.decode_token(creds.credentials)
    except JWTError:
        raise UnauthenticatedError("Invalid or expired token")

    if payload.get("type") != "refresh":
        raise UnauthenticatedError("Invalid token type")

    return int(payload["sub"])
