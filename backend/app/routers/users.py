from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.auth import RegisterRequest
from app.schemas.common import envelope
from app.schemas.user import UserOut, UserUpdate
from app.services import email_service, user_service

router = APIRouter()


@router.get("")
async def get_users(
    search_kw: str = Query(""),
    roles: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    role_list = [r for r in roles.split(",") if r]
    users = await user_service.get_all(db, search_kw, role_list)
    return envelope([UserOut.model_validate(u).model_dump(mode="json") for u in users])


@router.post("", status_code=201)
async def add_user(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user, token = await user_service.create(db, current_user_id, data)
    if user.email:
        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.firstname,
            user.username,
            token,
        )
    return envelope(UserOut.model_validate(user).model_dump(mode="json"))


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    _: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_one(db, user_id)
    return envelope(UserOut.model_validate(user).model_dump(mode="json"))


@router.patch("/{user_id}")
async def update_user_profile(
    user_id: int,
    data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update(db, user_id, current_user_id, data)
    return envelope(UserOut.model_validate(user).model_dump(mode="json"))


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await user_service.delete(db, user_id, current_user_id)
    return envelope({"message": "User deleted"})
