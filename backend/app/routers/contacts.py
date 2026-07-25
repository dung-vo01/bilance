from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.common import envelope
from app.schemas.contact import SendContactRequestPayload
from app.schemas.notification import NotificationOut
from app.schemas.user import ContactDetailOut, UserPublicOut
from app.services import contact_service, email_service

router = APIRouter()


@router.get("")
async def list_contacts(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    contacts = await contact_service.get_visible_contacts(db, user_id)
    return envelope(
        [UserPublicOut.model_validate(u).model_dump(mode="json") for u in contacts]
    )


@router.get("/detail")
async def list_contacts_detail(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    contacts = await contact_service.list_my_contacts_detailed(db, user_id)
    return envelope(
        [ContactDetailOut.model_validate(u).model_dump(mode="json") for u in contacts]
    )


@router.get("/requests/sent")
async def list_sent_requests(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    requests = await contact_service.get_sent_requests(db, user_id)
    return envelope(
        [NotificationOut.model_validate(n).model_dump(mode="json") for n in requests]
    )


@router.post("/requests", status_code=201)
async def send_contact_request(
    data: SendContactRequestPayload,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    notification = await contact_service.send_request(db, user_id, data.username)
    if notification.recipient and notification.recipient.email:
        background_tasks.add_task(
            email_service.send_contact_request_email,
            notification.recipient.email,
            notification.recipient.firstname,
            notification.recipient.username,
            (
                notification.actor.firstname or notification.actor.username
                if notification.actor
                else "Someone"
            ),
        )
    return envelope({"message": "Contact request sent"})


@router.delete("/requests/{notification_id}")
async def cancel_contact_request(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await contact_service.cancel_request(db, user_id, notification_id)
    return envelope({"message": "Request cancelled"})


@router.delete("/{contact_user_id}")
async def remove_contact(
    contact_user_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await contact_service.remove_contact(db, user_id, contact_user_id)
    return envelope({"message": "Contact removed"})
