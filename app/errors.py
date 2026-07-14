import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | list[Any] | str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def error_response(error: AppError) -> JSONResponse:
    payload = ErrorResponse(
        code=error.code,
        message=error.message,
        details=error.details,
    )
    return JSONResponse(status_code=error.status_code, content=payload.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        del request, exception
        return error_response(
            AppError(
                status_code=400,
                code="VALIDATION_ERROR",
                message="입력값을 확인해 주세요.",
            )
        )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exception: AppError) -> JSONResponse:
        del request
        return error_response(exception)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled application error",
            extra={"method": request.method, "path": request.url.path},
            exc_info=exception,
        )
        return error_response(
            AppError(
                status_code=500,
                code="INTERNAL_ERROR",
                message="서버 오류가 발생했습니다.",
            )
        )
