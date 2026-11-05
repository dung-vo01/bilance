from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.user import UserPublicOut


class RepaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    paid_at: datetime | None = None
    note: str | None = None
    from_user_id: int
    to_user_id: int

    @model_validator(mode="after")
    def check_different_users(self):
        if self.from_user_id == self.to_user_id:
            raise ValueError("from_user_id and to_user_id must be different")

        return self


class RepaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    paid_at: datetime
    note: str | None = None
    is_deleted: bool
    deleted_at: datetime | None = None
    deleted_note: str | None = None
    created_at: datetime
    created_by: UserPublicOut
    from_user: UserPublicOut
    to_user: UserPublicOut
    deleted_by: UserPublicOut | None = None
    expense_group_id: int


class RepaymentUnresolve(BaseModel):
    deleted_note: str | None = None
