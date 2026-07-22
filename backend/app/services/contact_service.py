from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models import Contact, ExpenseGroupMember, Notification, NotificationType, User


async def send_request(
    db: AsyncSession, user_id: int, username: str | None
) -> Notification:
    if not username:
        raise AppError("Username is required")

    result = await db.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("User not found")

    if target.id == user_id:
        raise AppError("You can't add yourself as a contact")

    existing_contact = await db.execute(
        select(Contact).where(
            Contact.user_id == user_id, Contact.contact_id == target.id
        )
    )
    if existing_contact.scalar_one_or_none():
        raise ConflictError("Already connected with this user")

    pending = await db.execute(
        select(Notification).where(
            Notification.type == NotificationType.CONTACT_REQUEST,
            Notification.resolved_at.is_(None),
            (
                (Notification.actor_id == user_id)
                & (Notification.recipient_id == target.id)
            )
            | (
                (Notification.actor_id == target.id)
                & (Notification.recipient_id == user_id)
            ),
        )
    )
    if pending.scalar_one_or_none():
        raise ConflictError("A contact request is already pending with this user")

    notification = Notification(
        type=NotificationType.CONTACT_REQUEST,
        recipient_id=target.id,
        actor_id=user_id,
    )
    db.add(notification)
    await db.commit()

    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification.id)
        .options(selectinload(Notification.actor))
    )
    return result.scalar_one()


async def get_visible_contacts(db: AsyncSession, user_id: int) -> list[User]:
    accepted_ids = select(Contact.contact_id).where(Contact.user_id == user_id)

    m1 = aliased(ExpenseGroupMember)
    m2 = aliased(ExpenseGroupMember)
    shared_group_ids = (
        select(m2.user_id)
        .join(m1, m1.expense_group_id == m2.expense_group_id)
        .where(m1.user_id == user_id, m2.user_id != user_id)
    )

    visible_ids = accepted_ids.union(shared_group_ids).subquery()

    result = await db.execute(select(User).where(User.id.in_(select(visible_ids))))
    return list(result.scalars().all())
