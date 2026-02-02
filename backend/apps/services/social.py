from typing import cast
from urllib.parse import urlparse

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Request
from starlette.responses import RedirectResponse

from apps.exceptions import AppException
from apps.i18n import _
from apps.types.social import Social, SocialProvider, SocialUserInfo


class SocialAuthService:
    def __init__(
        self,
        socials: list[Social],
        redirect_uri_base: str,
        allowed_redirect_hosts: list[str],
    ):
        self.oauth = OAuth()
        self.redirect_uri_base = redirect_uri_base
        self.allowed_redirect_hosts = allowed_redirect_hosts

        for social in socials:
            self.oauth.register(
                name=social.provider.value,
                client_id=social.id,
                client_secret=social.secret,
                server_metadata_url=social.server_metadata_url,
                client_kwargs=social.client_kwargs,
            )

    def validate_redirect_uri(self, redirect_uri: str) -> None:
        """redirect_uri가 허용된 호스트인지 검증합니다."""
        parsed = urlparse(redirect_uri)
        host = parsed.netloc or parsed.scheme  # 커스텀 스킴(myapp://)은 scheme에 있음
        if host not in self.allowed_redirect_hosts:
            raise AppException(_("Invalid redirect_uri."))

    def _get_redirect_uri(self, provider: SocialProvider) -> str:
        return f"{self.redirect_uri_base}/api/v1/auth/{provider.value}/callback"

    async def redirect_login(self, request: Request, provider: SocialProvider) -> RedirectResponse:
        provider_client = getattr(self.oauth, provider.value)
        redirect_uri = self._get_redirect_uri(provider)
        return cast(
            RedirectResponse,
            await provider_client.authorize_redirect(request, redirect_uri),
        )

    async def handle_callback(self, request: Request, provider: SocialProvider) -> SocialUserInfo:
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
