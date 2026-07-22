import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.expense_group import ExpenseGroup
    from app.models.user import User


class NotificationType(str, enum.Enum):
    GROUP_INVITATION = "group_invitation"
    INVITATION_ACCEPTED = "invitation_accepted"
    INVITATION_DECLINED = "invitation_declined"
    MEMBER_REMOVED = "member_removed"
    MEMBER_LEFT = "member_left"
    MEMBERS_INVITED = "members_invited"
    CONTACT_REQUEST = "contact_request"
    CONTACT_ACCEPTED = "contact_accepted"
    CONTACT_DECLINED = "contact_declined"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient_unread", "recipient_id", "is_read"),
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notificationtype"), nullable=False
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    expense_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("expense_groups.id", ondelete="CASCADE")
    )
    payload: Mapped[dict | None] = mapped_column(JSON)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_id])
    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_id])
    expense_group: Mapped["ExpenseGroup | None"] = relationship(
        foreign_keys=[expense_group_id]
    )

    @property
    def expense_group_name(self) -> str | None:
        return self.expense_group.name if self.expense_group else None
