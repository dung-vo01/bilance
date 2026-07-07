from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.common import envelope
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.services import expense_service

router = APIRouter()


@router.get("")
async def list_expenses(
    expense_group_id: int | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    expenses = await expense_service.get_all(db, user_id, expense_group_id)
    return envelope([ExpenseOut.model_validate(e).model_dump(mode="json") for e in expenses])


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
