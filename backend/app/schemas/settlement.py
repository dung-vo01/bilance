from pydantic import BaseModel


class MemberBalance(BaseModel):
    user_id: int
    username: str | None = None
    paid: float
    should_pay: float
    balance: float


class Transaction(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: float


class PendingExpense(BaseModel):
    id: int
    value: float
    payee_id: int | None = None
    name: str | None = None
    description: str | None = None


class SettlementOut(BaseModel):
    expense_group_id: int
    members: list[MemberBalance]
    transactions: list[Transaction]
    pending_expenses: list[PendingExpense]
    pending_total: float
    settled_total: float
    total: float
