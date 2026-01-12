from pydantic import EmailStr
from sqlmodel import Field

from apps.models.base import BaseModel
from apps.types.social import SocialProvider


class User(BaseModel, table=True):
    email: EmailStr = Field(max_length=50, unique=True)
    nickname: str = Field(max_length=20, unique=True)

    social_provider: SocialProvider = Field(max_length=20)
    social_id: str = Field(max_length=50)
