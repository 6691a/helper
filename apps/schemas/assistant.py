from pydantic import BaseModel, Field

from apps.schemas.memory import MemoryResponse, MemorySearchResult
from apps.types.assistant import IntentType, ReminderInfo


class AssistantRequest(BaseModel):
    """Assistant 요청"""

    text: str = Field(description="사용자 입력 텍스트 (음성 인식 결과 또는 직접 입력)")


class AssistantSaveResponse(BaseModel):
    """정보 저장 응답"""

    message: str = Field(description="저장 결과 메시지")
    memory: MemoryResponse = Field(description="저장된 Memory 정보")
    reminder: ReminderInfo | None = Field(
        default=None, description="설정된 알림 정보 (알림 요청이 있었을 때)"
    )


class AssistantQueryResponse(BaseModel):
    """질문 응답"""

    answer: str = Field(description="AI가 생성한 답변")
    related_memories: list[MemorySearchResult] = Field(
        default_factory=list, description="관련 Memory 목록"
    )


class AssistantResponse(BaseModel):
    """Assistant 통합 응답"""

    intent: IntentType = Field(description="분류된 의도")
    save_result: AssistantSaveResponse | None = Field(
        default=None, description="저장 결과 (intent=save일 때)"
    )
    query_result: AssistantQueryResponse | None = Field(
        default=None, description="질문 응답 (intent=query일 때)"
    )
    error_message: str | None = Field(
        default=None, description="에러 메시지 (intent=unknown일 때)"
    )
