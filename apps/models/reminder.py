from datetime import date, datetime
from datetime import time as _time
from typing import TYPE_CHECKING

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

    # Memory 연결 (알림 대상 정보)
    memory_id: int = Field(foreign_key="memory.id", nullable=False, index=True)
    memory: "Memory" = Relationship()
    # 반복 주기
    frequency: ReminderFrequency = Field(nullable=False)

    # 요일 (frequency=weekly일 때)
    weekday: Weekday | None = Field(default=None)

    # 매월 몇 일 (frequency=monthly일 때)
    day_of_month: int | None = Field(default=None, ge=1, le=31)

    # 특정 일자 (frequency=once일 때)
    specific_date: date | None = Field(default=None)

    # 알림 시간
    time: _time = Field(default=_time(9, 0), nullable=False)

    # 다음 실행 시각 (Celery Beat 스케줄링용)
    next_run_at: datetime | None = Field(default=None, index=True)

    # 상태
    status: ReminderStatus = Field(default=ReminderStatus.ACTIVE, nullable=False, index=True)

    # 사용자 ID
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)

    # Relationships
    conversations: list[Conversation] = Relationship(
        back_populates="reminders",
        link_model=ConversationReminderLink,
    )
