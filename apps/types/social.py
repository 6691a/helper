from enum import StrEnum

from pydantic import BaseModel, EmailStr


class SocialProvider(StrEnum):
    GOOGLE = "google"


class Social(BaseModel):
    provider: SocialProvider
    secret: str
    id: str
    server_metadata_url: str | None = None
    client_kwargs: dict[str, str] | None = None


class SocialUserInfo(BaseModel):
    provider: SocialProvider
    social_id: str
    email: EmailStr
    nickname: str


class SocialConfig(BaseModel):
    redirect_uri_base: str
    providers: list[Social]
