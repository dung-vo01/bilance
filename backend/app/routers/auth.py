from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_user_id, get_refresh_user_id
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.schemas.common import envelope
from app.schemas.user import UserOut
from app.services import auth_service, email_service, guest_service

router = APIRouter()


@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user, token = await auth_service.register(db, data)
    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.firstname,
        user.username,
        token,
    )

    return envelope({"user": UserOut.model_validate(user).model_dump(mode="json")})


@router.post("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    user = await auth_service.verify_email(db, token)
    return envelope({"user": UserOut.model_validate(user).model_dump(mode="json")})


@router.post("/resend-verification")
async def resend_verification(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.resend_verification(db, data.email)
    if result:
        user, token = result
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.firstname,
            user.username,
            token,
        )
    return envelope(
        {
            "message": "If that email is registered and unverified, a new link has been sent"
        }
    )


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.forgot_password(db, data.email)
    if result:
        user, token = result
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.firstname,
            user.username,
            token,
        )
    return envelope(
        {"message": "If that email is registered, a reset link has been sent"}
    )


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    await auth_service.reset_password(db, data.token, data.new_password)
    return envelope({"message": "Password has been reset"})


@router.post("/guest")
async def guest_login(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    guest, access_token, refresh_token = await guest_service.create_guest(db)
    background_tasks.add_task(guest_service.cleanup_expired_guests)

    return envelope(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": UserOut.model_validate(guest).model_dump(mode="json"),
        }
    )


@router.post("/guest/logout")
async def guest_logout(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await guest_service.delete_guest_now(db, user_id)
    return envelope({"message": "Guest account deleted"})


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
