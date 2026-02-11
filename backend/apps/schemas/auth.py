from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    auth_code: str = Field(description="OAuth 콜백에서 받은 인증 코드")
    nickname: str = Field(min_length=2, max_length=20, description="닉네임")
    profile_image: str | None = Field(default=None, description="프로필 이미지 URL")


class AuthResponse(BaseModel):
    session_token: str = Field(description="세션 토큰")


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    profile_image: str | None
