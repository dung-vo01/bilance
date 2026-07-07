import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.user import User


class GroupRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class ExpenseGroup(Base, TimestampMixin):
    __tablename__ = "expense_groups"

    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])

    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])

    members: Mapped[list["ExpenseGroupMember"]] = relationship(
        back_populates="expense_group", cascade="all, delete-orphan"
    )


class ExpenseGroupMember(Base):
    __tablename__ = "expense_group_members"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    expense_group_id: Mapped[int] = mapped_column(
        ForeignKey("expense_groups.id"), primary_key=True
    )
    role: Mapped[GroupRole] = mapped_column(
        Enum(GroupRole, name="grouprole"), default=GroupRole.MEMBER
    )
    default_split_ratio: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    expense_group: Mapped["ExpenseGroup"] = relationship(
        foreign_keys=[expense_group_id], back_populates="members"
    )
