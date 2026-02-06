from typing import Annotated
from urllib.parse import urlencode

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette.authentication import requires
from starlette.responses import RedirectResponse

from apps.schemas.auth import AuthResponse, SignupRequest, UserResponse
from apps.schemas.common import Response, ResponseProvider
from apps.services.auth import AuthService
from apps.services.social import SocialAuthService
from apps.types.social import SocialProvider
from containers import Container

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@router.get("/{provider}")
@inject
async def social_login(
    provider: SocialProvider,
    request: Request,
    redirect_uri: str,
    social_auth_service: Annotated[
        SocialAuthService,
        Depends(Provide[Container.social_auth_service]),
    ],
) -> RedirectResponse:
    """소셜 로그인 페이지로 리다이렉트합니다."""
    social_auth_service.validate_redirect_uri(redirect_uri)
    # State를 Redis에 저장하고 OAuth 시작
    return await social_auth_service.redirect_login(request, provider, redirect_uri)


@router.get("/{provider}/callback")
@inject
async def social_callback(
    provider: SocialProvider,
    request: Request,
    social_auth_service: Annotated[
        SocialAuthService,
        Depends(Provide[Container.social_auth_service]),
    ],
    auth_service: Annotated[
        AuthService,
        Depends(Provide[Container.auth_service]),
    ],
) -> RedirectResponse:
    """OAuth 콜백을 처리하고 앱으로 리다이렉트합니다."""
    user_info, redirect_uri = await social_auth_service.handle_callback(request, provider)
    is_new_user, token_or_code = await auth_service.login_or_prepare_signup(user_info)

    if not redirect_uri:
        raise ValueError("redirect_uri not found.")

    if is_new_user:
        params = urlencode({"auth_code": token_or_code, "is_new_user": "true"})
    else:
        params = urlencode({"session_token": token_or_code, "is_new_user": "false"})

    return RedirectResponse(url=f"{redirect_uri}?{params}")


@router.post("/signup", response_model=Response[AuthResponse], status_code=201)
@inject
async def signup(
    body: SignupRequest,
    auth_service: Annotated[
        AuthService,
        Depends(Provide[Container.auth_service]),
    ],
) -> JSONResponse:
    """회원가입을 완료합니다."""
    session_token = await auth_service.signup(
        auth_code=body.auth_code,
        nickname=body.nickname,
    )
    return ResponseProvider.created(AuthResponse(session_token=session_token))


@router.get("/me", response_model=Response[UserResponse])
@requires("authenticated")
@inject
async def get_current_user(
    request: Request,
    auth_service: Annotated[
        AuthService,
        Depends(Provide[Container.auth_service]),
    ],
) -> JSONResponse:
    """현재 로그인한 사용자 정보를 조회합니다."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = await auth_service.get_current_user(token)
    return ResponseProvider.success(
        UserResponse(
            id=user.id if user.id else 0,
            email=user.email,
            nickname=user.nickname,
            profile_image=user.profile_image,
        )
    )


@router.post("/logout", response_model=Response[None])
@requires("authenticated")
@inject
async def logout(
    request: Request,
    auth_service: Annotated[
        AuthService,
        Depends(Provide[Container.auth_service]),
    ],
) -> JSONResponse:
    """로그아웃합니다."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    await auth_service.logout(token)
    return ResponseProvider.success(None)
