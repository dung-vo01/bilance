from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models import NotificationType
from app.schemas.user import UserPublicOut


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    recipient_id: int
    actor_id: int | None = None
    actor: UserPublicOut | None = None
    recipient: UserPublicOut | None = None
    expense_group_id: int | None = None
    payload: dict | None = None
    is_read: bool
    read_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    expense_group_name: str | None = None


class RespondInvitationRequest(BaseModel):
    accept: bool = False
