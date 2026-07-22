from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.common import envelope
from app.schemas.contact import SendContactRequestPayload
from app.schemas.user import UserPublicOut
from app.services import contact_service

router = APIRouter()


@router.get("")
async def list_contacts(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    contacts = await contact_service.get_visible_contacts(db, user_id)
    return envelope(
        [UserPublicOut.model_validate(u).model_dump(mode="json") for u in contacts]
    )


@router.post("/requests", status_code=201)
async def send_contact_request(
    data: SendContactRequestPayload,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await contact_service.send_request(db, user_id, data.username)
    return envelope({"message": "Contact request sent"})
