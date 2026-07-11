from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.common import envelope
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.schemas.user import UserPublicOut
from app.services import expense_service

router = APIRouter()


@router.get("")
async def list_expenses(
    expense_group_id: int | None = Query(None),
    status: Literal["all", "active", "deleted"] = Query("all"),
    search_kw: str | None = Query(None),
    category_id: int | None = Query(None),
    no_category: bool = Query(False),
    payee_id: int | None = Query(None),
    sort_by: Literal["name", "paid_at", "created_at", "value"] = Query("paid_at"),
    sort_dir: Literal["asc", "desc"] = Query("desc"),
    page: int | None = Query(None, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    expenses, total, total_value = await expense_service.get_all(
        db,
        user_id,
        expense_group_id,
        status=status,
        search_kw=search_kw,
        category_id=category_id,
        no_category=no_category,
        payee_id=payee_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    items = [ExpenseOut.model_validate(e).model_dump(mode="json") for e in expenses]

    if page is None:
        return envelope(items)

    return envelope(
        {
            "items": items,
            "total": total,
            "total_value": total_value,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if page_size else 0,
        }
    )


@router.get("/payees")
async def list_payees(
    expense_group_id: int = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    payees = await expense_service.get_distinct_payees(db, user_id, expense_group_id)
    return envelope(
        [UserPublicOut.model_validate(u).model_dump(mode="json") for u in payees]
    )


@router.get("/category-breakdown")
async def category_breakdown(
    days: int = Query(30, ge=1, le=365),
    expense_group_id: int | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await expense_service.get_category_breakdown(
        db, user_id, days, expense_group_id
    )
    return envelope(data)


@router.post("", status_code=201)
async def create_personal(
    data: ExpenseCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    expense = await expense_service.create(db, user_id, data)
    return envelope(ExpenseOut.model_validate(expense).model_dump(mode="json"))


@router.patch("/{expense_id}")
async def update_personal(
    expense_id: int,
    data: ExpenseUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    expense = await expense_service.update(db, expense_id, user_id, data)
    return envelope(ExpenseOut.model_validate(expense).model_dump(mode="json"))


@router.delete("/{expense_id}")
async def delete_personal(
    expense_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await expense_service.delete(db, expense_id, user_id)
    return envelope({"message": "Expense deleted"})
