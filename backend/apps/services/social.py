import secrets
from typing import cast
from urllib.parse import urlparse

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Request
from starlette.responses import RedirectResponse

from apps.exceptions import AppException
from apps.i18n import _
from apps.services.session import SessionService
from apps.types.social import Social, SocialProvider, SocialUserInfo


class SocialAuthService:
    def __init__(
        self,
        socials: list[Social],
        redirect_uri_base: str,
        allowed_redirect_schemes: list[str],
        allowed_redirect_hosts: list[str],
        session_service: SessionService,
    ):
        self.oauth = OAuth()
        self.redirect_uri_base = redirect_uri_base
        self.allowed_redirect_schemes = allowed_redirect_schemes
        self.allowed_redirect_hosts = allowed_redirect_hosts
        self.session_service = session_service

        for social in socials:
            self.oauth.register(
                name=social.provider.value,
                client_id=social.id,
                client_secret=social.secret,
                server_metadata_url=social.server_metadata_url,
                client_kwargs=social.client_kwargs,
            )

    def validate_redirect_uri(self, redirect_uri: str) -> None:
        """redirect_uri가 허용된 스킴 또는 호스트인지 검증합니다."""
        parsed = urlparse(redirect_uri)

        if parsed.scheme in self.allowed_redirect_schemes:
            return

        if parsed.netloc in self.allowed_redirect_hosts:
            return

        raise AppException(_("Invalid redirect_uri."))

    def _get_redirect_uri(self, provider: SocialProvider) -> str:
        return f"{self.redirect_uri_base}/api/v1/auth/{provider.value}/callback"

    async def redirect_login(
        self, request: Request, provider: SocialProvider, app_redirect_uri: str
    ) -> RedirectResponse:
        provider_client = getattr(self.oauth, provider.value)
        redirect_uri = self._get_redirect_uri(provider)

        # Generate OAuth state and store redirect_uri in Redis
        state = secrets.token_urlsafe(32)
        await self.session_service.store_oauth_state(state, app_redirect_uri)

        return cast(
            RedirectResponse,
            await provider_client.authorize_redirect(request, redirect_uri, state=state),
        )

    async def handle_callback(
        self, request: Request, provider: SocialProvider
    ) -> tuple[SocialUserInfo, str | None]:
        """OAuth 콜백을 처리하고 사용자 정보 및 redirect_uri를 반환합니다."""
        provider_client = getattr(self.oauth, provider.value)

        # Extract state and verify it (manual CSRF validation)
        state = request.query_params.get("state")
        redirect_uri = None
        if state:
            redirect_uri = await self.session_service.get_oauth_redirect_uri(state)
            if not redirect_uri:
                raise ValueError("Invalid or expired OAuth state")

        try:
            # Manually fetch token without Authlib's state validation
            # since we're managing state via Redis instead of session
            code = request.query_params.get("code")
            if not code:
                raise ValueError("Missing authorization code")

            redirect_callback_uri = self._get_redirect_uri(provider)
            token = await provider_client.fetch_access_token(
                code=code,
                redirect_uri=redirect_callback_uri,
            )
        except OAuthError as e:
            raise ValueError(f"OAuth 인증 실패: {e.description}") from e

        # OpenID Connect를 통해 사용자 정보 가져오기
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await provider_client.userinfo(token=token)

        social_user_info = SocialUserInfo(
            provider=provider,
            social_id=user_info["sub"],
            email=user_info["email"],
            nickname=user_info.get("name") or user_info["email"].split("@")[0],
        )

        return social_user_info, redirect_uri
