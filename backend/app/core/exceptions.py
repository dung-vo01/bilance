import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.error")


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnauthenticatedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, 404)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, 409)


class ServerError(AppError):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first["loc"] if p != "body")
        message = f"{loc}: {first['msg']}" if loc else first["msg"]
        return JSONResponse(
            status_code=422, content={"success": False, "error": message}
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"},
        )
