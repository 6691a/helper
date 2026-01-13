from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.schemas.common import Response


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
