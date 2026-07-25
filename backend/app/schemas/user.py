from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models import AppRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    role: AppRole
    is_active: bool
    is_email_verified: bool
    is_guest: bool
    phone_number: str | None = None
    created_at: datetime


class UserPublicOut(BaseModel):
    # Same as UserOut but omits email
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    firstname: str | None = None
    lastname: str | None = None
    role: AppRole
    is_active: bool
    phone_number: str | None = None
    created_at: datetime


class SharedGroupRef(BaseModel):
    id: int
    name: str | None = None


class ContactDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone_number: str | None = None
    created_at: datetime
    shared_groups: list[SharedGroupRef] = []


class UserCreate(BaseModel):
    username: str
    email: str
    password: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone_number: str | None = None
    role: AppRole | None = None


class UserUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    phone_number: str | None = None
    role: AppRole | None = None
    is_active: bool | None = None
