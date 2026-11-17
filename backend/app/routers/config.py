from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import envelope

router = APIRouter()


@router.get("")
def get_server_config():
    return envelope({"email_enabled": settings.EMAIL_ENABLED})
