from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import is_app_admin
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models import AppRole, User
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserUpdate
from app.services import auth_service


async def get_all(db: AsyncSession, search_kw: str, roles: list[str]) -> list[User]:
    stmt = select(User)

    if search_kw:
        like = f"%{search_kw}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like),
                User.firstname.ilike(like),
                User.lastname.ilike(like),
                User.email.ilike(like),
            )
        )

    if roles:
        parsed_roles = [r for r in (_parse_role(r) for r in roles) if r is not None]
        if parsed_roles:
            stmt = stmt.where(User.role.in_(parsed_roles))

    result = await db.execute(stmt)
    return list(result.scalars().all())


def _parse_role(value: str) -> AppRole | None:
    try:
        return AppRole(value.lower())
    except ValueError:
        return None


async def get_one(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


async def create(db: AsyncSession, current_user_id: int, data: RegisterRequest) -> User:
    if not await is_app_admin(db, current_user_id):
        raise ForbiddenError("Only app admins can create users")

    return await auth_service.register(db, data, current_user_id=current_user_id)


async def update(
    db: AsyncSession, user_id: int, current_user_id: int, data: UserUpdate
) -> User:
    has_admin_right = await is_app_admin(db, current_user_id)
    if user_id != current_user_id and not has_admin_right:
        raise ForbiddenError("Can only edit your own information")

    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    for field in ("firstname", "lastname", "phone_number"):
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value)

    if has_admin_right:
        if data.role is not None:
            if data.role == AppRole.MEMBER and user.role == AppRole.ADMIN:
                admin_count = await _admin_count(db)
                if admin_count <= 1:
                    raise AppError("Cannot remove the last admin")
            user.role = data.role

        if data.is_active is not None:
            if data.is_active is False and user.role == AppRole.ADMIN:
                admin_count = await _admin_count(db)
                if admin_count <= 1:
                    raise AppError("Cannot deactivate the last admin")
            user.is_active = data.is_active

    await db.commit()
    await db.refresh(user)

    return user


async def delete(db: AsyncSession, user_id: int, current_user_id: int) -> None:
    if not await is_app_admin(db, current_user_id):
        raise ForbiddenError("Only app admins can delete users")

    if user_id == current_user_id:
        raise AppError("Cannot delete your own account")

    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    if user.is_active:
        raise AppError("User must be deactivated before deleting")

    if user.role == AppRole.ADMIN:
        admin_count = await _admin_count(db)
        if admin_count <= 1:
            raise AppError("Cannot delete the last admin")

    await db.delete(user)
    await db.commit()


async def _admin_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(User).where(User.role == AppRole.ADMIN)
    )
    return result.scalar_one()
