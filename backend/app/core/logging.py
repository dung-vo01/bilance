import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("app.request")

    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)

        self.logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration}ms)"
        )
        return response
