from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_internal_secret
from app.db.session import get_db
from app.schemas.common import envelope
from app.services import guest_service

router = APIRouter()


@router.post("/cleanup-guests", dependencies=[Depends(require_internal_secret)])
async def cleanup_guests(
    db: AsyncSession = Depends(get_db),
):
    deleted = await guest_service.purge_expired_guests(db)

    return envelope({"deleted": deleted})
