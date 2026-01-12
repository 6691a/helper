from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from containers import Container
from settings import Settings
from apps.controllers import *


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = Container()
    container.config.from_pydantic(settings=Settings, required=True)
    app.container = container
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=Settings.secret_key)

for router in routers:
    app.include_router(router)
