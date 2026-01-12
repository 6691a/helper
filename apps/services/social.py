from typing import cast

from fastapi import Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from apps.types.social import SocialProvider, Social, SocialUserInfo


class SocialAuthService:
    def __init__(self, socials: list[Social], redirect_uri_base: str):
        self.oauth = OAuth()
        self.redirect_uri_base = redirect_uri_base

        for social in socials:
            self.oauth.register(
                name=social.provider.value,
                client_id=social.id,
                client_secret=social.secret,
                server_metadata_url=social.server_metadata_url,
                client_kwargs=social.client_kwargs,
            )

    def _get_redirect_uri(self, provider: SocialProvider) -> str:
        return f"{self.redirect_uri_base}/auth/{provider.value}/callback"

    async def redirect_login(
        self, request: Request, provider: SocialProvider
    ) -> RedirectResponse:
        provider_client = getattr(self.oauth, provider.value)
        redirect_uri = self._get_redirect_uri(provider)
        return cast(
            RedirectResponse,
            await provider_client.authorize_redirect(request, redirect_uri),
        )

    async def handle_callback(
        self, request: Request, provider: SocialProvider
    ) -> SocialUserInfo:
        """OAuth 콜백을 처리하고 사용자 정보를 반환합니다."""
        provider_client = getattr(self.oauth, provider.value)

        try:
            token = await provider_client.authorize_access_token(request)
        except OAuthError as e:
            raise ValueError(f"OAuth 인증 실패: {e.description}") from e

        # OpenID Connect를 통해 사용자 정보 가져오기
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await provider_client.userinfo(token=token)

        return SocialUserInfo(
            provider=provider,
            social_id=user_info["sub"],
            email=user_info["email"],
            nickname=user_info.get("name") or user_info["email"].split("@")[0],
        )
