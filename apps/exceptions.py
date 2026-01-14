from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.i18n import _
from apps.schemas.common import Response


class AppException(Exception):
    """애플리케이션 기본 예외"""

    def __init__(self, message: str, code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthenticationError(AppException):
    """인증 관련 예외"""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or _("Authentication failed."),
            status.HTTP_401_UNAUTHORIZED,
        )


class NotFoundError(AppException):
    """리소스를 찾을 수 없음"""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or _("Resource not found."),
            status.HTTP_404_NOT_FOUND,
        )


class ConflictError(AppException):
    """중복 리소스 예외"""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or _("Resource already exists."),
            status.HTTP_409_CONFLICT,
        )


class ValidationErrorDetail(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(Response[list[ValidationErrorDetail]]):
    code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    message: str = "VALIDATION_ERROR"


VALIDATION_ERROR_RESPONSES = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Validation Error",
    }
}


def exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        response = Response[None](
            code=exc.code,
            message=exc.message,
            result=None,
        )
        return JSONResponse(
            status_code=exc.code,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            ValidationErrorDetail(
                field=" -> ".join(str(loc) for loc in error["loc"]),
                message=error["msg"],
            )
            for error in exc.errors()
        ]

        response = Response[list[ValidationErrorDetail]](
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="VALIDATION_ERROR",
            result=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(mode="json"),
        )
