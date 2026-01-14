from pydantic import BaseModel


class AuthConfig(BaseModel):
    token_max_age_seconds: int
    auth_code_max_age_seconds: int


class AuthCodeData(BaseModel):
    """임시 인증 코드에 저장되는 데이터"""

    provider: str
    social_id: str
    email: str
    nickname: str
