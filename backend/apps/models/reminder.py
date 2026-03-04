from datetime import date, datetime
from datetime import time as _time
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Time as SATime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, Relationship

from apps.models import Memory
from apps.models.base import BaseModel
from apps.models.links import ConversationReminderLink
from apps.types.assistant import ReminderFrequency, Weekday
from apps.types.reminder import ReminderStatus

if TYPE_CHECKING:
    from apps.models.conversation import Conversation


class Reminder(BaseModel, table=True):
    """알림 스케줄 모델"""

    # Memory 연결 (알림 대상 정보) - CASCADE 삭제
    memory_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("memory.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    memory: "Memory" = Relationship()
    # 반복 주기
    frequency: ReminderFrequency = Field(nullable=False)

    # 요일 목록 (frequency=weekly일 때, 복수 선택 가능)
    weekdays: list[Weekday] = Field(
        sa_column=Column(ARRAY(String()), nullable=False, server_default="{}"),
        default_factory=list,
    )

    # 매월 몇 일 (frequency=monthly일 때)
    day_of_month: int | None = Field(default=None, ge=1, le=31)

    # 특정 일자 (frequency=once일 때)
    specific_date: date | None = Field(default=None)

    # 알림 시간
    time: _time = Field(
        sa_column=Column(SATime(), nullable=False),
        default=_time(9, 0),
    )

    # 다음 실행 시각 (Celery Beat 스케줄링용)
    next_run_at: datetime | None = Field(  # type: ignore[call-overload]
        default=None,
        sa_type=DateTime(timezone=True),
        index=True,
    )

    # 상태
    status: ReminderStatus = Field(default=ReminderStatus.ACTIVE, nullable=False, index=True)

    # 사용자 ID
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)

    # Relationships
    conversations: list["Conversation"] = Relationship(
        back_populates="reminders",
        link_model=ConversationReminderLink,
    )
