from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    is_global: bool
    created_by_id: int | None = None
    expense_group_id: int | None = None


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    expense_group_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
