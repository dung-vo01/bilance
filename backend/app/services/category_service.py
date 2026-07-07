from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import is_app_admin, is_group_member
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_all(
    db: AsyncSession, user_id: int, expense_group_id: int | None = None
) -> list[Category]:
    if expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")

        stmt = select(Category).where(
            or_(
                Category.is_global.is_(True),
                Category.expense_group_id == expense_group_id,
            )
        )
    else:
        stmt = select(Category).where(
            or_(
                Category.is_global.is_(True),
                and_(
                    Category.created_by_id == user_id,
                    Category.expense_group_id.is_(None),
                ),
            )
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, user_id: int, data: CategoryCreate) -> Category:
    if not data.name:
        raise AppError("Category name is required")

    expense_group_id = data.expense_group_id

    if expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, expense_group_id, user_id
        ):
            raise ForbiddenError("Not a member of this group")

        duplicate = await db.execute(
            select(Category).where(
                Category.name == data.name,
                Category.expense_group_id == expense_group_id,
            )
        )
        if duplicate.scalar_one_or_none():
            raise ConflictError("Category already exists in this group")

        category = Category(
            name=data.name,
            description=data.description,
            is_global=False,
            expense_group_id=expense_group_id,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
    else:
        duplicate = await db.execute(
            select(Category).where(
                Category.name == data.name,
                Category.created_by_id == user_id,
                Category.expense_group_id.is_(None),
            )
        )
        if duplicate.scalar_one_or_none():
            raise ConflictError("Category already exists")

        category = Category(
            name=data.name,
            description=data.description,
            is_global=False,
            created_by_id=user_id,
            updated_by_id=user_id,
        )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category


async def _get_authorized(
    db: AsyncSession, category_id: int, user_id: int, global_action: str = "update"
) -> Category:
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundError("Category not found")

    if category.is_global and not await is_app_admin(db, user_id):
        raise ForbiddenError(f"Cannot {global_action} global categories")

    if category.expense_group_id:
        if not await is_app_admin(db, user_id) and not await is_group_member(
            db, category.expense_group_id, user_id
        ):
            raise ForbiddenError("Unauthorized")
    elif not await is_app_admin(db, user_id) and category.created_by_id != user_id:
        raise ForbiddenError("Unauthorized")

    return category


async def update(
    db: AsyncSession, category_id: int, user_id: int, data: CategoryUpdate
) -> Category:
    category = await _get_authorized(db, category_id, user_id)

    if data.name is not None:
        category.name = data.name
    if data.description is not None:
        category.description = data.description
    category.updated_by_id = user_id

    await db.commit()
    await db.refresh(category)

    return category


async def delete(db: AsyncSession, category_id: int, user_id: int) -> None:
    category = await _get_authorized(db, category_id, user_id, global_action="delete")

    await db.delete(category)
    await db.commit()
