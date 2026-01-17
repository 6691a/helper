from datetime import date
from datetime import time as _time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# Enums
# ============================================================


class IntentType(str, Enum):
    """사용자 의도 유형"""

    SAVE = "save"
    QUERY = "query"
    UNKNOWN = "unknown"


class MemoryType(str, Enum):
    """Memory 정보 유형"""

    ITEM = "item"  # 물건 위치/보관
    PLACE = "place"  # 장소/가는 방법
    SCHEDULE = "schedule"  # 일정/약속
    PERSON = "person"  # 인물 정보
    MEMO = "memo"  # 기타 메모


class ReminderFrequency(str, Enum):
    """알림 반복 주기"""

    ONCE = "once"  # 1회성
    DAILY = "daily"  # 매일
    WEEKLY = "weekly"  # 매주
    MONTHLY = "monthly"  # 매월


class Weekday(str, Enum):
    """요일"""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# ============================================================
# LLM Structured Output Models
# ============================================================


class IntentClassification(BaseModel):
    """LLM 의도 분류 결과 (with_structured_output용)"""

    intent: IntentType = Field(description="분류된 의도")
    reason: str = Field(description="판단 이유")


class ReminderInfo(BaseModel):
    """알림 정보 (with_structured_output용)"""

    frequency: ReminderFrequency = Field(description="알림 반복 주기")
    weekday: Weekday | None = Field(
        default=None,
        description="요일 (frequency=weekly일 때 필수)",
    )
    day_of_month: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="매월 몇 일 (frequency=monthly일 때 필수, 1~31)",
    )
    specific_date: date | None = Field(
        default=None,
        description="특정 일자 (frequency=once일 때 필수)",
    )
    time: _time | None = Field(
        default=None,
        description="알림 시간",
    )


class ParsedMemory(BaseModel):
    """LLM 텍스트 파싱 결과 (with_structured_output용)"""

    type: MemoryType = Field(description="정보 유형")
    keywords: str = Field(description="검색용 키워드, 쉼표로 구분")
    content: str = Field(description="AI가 정리한 핵심 내용 한두 문장")
    metadata: dict[str, Any] | None = Field(
        default=None, description="유형별 추가 정보"
    )
    reminder: ReminderInfo | None = Field(
        default=None,
        description="알림 설정 (알려줘, 리마인드 등 알림 요청이 있을 때만)",
    )


# ============================================================
# Config
# ============================================================


class AssistantConfig(BaseModel):
    """AI Assistant 설정 (LangChain + Gemini)"""

    api_key: str = Field(description="Google AI (Gemini) API Key")
    model: str = Field(description="LLM 모델명")
    embedding_model: str = Field(description="임베딩 모델명")
    embedding_dimensions: int = Field(description="임베딩 벡터 차원 (최대 3072)")
    temperature: float = Field(ge=0, le=1, description="LLM 온도")
    max_tokens: int = Field(ge=1, description="최대 토큰 수")
