from apps.exceptions import AuthenticationError, ConflictError
from apps.i18n import _
from apps.models.user import User
from apps.repositories.user import UserRepository
from apps.services.session import SessionService
from apps.types.auth import AuthCodeData
from apps.types.social import SocialUserInfo


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_service: SessionService,
    ):
        self.user_repository = user_repository
        self.session_service = session_service

    async def login_or_prepare_signup(self, user_info: SocialUserInfo) -> tuple[bool, str]:
        """
        소셜 로그인 정보로 로그인하거나 회원가입을 준비합니다.

        Returns:
            (is_new_user, token_or_code)
            - 기존 사용자: (False, session_token)
            - 신규 사용자: (True, auth_code)
        """
        user = await self.user_repository.get_by_social(user_info.provider, user_info.social_id)

        if user and user.id:
            session_token = await self.session_service.create_session(user.id)
            return False, session_token

        auth_code = await self.session_service.create_auth_code(
            AuthCodeData(
                provider=user_info.provider,
                social_id=user_info.social_id,
                email=user_info.email,
                nickname=user_info.nickname,
            )
        )
        return True, auth_code

    async def signup(
        self,
        auth_code: str,
        nickname: str,
        profile_image: str | None = None,
    ) -> str:
        """
        인증 코드를 사용해 회원가입을 완료합니다.

        Returns:
            세션 토큰
        """
        auth_data = await self.session_service.get_auth_code_data(auth_code)
        if auth_data is None:
            raise AuthenticationError(_("Invalid or expired auth code."))

        existing_user = await self.user_repository.get_by_nickname(nickname)
        if existing_user:
            raise ConflictError(_("Nickname already in use."))

        existing_email = await self.user_repository.get_by_email(auth_data.email)
        if existing_email:
            raise ConflictError(_("Email already registered."))

        user = User(
            email=auth_data.email,
            nickname=nickname,
            profile_image=profile_image,
            social_provider=auth_data.provider,
            social_id=auth_data.social_id,
        )
        user = await self.user_repository.create(user)
        if user.id is None:
            raise RuntimeError("User ID is None after creation")

        session_token = await self.session_service.create_session(user.id)
        return session_token

    async def logout(self, session_token: str) -> bool:
        """세션을 삭제하여 로그아웃합니다."""
        return await self.session_service.delete_session(session_token)

    async def get_current_user(self, session_token: str) -> User:
        """세션 토큰으로 현재 사용자를 조회합니다."""
        user_id = await self.session_service.get_user_id(session_token)
        if user_id is None:
            raise AuthenticationError(_("Invalid or expired session."))

        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError(_("User not found."))

        return user
