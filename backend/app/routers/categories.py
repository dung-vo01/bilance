from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import envelope
from app.services import category_service

router = APIRouter()


@router.get("")
async def list_categories(
    expense_group_id: int | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    categories = await category_service.get_all(db, user_id, expense_group_id)
    return envelope(
        [CategoryOut.model_validate(c).model_dump(mode="json") for c in categories]
    )


@router.post("", status_code=201)
async def create_category(
    data: CategoryCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.create(db, user_id, data)
    return envelope(CategoryOut.model_validate(category).model_dump(mode="json"))


@router.patch("/{category_id}")
async def patch_category(
    category_id: int,
    data: CategoryUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.update(db, category_id, user_id, data)
    return envelope(CategoryOut.model_validate(category).model_dump(mode="json"))


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await category_service.delete(db, category_id, user_id)
    return envelope({"message": "Category deleted"})
