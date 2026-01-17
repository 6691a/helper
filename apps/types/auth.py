from pydantic import BaseModel

from apps.types.social import SocialProvider


class AuthConfig(BaseModel):
    token_max_age_seconds: int
    auth_code_max_age_seconds: int


class AuthCodeData(BaseModel):
    """임시 인증 코드에 저장되는 데이터"""

    provider: SocialProvider
    social_id: str
    email: str
    nickname: str
