from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import (
    get_group_admin_ids,
    is_app_admin,
    is_group_admin,
    is_group_member,
)
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models import (
    ExpenseGroup,
    ExpenseGroupMember,
    GroupRole,
    Notification,
    NotificationType,
    User,
)
from app.schemas.expense_group import (
    BulkMemberUpdateItem,
    ExpenseGroupCreate,
    ExpenseGroupUpdate,
    InviteMemberInput,
    MemberUpdate,
)

_MEMBERS_LOADER = selectinload(ExpenseGroup.members).selectinload(
    ExpenseGroupMember.user
)


async def _get_group_with_members(
    db: AsyncSession, expense_group_id: int
) -> ExpenseGroup | None:
    result = await db.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.id == expense_group_id)
        .options(_MEMBERS_LOADER)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def get_user_expense_groups(db: AsyncSession, user_id: int) -> list[ExpenseGroup]:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    result = await db.execute(
        select(ExpenseGroup)
        .join(
            ExpenseGroupMember, ExpenseGroupMember.expense_group_id == ExpenseGroup.id
        )
        .where(ExpenseGroupMember.user_id == user_id)
        .options(_MEMBERS_LOADER)
    )
    return list(result.scalars().unique().all())


async def create(
    db: AsyncSession, user_id: int, data: ExpenseGroupCreate
) -> ExpenseGroup:
    if not data.name:
        raise AppError("Expense group name is required")

    expense_group = ExpenseGroup(
        name=data.name,
        description=data.description,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    db.add(expense_group)
    await db.flush()

    # creator is automatically admin
    group_admin = ExpenseGroupMember(
        user_id=user_id,
        expense_group_id=expense_group.id,
        role=GroupRole.ADMIN,
    )
    db.add(group_admin)
    all_members = [group_admin]

    # add members to group
    for member_data in data.members:
        member = ExpenseGroupMember(
            user_id=member_data.id,
            expense_group_id=expense_group.id,
            role=(
                GroupRole(member_data.role.lower())
                if member_data.role
                else GroupRole.MEMBER
            ),
        )
        db.add(member)
        all_members.append(member)

    # calculate split ratios
    if data.split_ratios:
        by_user = {sr.user_id: sr.default_split_ratio for sr in data.split_ratios}
        for member in all_members:
            if member.user_id in by_user:
                member.default_split_ratio = float(by_user[member.user_id])
    else:
        # If no split ratios provided, split evenly
        default_split_ratio = 1 / len(all_members) if len(all_members) > 1 else 1
        for member in all_members:
            member.default_split_ratio = float(default_split_ratio)

    await db.commit()

    return await _get_group_with_members(db, expense_group.id)


async def get(db: AsyncSession, expense_group_id: int, user_id: int) -> ExpenseGroup:
    group = await _get_group_with_members(db, expense_group_id)
    if not group:
        raise NotFoundError("Group not found")

    if not await is_app_admin(db, user_id) and not await is_group_member(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Not a member of this group")

    return group


async def update(
    db: AsyncSession, expense_group_id: int, user_id: int, data: ExpenseGroupUpdate
) -> ExpenseGroup:
    group = await db.get(ExpenseGroup, expense_group_id)
    if not group:
        raise NotFoundError("Group not found")

    if not await is_app_admin(db, user_id) and not await is_group_admin(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Only admin can update the group")

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    group.updated_by_id = user_id

    await db.commit()

    return await _get_group_with_members(db, expense_group_id)


async def delete(db: AsyncSession, expense_group_id: int, user_id: int) -> None:
    group = await db.get(ExpenseGroup, expense_group_id)
    if not group:
        raise NotFoundError("Group not found")

    if not await is_app_admin(db, user_id) and not await is_group_admin(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Only admin can delete the group")

    await db.delete(group)
    await db.commit()


async def invite(
    db: AsyncSession,
    expense_group_id: int,
    user_id: int,
    members: list[InviteMemberInput],
) -> list[Notification]:
    if not await is_app_admin(db, user_id) and not await is_group_admin(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Only admin can invite members")

    new_notifications = []
    invited_users_info = []
    for member_payload in members:
        result = await db.execute(
            select(User).where(User.username == member_payload.username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")

        # Skip if already a member
        if await is_group_member(db, expense_group_id, user.id):
            continue

        # Skip if there already an unresolved invitation for this user+group
        existing = await db.execute(
            select(Notification).where(
                Notification.type == NotificationType.GROUP_INVITATION,
                Notification.recipient_id == user.id,
                Notification.expense_group_id == expense_group_id,
                Notification.resolved_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            continue

        notification = Notification(
            type=NotificationType.GROUP_INVITATION,
            recipient_id=user.id,
            actor_id=user_id,
            expense_group_id=expense_group_id,
            payload={"default_split_ratio": float(member_payload.default_split_ratio)},
        )
        db.add(notification)
        new_notifications.append(notification)
        invited_users_info.append(
            {
                "username": user.username,
                "firstname": user.firstname,
                "lastname": user.lastname,
            }
        )

    # Inform other admins about who got invited
    if invited_users_info:
        admin_ids = await get_group_admin_ids(
            db, expense_group_id, exclude_user_id=user_id
        )
        for admin_id in admin_ids:
            db.add(
                Notification(
                    type=NotificationType.MEMBERS_INVITED,
                    recipient_id=admin_id,
                    actor_id=user_id,
                    expense_group_id=expense_group_id,
                    payload={"invited_users": invited_users_info},
                )
            )

    await db.commit()

    ids = [n.id for n in new_notifications]
    if not ids:
        return []

    result = await db.execute(
        select(Notification)
        .where(Notification.id.in_(ids))
        .options(
            selectinload(Notification.actor),
            selectinload(Notification.recipient),
            selectinload(Notification.expense_group),
        )
    )
    return list(result.scalars().all())


async def leave(db: AsyncSession, expense_group_id: int, user_id: int) -> None:
    if await is_group_admin(db, expense_group_id, user_id):
        result = await db.execute(
            select(ExpenseGroupMember).where(
                ExpenseGroupMember.expense_group_id == expense_group_id,
                ExpenseGroupMember.role == GroupRole.ADMIN,
                ExpenseGroupMember.user_id != user_id,
            )
        )
        other_admins = len(result.scalars().all())
        if other_admins == 0:
            raise AppError(
                "You are the only admin, please assign another admin before leaving"
            )

    result = await db.execute(
        select(ExpenseGroupMember).where(
            ExpenseGroupMember.expense_group_id == expense_group_id,
            ExpenseGroupMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member not found")

    admin_ids = await get_group_admin_ids(db, expense_group_id, exclude_user_id=user_id)
    for admin_id in admin_ids:
        db.add(
            Notification(
                type=NotificationType.MEMBER_LEFT,
                recipient_id=admin_id,
                actor_id=user_id,
                expense_group_id=expense_group_id,
            )
        )

    await db.delete(member)
    await db.commit()


async def update_member(
    db: AsyncSession,
    expense_group_id: int,
    current_user_id: int,
    member_user_id: int,
    data: MemberUpdate,
) -> ExpenseGroupMember:
    is_admin = await is_group_admin(db, expense_group_id, current_user_id)

    if not is_admin and current_user_id != member_user_id:
        raise ForbiddenError("Not authorized to update this member")

    result = await db.execute(
        select(ExpenseGroupMember)
        .where(
            ExpenseGroupMember.expense_group_id == expense_group_id,
            ExpenseGroupMember.user_id == member_user_id,
        )
        .options(selectinload(ExpenseGroupMember.user))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member not found")

    if data.default_split_ratio is not None:
        if data.default_split_ratio < 0 or data.default_split_ratio > 1:
            raise AppError("Ratio must be between 0 and 1")
        member.default_split_ratio = data.default_split_ratio

    if data.role is not None and is_admin:
        member.role = GroupRole(data.role.lower())

    await db.commit()
    await db.refresh(member, attribute_names=["user"])

    return member


async def bulk_update_members(
    db: AsyncSession,
    expense_group_id: int,
    current_user_id: int,
    members: list[BulkMemberUpdateItem],
) -> list[ExpenseGroupMember]:
    is_admin = await is_group_admin(db, expense_group_id, current_user_id)

    updated = []
    for m in members:
        result = await db.execute(
            select(ExpenseGroupMember).where(
                ExpenseGroupMember.expense_group_id == expense_group_id,
                ExpenseGroupMember.user_id == m.user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            continue

        can_edit_own = member.user_id == current_user_id
        can_edit_others = is_admin and member.user_id != current_user_id

        if not can_edit_own and not can_edit_others:
            continue

        if m.default_split_ratio is not None:
            member.default_split_ratio = m.default_split_ratio

        if m.role is not None and is_admin and member.user_id != current_user_id:
            member.role = GroupRole(m.role.lower())

        updated.append(member)

    # sanity check — at least one admin must remain
    all_members_result = await db.execute(
        select(ExpenseGroupMember).where(
            ExpenseGroupMember.expense_group_id == expense_group_id
        )
    )
    all_members = all_members_result.scalars().all()
    admin_count = sum(1 for m in all_members if m.role == GroupRole.ADMIN)
    if admin_count == 0:
        raise AppError("There must be at least one admin in the group")

    await db.commit()

    for member in updated:
        await db.refresh(member, attribute_names=["user"])

    return updated


async def remove_members(
    db: AsyncSession, expense_group_id: int, user_id: int, member_ids: list[int]
) -> None:
    if not await is_app_admin(db, user_id) and not await is_group_admin(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Only admin can remove members")

    for member_id in member_ids:
        if await is_group_admin(db, expense_group_id, user_id) and user_id == member_id:
            raise AppError("Admin cannot remove themselves")

        result = await db.execute(
            select(ExpenseGroupMember)
            .where(
                ExpenseGroupMember.expense_group_id == expense_group_id,
                ExpenseGroupMember.user_id == member_id,
            )
            .options(selectinload(ExpenseGroupMember.user))
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Member not found")

        db.add(
            Notification(
                type=NotificationType.MEMBER_REMOVED,
                recipient_id=member_id,
                actor_id=user_id,
                expense_group_id=expense_group_id,
            )
        )

        # Other admins should also know a member was removed, and by whom.
        admin_ids = await get_group_admin_ids(
            db, expense_group_id, exclude_user_id=user_id
        )
        for admin_id in admin_ids:
            if admin_id == member_id:
                continue
            db.add(
                Notification(
                    type=NotificationType.MEMBER_REMOVED,
                    recipient_id=admin_id,
                    actor_id=user_id,
                    expense_group_id=expense_group_id,
                    payload={
                        "removed_user_id": member_id,
                        "removed_user": (
                            {
                                "username": member.user.username,
                                "firstname": member.user.firstname,
                                "lastname": member.user.lastname,
                            }
                            if member.user
                            else None
                        ),
                    },
                )
            )

        await db.delete(member)

    await db.commit()
