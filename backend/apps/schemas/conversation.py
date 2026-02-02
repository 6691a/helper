from uuid import UUID

from pydantic import BaseModel, Field

from apps.types.conversation import Intent


class ProcessVoiceRequest(BaseModel):
    """음성 처리 요청"""

    session_id: UUID = Field(description="VoiceSession UUID")
    text: str | None = Field(
        default=None,
        description="사용자가 수정한 텍스트 (없으면 STT 원본 사용)",
    )


class ConversationResponse(BaseModel):
    """대화 처리 결과 응답"""

    conversation_id: int = Field(description="생성된 Conversation ID")
    intent: Intent = Field(description="분류된 의도")
    assistant_response: str = Field(description="AI 어시스턴트 응답")
    created_memory_ids: list[int] = Field(default_factory=list, description="생성된 Memory ID 목록")
    created_reminder_ids: list[int] = Field(default_factory=list, description="생성된 Reminder ID 목록")
