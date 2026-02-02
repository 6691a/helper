from pydantic import EmailStr
from sqlmodel import Field, Relationship

from apps.models import Memory
from apps.models.base import BaseModel
from apps.types.social import SocialProvider


class User(BaseModel, table=True):
    email: EmailStr = Field(max_length=50, unique=True)
    nickname: str = Field(max_length=20, unique=True)
    profile_image: str | None = Field(default=None, max_length=255)

    social_provider: SocialProvider = Field(max_length=20)
    social_id: str = Field(max_length=50)

    ####### Relationship #######
    memories: list[Memory] = Relationship(back_populates="user")
