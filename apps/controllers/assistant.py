from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette import status
from starlette.authentication import requires

from apps.schemas.assistant import AssistantRequest, AssistantResponse
from apps.schemas.common import Response, ResponseProvider
from apps.schemas.conversation import ConversationResponse, ProcessVoiceRequest
from apps.services.assistant import AssistantService
from apps.services.conversation import ConversationService
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
