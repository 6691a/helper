from typing import TypeVar

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class Response[T](BaseModel):
    code: int
    message: str
    result: T | None = None


class ResponseProvider:
    @staticmethod
    def success(result: T, status_code: int = status.HTTP_200_OK) -> JSONResponse:
        response = Response(code=status_code, message="SUCCESS", result=result)
        return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))

    @staticmethod
    def created(result: T) -> JSONResponse:
        response = Response(code=status.HTTP_201_CREATED, message="CREATED", result=result)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump(mode="json"),
        )

    @staticmethod
    def failed(status_code: int, message: str, result: T | None = None) -> JSONResponse:
        response = Response(code=status_code, message=message, result=result)
        return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))
