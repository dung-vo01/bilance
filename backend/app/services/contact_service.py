from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.models import (
    Contact,
    ExpenseGroup,
    ExpenseGroupMember,
    Notification,
    NotificationType,
    User,
)


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
        .options(selectinload(Notification.actor), selectinload(Notification.recipient))
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


async def list_my_contacts_detailed(db: AsyncSession, user_id: int) -> list[User]:
    contact_ids_result = await db.execute(
        select(Contact.contact_id).where(Contact.user_id == user_id)
    )
    contact_ids = list(contact_ids_result.scalars().all())
    if not contact_ids:
        return []

    users_result = await db.execute(select(User).where(User.id.in_(contact_ids)))
    users = list(users_result.scalars().all())

    m1 = aliased(ExpenseGroupMember)
    m2 = aliased(ExpenseGroupMember)
    shared_result = await db.execute(
        select(m2.user_id, ExpenseGroup.id, ExpenseGroup.name)
        .select_from(m1)
        .join(m2, m1.expense_group_id == m2.expense_group_id)
        .join(ExpenseGroup, ExpenseGroup.id == m1.expense_group_id)
        .where(m1.user_id == user_id, m2.user_id.in_(contact_ids))
    )
    groups_by_contact: dict[int, list[dict]] = {}
    for other_id, group_id, group_name in shared_result.all():
        groups_by_contact.setdefault(other_id, []).append(
            {"id": group_id, "name": group_name}
        )

    for u in users:
        u.shared_groups = groups_by_contact.get(u.id, [])

    return users


async def get_sent_requests(db: AsyncSession, user_id: int) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(
            Notification.type == NotificationType.CONTACT_REQUEST,
            Notification.actor_id == user_id,
            Notification.resolved_at.is_(None),
        )
        .options(selectinload(Notification.recipient))
        .order_by(Notification.created_at.desc())
    )
    return list(result.scalars().all())


async def cancel_request(db: AsyncSession, user_id: int, notification_id: int) -> None:
    notification = await db.get(Notification, notification_id)
    if not notification or notification.type != NotificationType.CONTACT_REQUEST:
        raise NotFoundError("Request not found")
    if notification.actor_id != user_id:
        raise ForbiddenError("Not your request")
    if notification.resolved_at is not None:
        raise AppError("Request already resolved")

    await db.delete(notification)
    await db.commit()


async def remove_contact(db: AsyncSession, user_id: int, contact_user_id: int) -> None:
    result = await db.execute(
        select(Contact).where(
            ((Contact.user_id == user_id) & (Contact.contact_id == contact_user_id))
            | ((Contact.user_id == contact_user_id) & (Contact.contact_id == user_id))
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise NotFoundError("Not a contact")

    for row in rows:
        await db.delete(row)
    await db.commit()
