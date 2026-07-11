from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import is_app_admin, is_group_member
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models import Category, Expense, ExpenseShare, User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

_DETAIL_LOADERS = (
    selectinload(Expense.shares).selectinload(ExpenseShare.user),
    selectinload(Expense.payee),
)

_SORT_COLUMNS = {
    "name": Expense.name,
    "paid_at": Expense.paid_at,
    "created_at": Expense.created_at,
    "value": Expense.value,
}


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def get_all(
    db: AsyncSession,
    user_id: int,
    expense_group_id: int | None,
    status: str = "all",
    search_kw: str | None = None,
    category_id: int | None = None,
    no_category: bool = False,
    payee_id: int | None = None,
    sort_by: str = "paid_at",
    sort_dir: str = "desc",
    page: int | None = None,
    page_size: int = 10,
) -> tuple[list[Expense], int, float]:
    if expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")
        filters = [Expense.expense_group_id == expense_group_id]
    else:
        filters = [
            Expense.payee_id == user_id,
            Expense.expense_group_id.is_(None),
        ]

    if status == "active":
        filters.append(Expense.is_deleted.is_(False))
    elif status == "deleted":
        filters.append(Expense.is_deleted.is_(True))

    if no_category:
        filters.append(Expense.category_id.is_(None))
    elif category_id is not None:
        filters.append(Expense.category_id == category_id)
    if payee_id is not None:
        filters.append(Expense.payee_id == payee_id)
    if search_kw:
        kw = f"%{_escape_like(search_kw)}%"
        filters.append(
            or_(
                Expense.name.ilike(kw, escape="\\"),
                Expense.description.ilike(kw, escape="\\"),
            )
        )

    total = (
        await db.execute(select(func.count(Expense.id)).where(*filters))
    ).scalar_one()
    total_value = (
        await db.execute(
            select(func.coalesce(func.sum(Expense.value), 0.0)).where(*filters)
        )
    ).scalar_one()

    sort_column = _SORT_COLUMNS.get(sort_by, Expense.paid_at)
    order = (
        sort_column.asc() if sort_dir == "asc" else sort_column.desc()
    ).nulls_last()

    stmt = (
        select(Expense)
        .where(*filters)
        .options(*_DETAIL_LOADERS)
        .order_by(order, Expense.id.desc())
    )

    if page is not None:
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total, float(total_value)


async def get_distinct_payees(
    db: AsyncSession, user_id: int, expense_group_id: int
) -> list[User]:
    if not await is_app_admin(db, user_id) and not await is_group_member(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Not a member of this group")

    result = await db.execute(
        select(User)
        .join(Expense, Expense.payee_id == User.id)
        .where(Expense.expense_group_id == expense_group_id)
        .distinct()
    )
    return list(result.scalars().all())


async def get_category_breakdown(
    db: AsyncSession,
    user_id: int,
    days: int,
    expense_group_id: int | None = None,
) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    if expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")
        scope_filter = Expense.expense_group_id == expense_group_id
    else:
        scope_filter = (Expense.payee_id == user_id) & Expense.expense_group_id.is_(
            None
        )

    stmt = (
        select(
            Expense.category_id,
            Category.name,
            func.sum(Expense.value),
        )
        .outerjoin(Category, Category.id == Expense.category_id)
        .where(
            scope_filter,
            Expense.is_deleted.is_(False),
            Expense.paid_at.is_not(None),
            Expense.paid_at >= cutoff,
        )
        .group_by(Expense.category_id, Category.name)
        .order_by(func.sum(Expense.value).desc())
    )
    rows = (await db.execute(stmt)).all()

    total = sum(row[2] for row in rows)
    categories = [
        {
            "category_id": category_id,
            "category_name": name or "No category",
            "total": float(value),
            "percentage": round(value / total * 100, 2) if total else 0.0,
        }
        for category_id, name, value in rows
    ]

    return {"period_days": days, "total": float(total), "categories": categories}


def _validate_ratios_sum_to_one(shares: list) -> None:
    total = round(sum(s.ratio for s in shares), 10)
    if abs(total - 1.0) > 0.001:
        raise AppError(f"Share ratios must sum to 100% (got {round(total * 100, 1)}%)")


async def _reload(db: AsyncSession, expense_id: int) -> Expense:
    result = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id)
        .options(*_DETAIL_LOADERS)
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
        select(Expense).where(Expense.id == expense_id).options(*_DETAIL_LOADERS)
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
