"""AI 처리 로그 모델"""

from typing import Any

from sqlalchemy import JSON, Text
from sqlmodel import Field

from apps.models.base import BaseModel


class AIProcessingLog(BaseModel, table=True):
    """AI 처리 단계별 로그 - 디버깅 및 성능 분석용"""

    __tablename__ = "ai_processing_log"

    # 연결된 Conversation (nullable - Conversation 생성 전 로그도 있을 수 있음)
    conversation_id: int | None = Field(
        default=None,
        foreign_key="conversation.id",
        index=True,
        description="연결된 Conversation ID",
    )

    # 사용자 ID
    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        index=True,
        description="사용자 ID",
    )

    # AI 처리 단계
    step: str = Field(
        max_length=50,
        index=True,
        description="처리 단계 (intent_classification, text_parsing, answer_generation)",
    )

    # 입력 텍스트
    input_text: str = Field(
        sa_type=Text,
        description="AI에 입력된 텍스트",
    )

    # AI 출력 결과
    output_data: dict[str, Any] = Field(
        sa_type=JSON,
        default_factory=dict,
        description="AI 응답 데이터 (JSON)",
    )

    # 모델 정보
    model_name: str | None = Field(
        default=None,
        max_length=100,
        description="사용된 AI 모델명",
    )

    # 처리 시간 (밀리초)
    processing_time_ms: int | None = Field(
        default=None,
        description="처리 소요 시간 (ms)",
    )
