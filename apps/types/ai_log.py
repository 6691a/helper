"""AI 로그 관련 타입 정의"""

from enum import Enum


class AILogStep(str, Enum):
    """AI 처리 단계"""

    INTENT_CLASSIFICATION = "intent_classification"
    TEXT_PARSING = "text_parsing"
    ANSWER_GENERATION = "answer_generation"
