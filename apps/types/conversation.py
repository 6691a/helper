from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from apps.types.assistant import IntentType


class Intent(BaseModel):
    """의도 분류 결과"""

    type: IntentType = Field(description="의도 타입 (save/query/unknown)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="신뢰도 (0.0-1.0)")


@dataclass
class ExtractedConversationData:
    """Assistant 응답에서 추출한 대화 데이터"""

    intent: Intent
    assistant_text: str
    parsed_data: dict[str, Any]
    memory_ids: list[int]
    reminder_ids: list[int]
