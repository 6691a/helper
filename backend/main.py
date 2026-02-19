import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from apps.controllers import *
from apps.exceptions import VALIDATION_ERROR_RESPONSES, exception_handlers
from apps.i18n.middleware import I18nMiddleware
from containers import Container
from settings import Settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


container = Container()
container.config.from_pydantic(settings=Settings, required=True)
limiter = Limiter(key_func=get_remote_address, storage_uri=Settings.redis.url)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.container = container
    app.state.limiter = limiter
    yield


app = FastAPI(
    lifespan=lifespan,
    responses=VALIDATION_ERROR_RESPONSES,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)


def openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Helper API",
        version="1.0.0",
        description="Memory Assistant API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "token",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = openapi

app.add_middleware(SessionMiddleware, secret_key=Settings.secret_key)
app.add_middleware(AuthenticationMiddleware, backend=container.auth_backend())
app.add_middleware(I18nMiddleware)

exception_handlers(app)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


for router in routers:
    app.include_router(router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
