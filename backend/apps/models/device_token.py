from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlmodel import Field

from apps.models.base import BaseModel


class DeviceToken(BaseModel, table=True):
    """FCM 디바이스 토큰 모델"""

    __tablename__ = "device_token"

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    token: str = Field(sa_column=Column(String(512), unique=True, nullable=False))
    platform: str = Field(sa_column=Column(String(10), nullable=False))  # "ios" | "android"
    is_active: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="true"),
        default=True,
    )
