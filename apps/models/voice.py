from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship

from apps.models.base import BaseModel

if TYPE_CHECKING:
    from apps.models.conversation import Conversation


class VoiceSession(BaseModel, table=True):
    """음성 세션 모델 - STT 결과 및 사용자 확인 저장"""

    __tablename__ = "voice_session"

    session_id: UUID = Field(
        default_factory=uuid4,
        unique=True,
        nullable=False,
        index=True,
        description="세션 고유 식별자",
    )
    user_id: int = Field(
        foreign_key="user.id",
        nullable=False,
        description="사용자 ID",
    )
    audio_path: str = Field(
        sa_column=Column(String(500), nullable=False),
        description="서버에 저장된 오디오 파일 경로",
    )
    stt_text: str = Field(
        nullable=False,
        description="STT 원본 결과 텍스트",
    )
    stt_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="STT 신뢰도 (0.0-1.0)",
    )
    user_confirmed_text: str | None = Field(
        default=None,
        nullable=True,
        description="사용자가 확인/수정한 최종 텍스트",
    )

    # Relationships
    conversation: Conversation | None = Relationship(
        back_populates="voice_session",
        sa_relationship_kwargs={"uselist": False},
    )
