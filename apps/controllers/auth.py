from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Request, Depends
from starlette.responses import RedirectResponse

from apps.services.social import SocialAuthService
from apps.types.social import SocialProvider
from containers import Container

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@router.get("/{provider}/login")
@inject
async def social_login(
    provider: SocialProvider,
    request: Request,
    social_auth_service: Annotated[
        SocialAuthService,
        Depends(Provide[Container.social_auth_service]),
    ],
) -> RedirectResponse:
    return await social_auth_service.redirect_login(request, provider)
