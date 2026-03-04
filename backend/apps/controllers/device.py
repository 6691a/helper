from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette.authentication import requires

from apps.repositories.device_token import DeviceTokenRepository
from apps.schemas.common import Response, ResponseProvider
from apps.schemas.device import (
    DeviceTokenDeleteRequest,
    DeviceTokenNotificationUpdateRequest,
    DeviceTokenRegisterRequest,
    DeviceTokenResponse,
)
from apps.services.push import PushService
from containers import Container

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["device"],
)


@router.post("", response_model=Response[DeviceTokenResponse], status_code=200)
@requires("authenticated")
@inject
async def register_device_token(
    request: Request,
    data: DeviceTokenRegisterRequest,
    device_token_repository: Annotated[DeviceTokenRepository, Depends(Provide[Container.device_token_repository])],
) -> JSONResponse:
    """FCM 디바이스 토큰을 등록합니다."""
    user_id = request.user.user.id
    device_token = await device_token_repository.upsert(
        user_id=user_id,
        token=data.token,
        platform=data.platform,
    )
    response = DeviceTokenResponse.model_validate(device_token)
    return ResponseProvider.success(response.model_dump(mode="json"))


@router.post("/test-push", response_model=Response[None], status_code=200)
@inject
async def test_push(
    request: Request,
    device_token_repository: Annotated[DeviceTokenRepository, Depends(Provide[Container.device_token_repository])],
    push_service: Annotated[PushService, Depends(Provide[Container.push_service])],
) -> JSONResponse:
    """모든 사용자의 활성화된 디바이스에 테스트 푸시 알림을 전송합니다."""
    tokens = await device_token_repository.get_all_active()
    token_values = [t.token for t in tokens]
    push_service.send_multicast(token_values, title="테스트 알림", body="푸시 알림이 정상적으로 작동합니다.")
    return ResponseProvider.success(None)


@router.patch("/notification", response_model=Response[DeviceTokenResponse], status_code=200)
@requires("authenticated")
@inject
async def update_notification(
    request: Request,
    data: DeviceTokenNotificationUpdateRequest,
    device_token_repository: Annotated[DeviceTokenRepository, Depends(Provide[Container.device_token_repository])],
) -> JSONResponse:
    """FCM 디바이스 토큰의 알림 활성화 여부를 변경합니다."""
    device_token = await device_token_repository.update_is_active(
        token=data.token,
        is_active=data.is_active,
    )
    if device_token is None:
        return ResponseProvider.failed(404, "등록되지 않은 토큰입니다.")
    response = DeviceTokenResponse.model_validate(device_token)
    return ResponseProvider.success(response.model_dump(mode="json"))


@router.delete("", response_model=Response[None], status_code=200)
@requires("authenticated")
@inject
async def delete_device_token(
    request: Request,
    data: DeviceTokenDeleteRequest,
    device_token_repository: Annotated[DeviceTokenRepository, Depends(Provide[Container.device_token_repository])],
) -> JSONResponse:
    """FCM 디바이스 토큰을 삭제합니다."""
    await device_token_repository.delete_by_token(token=data.token)
    return ResponseProvider.success(None)
