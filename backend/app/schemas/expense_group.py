from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models import GroupRole
from app.schemas.user import UserPublicOut


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    expense_group_id: int
    role: GroupRole
    default_split_ratio: float
    user: UserPublicOut | None = None


class ExpenseGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    description: str | None = None
    created_by_id: int | None = None
    members: list[MemberOut] = []
    created_at: datetime
    updated_at: datetime


class MemberInput(BaseModel):
    id: int
    role: str | None = None


class SplitRatioInput(BaseModel):
    user_id: int
    default_split_ratio: float


class ExpenseGroupCreate(BaseModel):
    name: str
    description: str | None = None
    members: list[MemberInput] = []
    split_ratios: list[SplitRatioInput] = []


class ExpenseGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class InviteMemberInput(BaseModel):
    username: str
    default_split_ratio: float = 0


class InviteRequest(BaseModel):
    members: list[InviteMemberInput]


class MemberUpdate(BaseModel):
    default_split_ratio: float | None = None
    role: str | None = None


class BulkMemberUpdateItem(BaseModel):
    user_id: int
    default_split_ratio: float | None = None
    role: str | None = None


class BulkMemberUpdateRequest(BaseModel):
    members: list[BulkMemberUpdateItem] = []
