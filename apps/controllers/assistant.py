from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from starlette.authentication import requires

from apps.schemas.assistant import AssistantRequest, AssistantResponse
from apps.schemas.common import Response, ResponseProvider
from apps.services.assistant import AssistantService
from containers import Container

router = APIRouter(
    prefix="/api/v1/assistant",
    tags=["assistant"],
)


@router.post("/chat", response_model=Response[AssistantResponse])
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
