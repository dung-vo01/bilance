from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.common import envelope
from app.schemas.notification import NotificationOut, RespondInvitationRequest
from app.services import notification_service

router = APIRouter()


@router.get("")
async def list_notifications(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    notifications = await notification_service.get_unread(db, user_id)
    return envelope(
        [
            NotificationOut.model_validate(n).model_dump(mode="json")
            for n in notifications
        ]
    )


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.mark_read(db, notification_id, user_id)
    return envelope({"message": "Marked as read"})


@router.post("/invitations/{notification_id}/respond")
async def respond_invitation(
    notification_id: int,
    data: RespondInvitationRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await notification_service.respond_invitation(
        db, notification_id, user_id, data.accept
    )
    return envelope(
        {"message": "Invitation accepted" if data.accept else "Invitation declined"}
    )
