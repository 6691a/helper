from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware

from apps.exceptions import exception_handlers, VALIDATION_ERROR_RESPONSES
from apps.i18n.middleware import I18nMiddleware
from containers import Container
from settings import Settings
from apps.controllers import *


container = Container()
container.config.from_pydantic(settings=Settings, required=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.container = container
    yield


app = FastAPI(lifespan=lifespan, responses=VALIDATION_ERROR_RESPONSES)

app.add_middleware(SessionMiddleware, secret_key=Settings.secret_key)
app.add_middleware(AuthenticationMiddleware, backend=container.auth_backend())
app.add_middleware(I18nMiddleware)

exception_handlers(app)

for router in routers:
    app.include_router(router)
