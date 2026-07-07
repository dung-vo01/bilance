from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_refresh_user_id
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import envelope
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter()


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(db, data)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return envelope(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        }
    )


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.login(db, data.email, data.password)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return envelope(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        }
    )


# As long as the user stays active in the app at least once within 30 days
# they never need to log in again
@router.post("/refresh")
async def refresh(user_id: int = Depends(get_refresh_user_id)):
    access_token = create_access_token(str(user_id))
    refresh_token = create_refresh_token(str(user_id))  # new refresh token

    return envelope({"access_token": access_token, "refresh_token": refresh_token})


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return envelope(UserOut.model_validate(user).model_dump(mode="json"))
