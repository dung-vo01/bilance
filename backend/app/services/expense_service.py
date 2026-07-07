from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import is_app_admin, is_group_member
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models import Expense, ExpenseShare
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

_SHARES_LOADER = selectinload(Expense.shares).selectinload(ExpenseShare.user)


async def get_all(
    db: AsyncSession, user_id: int, expense_group_id: int | None
) -> list[Expense]:
    if expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")

        result = await db.execute(
            select(Expense)
            .where(Expense.expense_group_id == expense_group_id)
            .options(_SHARES_LOADER)
        )
    else:
        result = await db.execute(
            select(Expense)
            .where(Expense.payee_id == user_id, Expense.expense_group_id.is_(None))
            .options(_SHARES_LOADER)
        )

    return list(result.scalars().all())


def _validate_ratios_sum_to_one(shares: list) -> None:
    total = round(sum(s.ratio for s in shares), 10)
    if abs(total - 1.0) > 0.001:
        raise AppError(f"Share ratios must sum to 100% (got {round(total * 100, 1)}%)")


async def _reload(db: AsyncSession, expense_id: int) -> Expense:
    result = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id)
        .options(_SHARES_LOADER)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


# Handle creating both personal and group expenses
async def create(db: AsyncSession, user_id: int, data: ExpenseCreate) -> Expense:
    expense_group_id = data.expense_group_id

    if (
        expense_group_id
        and not await is_app_admin(db, user_id)
        and not await is_group_member(db, expense_group_id, user_id)
    ):
        raise ForbiddenError("Not a member of this group")

    if not data.name:
        raise AppError("Name and value are required")
    if not data.value:
        raise AppError("Value are required")

    # payee is the one who paid, default to current user if not provided
    payee_id = data.payee_id or user_id

    if expense_group_id and not await is_group_member(db, expense_group_id, payee_id):
        raise AppError("Payee is not a member of this group")

    expense = Expense(
        name=data.name,
        description=data.description,
        value=data.value,
        category_id=data.category_id,
        payee_id=payee_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        paid_at=datetime.fromisoformat(data.paid_at) if data.paid_at else None,
    )
    db.add(expense)
    await db.flush()

    if expense_group_id:
        expense.expense_group_id = expense_group_id

        if data.shares:
            _validate_ratios_sum_to_one(data.shares)
            for s in data.shares:
                db.add(
                    ExpenseShare(
                        expense_id=expense.id,
                        user_id=s.user_id,
                        ratio=s.ratio,
                        amount=round(expense.value * s.ratio, 2),
                    )
                )

    await db.commit()

    return await _reload(db, expense.id)


async def _get_authorized(
    db: AsyncSession, expense_id: int, user_id: int, action: str
) -> Expense:
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id).options(_SHARES_LOADER)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("Expense not found")

    if expense.expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense.expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")
    elif not await is_app_admin(db, user_id) and expense.payee_id != user_id:
        raise ForbiddenError(f"Not authorized to {action} this expense")

    return expense


async def update(
    db: AsyncSession, expense_id: int, user_id: int, data: ExpenseUpdate
) -> Expense:
    expense = await _get_authorized(db, expense_id, user_id, "update")

    payload = data.model_dump(exclude_unset=True)

    for field in (
        "name",
        "description",
        "value",
        "category_id",
        "is_deleted",
        "payee_id",
    ):
        if field in payload:
            setattr(expense, field, payload[field])

    if "paid_at" in payload:
        expense.paid_at = (
            datetime.fromisoformat(payload["paid_at"]) if payload["paid_at"] else None
        )

    if "shares" in payload:
        shares = data.shares
        _validate_ratios_sum_to_one(shares)

        # Clear existing shares and rebuilds with those provided in payload
        expense.shares.clear()
        await db.flush()
        for s in shares:
            expense.shares.append(
                ExpenseShare(
                    user_id=s.user_id,
                    ratio=s.ratio,
                    amount=round(expense.value * s.ratio, 2),
                )
            )
    elif "value" in payload:
        # value changed but shares not provided => recalculate amounts
        for share in expense.shares:
            share.amount = round(payload["value"] * share.ratio, 2)

    expense.updated_by_id = user_id

    await db.commit()

    return await _reload(db, expense_id)


async def delete(db: AsyncSession, expense_id: int, user_id: int) -> None:
    expense = await _get_authorized(db, expense_id, user_id, "delete")

    expense.is_deleted = True
    expense.updated_by_id = user_id

    await db.commit()
