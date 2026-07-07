from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserPublicOut


class ExpenseShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_id: int
    user_id: int
    ratio: float
    amount: float
    user: UserPublicOut | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    description: str | None = None
    value: float | None = None
    is_deleted: bool
    category_id: int | None = None
    payee_id: int | None = None
    expense_group_id: int | None = None
    created_by_id: int | None = None
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None
    shares: list[ExpenseShareOut] = []


class ExpenseShareInput(BaseModel):
    user_id: int
    ratio: float


class ExpenseCreate(BaseModel):
    name: str
    description: str | None = None
    value: float
    category_id: int | None = None
    payee_id: int | None = None
    expense_group_id: int | None = None
    paid_at: str | None = None
    shares: list[ExpenseShareInput] | None = None


class ExpenseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    value: float | None = None
    category_id: int | None = None
    is_deleted: bool | None = None
    payee_id: int | None = None
    paid_at: str | None = None
    shares: list[ExpenseShareInput] | None = None
