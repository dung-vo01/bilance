from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import get_group_admin_ids, is_group_member
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models import (
    Contact,
    ExpenseGroupMember,
    GroupRole,
    Notification,
    NotificationType,
)

_LOADER = (selectinload(Notification.actor), selectinload(Notification.expense_group))


async def get_unread(db: AsyncSession, user_id: int) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == user_id, Notification.is_read.is_(False))
        .options(*_LOADER)
        .order_by(Notification.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_owned(
    db: AsyncSession, notification_id: int, user_id: int
) -> Notification:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id).options(*_LOADER)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Notification not found")
    if notification.recipient_id != user_id:
        raise ForbiddenError("Not your notification")
    return notification


async def _reload(db: AsyncSession, notification_id: int) -> Notification:
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .options(*_LOADER)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def mark_read(
    db: AsyncSession, notification_id: int, user_id: int
) -> Notification:
    notification = await _get_owned(db, notification_id, user_id)

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)

    await db.commit()

    return await _reload(db, notification_id)


async def respond_invitation(
    db: AsyncSession, notification_id: int, user_id: int, accept: bool
) -> Notification:
    notification = await _get_owned(db, notification_id, user_id)

    if notification.type != NotificationType.GROUP_INVITATION:
        raise AppError("Not an invitation")

    if notification.resolved_at is not None:
        raise AppError("Invitation already resolved")

    if accept:
        already_member = await is_group_member(
            db, notification.expense_group_id, user_id
        )
        if not already_member:
            payload = notification.payload or {}
            db.add(
                ExpenseGroupMember(
                    user_id=user_id,
                    expense_group_id=notification.expense_group_id,
                    role=GroupRole.MEMBER,
                    default_split_ratio=float(payload.get("default_split_ratio", 0)),
                )
            )

    now = datetime.now(timezone.utc)
    notification.resolved_at = now
    notification.is_read = True
    notification.read_at = now

    # Let every current admin of the group know how the invitation was
    # resolved (not just whichever admin happened to send it)
    admin_ids = await get_group_admin_ids(
        db, notification.expense_group_id, exclude_user_id=user_id
    )
    for admin_id in admin_ids:
        db.add(
            Notification(
                type=(
                    NotificationType.INVITATION_ACCEPTED
                    if accept
                    else NotificationType.INVITATION_DECLINED
                ),
                recipient_id=admin_id,
                actor_id=user_id,
                expense_group_id=notification.expense_group_id,
            )
        )

    await db.commit()

    return await _reload(db, notification_id)


async def respond_contact_request(
    db: AsyncSession, notification_id: int, user_id: int, accept: bool
) -> Notification:
    notification = await _get_owned(db, notification_id, user_id)

    if notification.type != NotificationType.CONTACT_REQUEST:
        raise AppError("Not a contact request")

    if notification.resolved_at is not None:
        raise AppError("Contact request already resolved")

    requester_id = notification.actor_id

    if accept and requester_id is not None:
        db.add(Contact(user_id=user_id, contact_id=requester_id))
        db.add(Contact(user_id=requester_id, contact_id=user_id))

    now = datetime.now(timezone.utc)
    notification.resolved_at = now
    notification.is_read = True
    notification.read_at = now

    if requester_id is not None:
        db.add(
            Notification(
                type=(
                    NotificationType.CONTACT_ACCEPTED
                    if accept
                    else NotificationType.CONTACT_DECLINED
                ),
                recipient_id=requester_id,
                actor_id=user_id,
            )
        )

    await db.commit()

    return await _reload(db, notification_id)
