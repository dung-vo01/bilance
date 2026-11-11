from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    default_limits=["120/minute"],
    swallow_errors=True,
    in_memory_fallback_enabled=True,
    storage_options={"socket_connect_timeout": 1, "socket_timeout": 1},
)
