from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette.authentication import requires

from apps.repositories.reminder import ReminderRepository
from apps.schemas.common import Response, ResponseProvider
from apps.schemas.reminder import ReminderResponse, ReminderUpdate, ReminderWithMemoryResponse
from apps.services.reminder import ReminderService
from apps.types.reminder import ReminderStatus
from apps.utils.datetime_utils import TimezoneConverter
from containers import Container

router = APIRouter(
    prefix="/api/v1/reminders",
    tags=["reminder"],
)


@router.get("/", response_model=Response[list[ReminderWithMemoryResponse]], status_code=200)
@requires("authenticated")
@inject
async def get_reminders(
    request: Request,
    reminder_repository: Annotated[ReminderRepository, Depends(Provide[Container.reminder_repository])],
    status: ReminderStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> JSONResponse:
    """사용자의 알림(리마인더) 목록을 조회합니다."""
    user_id = request.user.user.id
    timezone = request.state.timezone
    reminders = await reminder_repository.get_all_with_memory(
        user_id=user_id, status=status, limit=limit, offset=offset
    )
    result = []
    for r in reminders:
        if r.id is None:
            raise ValueError("Reminder ID should not be None")
        result.append(
            TimezoneConverter.model_dump(
                ReminderWithMemoryResponse(
                    id=r.id,
                    memory_id=r.memory_id,
                    memory_content=r.memory.content,
                    memory_keywords=r.memory.keywords,
                    memory_type=r.memory.type,
                    frequency=r.frequency,
                    weekdays=r.weekdays,
                    day_of_month=r.day_of_month,
                    specific_date=r.specific_date,
                    time=r.time,
                    next_run_at=r.next_run_at,
                    status=r.status,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                ),
                timezone,
            )
        )
    return ResponseProvider.success(result)


@router.patch("/{reminder_id}", response_model=Response[ReminderResponse], status_code=200)
@requires("authenticated")
@inject
async def update_reminder(
    request: Request,
    reminder_id: int,
    data: ReminderUpdate,
    reminder_service: Annotated[ReminderService, Depends(Provide[Container.reminder_service])],
) -> JSONResponse:
    """알림(리마인더)을 수정합니다."""
    user_id = request.user.user.id
    updated = await reminder_service.update_reminder(reminder_id, data, user_id)
    return ResponseProvider.success(TimezoneConverter.model_dump(updated, request.state.timezone))


@router.post("/{reminder_id}/pause", response_model=Response[ReminderResponse], status_code=200)
@requires("authenticated")
@inject
async def pause_reminder(
    request: Request,
    reminder_id: int,
    reminder_service: Annotated[ReminderService, Depends(Provide[Container.reminder_service])],
) -> JSONResponse:
    """알림(리마인더)을 일시정지합니다."""
    user_id = request.user.user.id
    updated = await reminder_service.pause_reminder(reminder_id, user_id)
    return ResponseProvider.success(TimezoneConverter.model_dump(updated, request.state.timezone))


@router.post("/{reminder_id}/resume", response_model=Response[ReminderResponse], status_code=200)
@requires("authenticated")
@inject
async def resume_reminder(
    request: Request,
    reminder_id: int,
    reminder_service: Annotated[ReminderService, Depends(Provide[Container.reminder_service])],
) -> JSONResponse:
    """알림(리마인더)을 재개합니다."""
    user_id = request.user.user.id
    updated = await reminder_service.resume_reminder(reminder_id, user_id)
    return ResponseProvider.success(TimezoneConverter.model_dump(updated, request.state.timezone))
