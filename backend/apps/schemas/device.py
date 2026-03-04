from datetime import datetime

from pydantic import BaseModel, Field


class DeviceTokenRegisterRequest(BaseModel):
    """FCM 디바이스 토큰 등록 요청"""

    token: str = Field(max_length=512, description="FCM 토큰")
    platform: str = Field(pattern="^(ios|android)$", description="플랫폼 (ios 또는 android)")


class DeviceTokenDeleteRequest(BaseModel):
    """FCM 디바이스 토큰 삭제 요청"""

    token: str = Field(max_length=512, description="삭제할 FCM 토큰")


class DeviceTokenNotificationUpdateRequest(BaseModel):
    """FCM 알림 활성화 여부 변경 요청"""

    token: str = Field(max_length=512, description="FCM 토큰")
    is_active: bool = Field(description="알림 활성화 여부")


class DeviceTokenResponse(BaseModel):
    """FCM 디바이스 토큰 응답"""

    id: int = Field(description="DeviceToken ID")
    platform: str = Field(description="플랫폼")
    is_active: bool = Field(description="알림 활성화 여부")
    created_at: datetime = Field(description="등록일시")

    model_config = {"from_attributes": True}
