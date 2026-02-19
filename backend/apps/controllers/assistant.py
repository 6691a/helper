from datetime import date
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette import status
from starlette.authentication import requires

from apps.repositories.memory import MemoryRepository
from apps.schemas.assistant import AssistantRequest, AssistantResponse
from apps.schemas.common import Response, ResponseProvider
from apps.schemas.conversation import ConversationResponse, ProcessVoiceRequest
from apps.schemas.memory import MemoryResponse
from apps.services.assistant import AssistantService
from apps.services.conversation import ConversationService
from apps.utils.datetime_utils import format_datetime_for_timezone
from containers import Container

router = APIRouter(
    prefix="/api/v1/assistant",
    tags=["assistant"],
)


@router.post("/chat", response_model=Response[AssistantResponse], status_code=status.HTTP_200_OK)
@requires("authenticated")
@inject
async def chat(
    request: Request,
    body: AssistantRequest,
    assistant_service: Annotated[
        AssistantService,
        Depends(Provide[Container.assistant_service]),
    ],
) -> JSONResponse:
    """
    AI 어시스턴트와 대화합니다.

    - 정보 저장 요청: "~를 기억해", "~에 뒀어" 등
    - 질문: "~어디 있어?", "~어떻게 가?" 등
    """
    user_id = request.user.user.id
    result = await assistant_service.process(text=body.text, user_id=user_id)
    return ResponseProvider.success(result)


@router.post(
    "/voice",
    response_model=Response[ConversationResponse],
    status_code=status.HTTP_200_OK,
)
@requires("authenticated")
@inject
async def voice(
    request: Request,
    body: ProcessVoiceRequest,
    conversation_service: Annotated[
        ConversationService,
        Depends(Provide[Container.conversation_service]),
    ],
) -> JSONResponse:
    """
    음성 세션을 처리하여 대화 기록을 생성합니다.

    - WebSocket STT 완료 후 session_id를 받아 처리
    - 사용자가 확인/수정한 텍스트로 AI 처리
    - Memory/Reminder 생성 및 Conversation 기록
    """
    user_id = request.user.user.id
    result = await conversation_service.process_voice(request=body, user_id=user_id)
    return ResponseProvider.success(result)


@router.get("/memories", response_model=Response[list[MemoryResponse]], status_code=status.HTTP_200_OK)
@requires("authenticated")
@inject
async def get_memories(
    request: Request,
    memory_repository: Annotated[
        MemoryRepository,
        Depends(Provide[Container.memory_repository]),
    ],
    limit: int = 10,
    offset: int = 0,
) -> JSONResponse:
    """
    사용자의 메모리 목록을 조회합니다.

    - 최신순으로 정렬
    - limit: 가져올 개수 (기본 10개)
    - offset: 건너뛸 개수 (페이징용)
    - X-Timezone 헤더로 시간대 지정 가능
    """
    user_id = request.user.user.id
    timezone = request.headers.get("X-Timezone", "UTC")

    memories = await memory_repository.get_all(user_id=user_id, limit=limit, offset=offset)

    # Memory 객체를 dict로 변환하며 datetime을 사용자 시간대로 포맷팅
    response_data = [
        {
            "id": m.id,
            "type": m.type,
            "keywords": m.keywords,
            "content": m.content,
            "metadata_": m.metadata_,
            "original_text": m.original_text,
            "created_at": format_datetime_for_timezone(m.created_at, timezone),
            "updated_at": format_datetime_for_timezone(m.updated_at, timezone),
        }
        for m in memories
    ]

    return ResponseProvider.success(response_data)


@router.get("/memories/calendar-marks", response_model=Response[dict[str, int]], status_code=status.HTTP_200_OK)
@requires("authenticated")
@inject
async def get_calendar_marks(
    request: Request,
    memory_repository: Annotated[
        MemoryRepository,
        Depends(Provide[Container.memory_repository]),
    ],
) -> JSONResponse:
    """
    메모리가 있는 날짜와 개수를 반환합니다 (캘린더 마킹용).

    - 응답: {"YYYY-MM-DD": count, ...}
    - X-Timezone 헤더로 시간대 지정 가능
    """
    user_id = request.user.user.id
    timezone = request.headers.get("X-Timezone", "UTC")

    marks = await memory_repository.get_calendar_marks(user_id=user_id, timezone=timezone)
    return ResponseProvider.success(marks)


@router.get("/memories/by-date", response_model=Response[list[MemoryResponse]], status_code=status.HTTP_200_OK)
@requires("authenticated")
@inject
async def get_memories_by_date(
    request: Request,
    memory_repository: Annotated[
        MemoryRepository,
        Depends(Provide[Container.memory_repository]),
    ],
    date: str,
) -> JSONResponse:
    """
    특정 날짜의 메모리 목록을 조회합니다.

    - date: YYYY-MM-DD 형식
    - X-Timezone 헤더로 시간대 지정 가능
    """
    user_id = request.user.user.id
    timezone = request.headers.get("X-Timezone", "UTC")

    target_date = date_from_str(date)
    if target_date is None:
        return ResponseProvider.failed(status_code=400, message="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")

    memories = await memory_repository.get_by_date(target_date=target_date, user_id=user_id, timezone=timezone)

    response_data = [
        {
            "id": m.id,
            "type": m.type,
            "keywords": m.keywords,
            "content": m.content,
            "metadata_": m.metadata_,
            "original_text": m.original_text,
            "created_at": format_datetime_for_timezone(m.created_at, timezone),
            "updated_at": format_datetime_for_timezone(m.updated_at, timezone),
        }
        for m in memories
    ]

    return ResponseProvider.success(response_data)


def date_from_str(date_str: str) -> date | None:
    """YYYY-MM-DD 문자열을 date 객체로 변환합니다."""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


@router.delete("/memories/{memory_id}", response_model=Response[None], status_code=status.HTTP_200_OK)
@requires("authenticated")
@inject
async def delete_memory(
    request: Request,
    memory_id: int,
    memory_repository: Annotated[
        MemoryRepository,
        Depends(Provide[Container.memory_repository]),
    ],
) -> JSONResponse:
    """
    메모리를 삭제합니다.

    - memory_id: 삭제할 Memory ID
    - 본인의 메모리만 삭제 가능 (user_id 검증)
    """
    user_id = request.user.user.id

    # 메모리 조회 (본인 것만)
    memory = await memory_repository.get_by_id(memory_id, user_id=user_id)
    if memory is None:
        return ResponseProvider.failed(status_code=404, message="메모리를 찾을 수 없습니다")

    # 삭제
    await memory_repository.delete(memory)

    return ResponseProvider.success(None)
