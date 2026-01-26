from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON
from sqlmodel import Field, Relationship

from apps.models.base import BaseModel
from apps.models.links import ConversationMemoryLink, ConversationReminderLink
from apps.types.conversation import Intent

if TYPE_CHECKING:
    from apps.models.memory import Memory
    from apps.models.reminder import Reminder
    from apps.models.voice import VoiceSession


class Conversation(BaseModel, table=True):
    """대화 처리 결과 모델 - AI 처리 및 생성된 데이터 관계 저장"""

    __tablename__ = "conversation"

    voice_session_id: int = Field(
        foreign_key="voice_session.id",
        unique=True,
        nullable=False,
        index=True,
        description="연결된 음성 세션 ID (1:1)",
    )
    user_id: int = Field(
        foreign_key="user.id",
        nullable=False,
        description="사용자 ID",
    )
    intent: Intent = Field(
        sa_type=JSON,
        description="의도 분류 결과",
    )
    parsed_data: dict[str, Any] = Field(
        sa_type=JSON,
        default_factory=dict,
        description="파싱된 데이터 (예: {title: '...', content: '...', tags: [...]})",
    )
    assistant_response: str = Field(
        nullable=False,
        description="AI 어시스턴트 응답 텍스트",
    )

    # Relationships
    voice_session: "VoiceSession" = Relationship(
        back_populates="conversation",
    )
    memories: list["Memory"] = Relationship(
        back_populates="conversations",
        link_model=ConversationMemoryLink,
    )
    reminders: list["Reminder"] = Relationship(
        back_populates="conversations",
        link_model=ConversationReminderLink,
    )
