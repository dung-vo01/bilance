import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.db.session import async_session_factory
from app.models import (
    Category,
    Expense,
    ExpenseGroup,
    ExpenseGroupMember,
    ExpenseShare,
    GroupRole,
    User,
)

COMPANION_USERNAME = "alex.demo"


async def _get_or_create_companion(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == COMPANION_USERNAME))
    companion = result.scalar_one_or_none()
    if companion:
        return companion

    companion = User(
        username=COMPANION_USERNAME,
        firstname="Alex",
        lastname="Demo",
        email=None,
        password_hash=await hash_password(secrets.token_urlsafe(32)),
        is_email_verified=True,
    )
    db.add(companion)
    await db.flush()
    return companion


async def _seed_sample_data(db: AsyncSession, guest: User, companion: User) -> None:
    categories_result = await db.execute(
        select(Category).where(Category.is_global.is_(True)).limit(4)
    )
    categories = list(categories_result.scalars().all())
    now = datetime.now(timezone.utc)

    personal_expenses = [
        ("Groceries", 42.50, 0, 2),
        ("Dinner out", 28.00, 1, 5),
        ("Bus ticket", 55.00, 2, 8),
        ("Movie night", 18.00, 1, 11),
        ("Electricity bill", 76.40, 3, 13),
    ]
    for name, value, cat_idx, days_ago in personal_expenses:
        category = categories[cat_idx] if cat_idx < len(categories) else None
        db.add(
            Expense(
                name=name,
                value=value,
                category_id=category.id if category else None,
                payee_id=guest.id,
                created_by_id=guest.id,
                paid_at=now - timedelta(days=days_ago),
            )
        )

    group = ExpenseGroup(name="Sample Trip", created_by_id=guest.id)
    db.add(group)
    await db.flush()

    db.add(
        ExpenseGroupMember(
            user_id=guest.id,
            expense_group_id=group.id,
            role=GroupRole.ADMIN,
            default_split_ratio=0.5,
        )
    )
    db.add(
        ExpenseGroupMember(
            user_id=companion.id,
            expense_group_id=group.id,
            role=GroupRole.MEMBER,
            default_split_ratio=0.5,
        )
    )

    group_expenses = [
        ("Hotel", 140.00, 0, 3),
        ("Dinner together", 60.00, 1, 4),
    ]
    for name, value, cat_idx, days_ago in group_expenses:
        category = categories[cat_idx] if cat_idx < len(categories) else None
        expense = Expense(
            name=name,
            value=value,
            category_id=category.id if category else None,
            payee_id=guest.id,
            created_by_id=guest.id,
            expense_group_id=group.id,
            paid_at=now - timedelta(days=days_ago),
        )
        db.add(expense)
        await db.flush()
        for member_id in (guest.id, companion.id):
            db.add(
                ExpenseShare(
                    expense_id=expense.id,
                    user_id=member_id,
                    ratio=0.5,
                    amount=round(value * 0.5, 2),
                )
            )


async def create_guest(db: AsyncSession) -> tuple[User, str, str]:
    companion = await _get_or_create_companion(db)

    guest = User(
        username=f"guest_{secrets.token_hex(4)}",
        email=None,
        password_hash=await hash_password(secrets.token_urlsafe(32)),
        is_guest=True,
        is_email_verified=True,
    )
    db.add(guest)
    await db.flush()

    await _seed_sample_data(db, guest, companion)
    await db.commit()
    await db.refresh(guest)

    access_token = create_access_token(str(guest.id))
    refresh_token = create_refresh_token(str(guest.id))
    return guest, access_token, refresh_token


async def _delete_guest_ids(db: AsyncSession, user_ids: list[int]) -> None:
    if not user_ids:
        return

    group_ids = (
        (
            await db.execute(
                select(ExpenseGroup.id).where(
                    ExpenseGroup.created_by_id.in_(user_ids)
                )
            )
        )
        .scalars()
        .all()
    )

    await db.execute(
        delete(Expense).where(
            Expense.payee_id.in_(user_ids) | Expense.expense_group_id.in_(group_ids)
        )
    )

    groups_result = await db.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.id.in_(group_ids))
        .options(selectinload(ExpenseGroup.members))
    )
    for group in groups_result.scalars().all():
        await db.delete(group)

    # The app's session factory has autoflush disabled, so the ORM-tracked
    # group deletions above aren't sent to the DB until flushed - without this,
    # the raw DELETE below runs while those groups still reference the user,
    # violating the expense_groups.created_by_id FK.
    await db.flush()

    await db.execute(delete(User).where(User.id.in_(user_ids)))
    await db.commit()


async def _cleanup_expired_guests(db: AsyncSession) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=settings.GUEST_ACCOUNT_TTL_HOURS
    )
    expired_ids = (
        (
            await db.execute(
                select(User.id).where(User.is_guest.is_(True), User.created_at < cutoff)
            )
        )
        .scalars()
        .all()
    )
    await _delete_guest_ids(db, expired_ids)


async def cleanup_expired_guests() -> None:
    """Deletes guest accounts (and their owned data) older than the configured TTL.

    Runs as a fire-and-forget background task, so it opens its own DB session
    rather than reusing the request's (which is closed by the time background
    tasks run).
    """
    async with async_session_factory() as db:
        await _cleanup_expired_guests(db)


async def delete_guest_now(db: AsyncSession, user_id: int) -> None:
    """Deletes a guest's own account immediately, e.g. when they explicitly sign out."""
    user = await db.get(User, user_id)
    if not user or not user.is_guest:
        raise ForbiddenError("Not a guest account")

    await _delete_guest_ids(db, [user_id])
