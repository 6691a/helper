from datetime import date, datetime
from datetime import time as _time

from pydantic import BaseModel, Field, model_validator

from apps.types.assistant import ReminderFrequency, Weekday
from apps.types.reminder import ReminderStatus


class ReminderCreate(BaseModel):
    """Reminder 생성 요청"""

    memory_id: int = Field(description="알림 대상 Memory ID")
    frequency: ReminderFrequency = Field(description="반복 주기")
    weekday: Weekday | None = Field(default=None, description="요일 (frequency=weekly일 때)")
    day_of_month: int | None = Field(default=None, ge=1, le=31, description="매월 몇 일 (frequency=monthly일 때)")
    specific_date: date | None = Field(default=None, description="특정 일자 (frequency=once일 때)")
    time: _time = Field(default=_time(9, 0), description="알림 시간")

    @model_validator(mode="after")
    def validate_frequency_fields(self) -> "ReminderCreate":
        """frequency에 따른 필드 일관성 검증"""
        if self.frequency == ReminderFrequency.WEEKLY and self.weekday is None:
            raise ValueError("weekly 주기는 weekday가 필수입니다.")

        if self.frequency == ReminderFrequency.MONTHLY and self.day_of_month is None:
            raise ValueError("monthly 주기는 day_of_month가 필수입니다.")

        if self.frequency == ReminderFrequency.ONCE and self.specific_date is None:
            raise ValueError("once 주기는 specific_date가 필수입니다.")

        return self


class ReminderUpdate(BaseModel):
    """Reminder 수정 요청"""

    frequency: ReminderFrequency | None = Field(default=None, description="반복 주기")
    weekday: Weekday | None = Field(default=None, description="요일")
    day_of_month: int | None = Field(default=None, ge=1, le=31, description="매월 몇 일")
    specific_date: date | None = Field(default=None, description="특정 일자")
    time: _time | None = Field(default=None, description="알림 시간")
    status: ReminderStatus | None = Field(default=None, description="상태")

    @model_validator(mode="after")
    def validate_frequency_fields(self) -> "ReminderUpdate":
        """frequency에 따른 필드 일관성 검증"""
        if self.frequency is None:
            return self

        if self.frequency == ReminderFrequency.WEEKLY and self.weekday is None:
            raise ValueError("weekly 주기는 weekday가 필수입니다.")

        if self.frequency == ReminderFrequency.MONTHLY and self.day_of_month is None:
            raise ValueError("monthly 주기는 day_of_month가 필수입니다.")

        if self.frequency == ReminderFrequency.ONCE and self.specific_date is None:
            raise ValueError("once 주기는 specific_date가 필수입니다.")

        return self


class ReminderResponse(BaseModel):
    """Reminder 응답"""

    id: int = Field(description="Reminder ID")
    memory_id: int = Field(description="알림 대상 Memory ID")
    frequency: ReminderFrequency = Field(description="반복 주기")
    weekday: Weekday | None = Field(description="요일")
    day_of_month: int | None = Field(description="매월 몇 일")
    specific_date: date | None = Field(description="특정 일자")
    time: _time = Field(description="알림 시간")
    next_run_at: datetime | None = Field(description="다음 실행 시각")
    status: ReminderStatus = Field(description="상태")
    created_at: datetime = Field(description="생성일시")
    updated_at: datetime = Field(description="수정일시")

    model_config = {"from_attributes": True}
