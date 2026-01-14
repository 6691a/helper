import secrets

from redis.asyncio import Redis

from apps.types.auth import AuthCodeData
from apps.types.redis import RedisConfig


class SessionService:
    SESSION_PREFIX = "session:"
    AUTH_CODE_PREFIX = "auth_code:"

    def __init__(
        self,
        redis_config: RedisConfig,
        token_max_age: int,
        auth_code_max_age: int,
    ):
        self.redis = Redis(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            password=redis_config.password,
            decode_responses=True,
        )
        self.token_max_age = token_max_age
        self.auth_code_max_age = auth_code_max_age

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def create_session(self, user_id: int) -> str:
        """사용자 세션을 생성하고 세션 토큰을 반환합니다."""
        token = self._generate_token()
        key = f"{self.SESSION_PREFIX}{token}"
        await self.redis.set(key, str(user_id), ex=self.token_max_age)
        return token

    async def get_user_id(self, token: str) -> int | None:
        """세션 토큰으로 사용자 ID를 조회합니다."""
        key = f"{self.SESSION_PREFIX}{token}"
        user_id = await self.redis.get(key)
        if user_id is None:
            return None
        return int(user_id)

    async def delete_session(self, token: str) -> bool:
        """세션을 삭제합니다."""
        key = f"{self.SESSION_PREFIX}{token}"
        result: int = await self.redis.delete(key)
        return result > 0

    async def refresh_session(self, token: str) -> bool:
        """세션 만료 시간을 갱신합니다."""
        key = f"{self.SESSION_PREFIX}{token}"
        result: bool = await self.redis.expire(key, self.token_max_age)
        return result

    async def create_auth_code(self, data: AuthCodeData) -> str:
        """임시 인증 코드를 생성합니다. (회원가입 전 추가 정보 입력용)"""
        code = self._generate_token()
        key = f"{self.AUTH_CODE_PREFIX}{code}"
        await self.redis.set(key, data.model_dump_json(), ex=self.auth_code_max_age)
        return code

    async def get_auth_code_data(self, code: str) -> AuthCodeData | None:
        """인증 코드로 저장된 데이터를 조회하고 삭제합니다."""
        key = f"{self.AUTH_CODE_PREFIX}{code}"
        data = await self.redis.get(key)
        if data is None:
            return None
        await self.redis.delete(key)
        return AuthCodeData.model_validate_json(data)
