from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppRole, ExpenseGroupMember, GroupRole, User


async def is_app_admin(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(
        select(User.id).where(User.id == user_id, User.role == AppRole.ADMIN)
    )
    return result.scalar_one_or_none() is not None


async def is_group_member(
    db: AsyncSession, expense_group_id: int, user_id: int
) -> bool:
    member = await get_group_member(db, expense_group_id, user_id)
    return member is not None


async def is_group_admin(db: AsyncSession, expense_group_id: int, user_id: int) -> bool:
    member = await get_group_member(db, expense_group_id, user_id)
    return member is not None and member.role == GroupRole.ADMIN


async def get_group_member(
    db: AsyncSession, expense_group_id: int, user_id: int
) -> ExpenseGroupMember | None:
    result = await db.execute(
        select(ExpenseGroupMember).where(
            ExpenseGroupMember.expense_group_id == expense_group_id,
            ExpenseGroupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_group_admin_ids(
    db: AsyncSession, expense_group_id: int, exclude_user_id: int | None = None
) -> list[int]:
    stmt = select(ExpenseGroupMember.user_id).where(
        ExpenseGroupMember.expense_group_id == expense_group_id,
        ExpenseGroupMember.role == GroupRole.ADMIN,
    )
    if exclude_user_id is not None:
        stmt = stmt.where(ExpenseGroupMember.user_id != exclude_user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
