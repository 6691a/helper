from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from apps.models.base import BaseModel


class Memory(BaseModel, table=True):
    """통합 정보 기억 모델 - 물품, 장소, 일정, 인물, 메모 등 모든 정보 저장"""

    # 정보 유형: item, place, schedule, person, memo
    type: str = Field(max_length=50, nullable=False, index=True)

    # 검색용 키워드 (쉼표 구분)
    # 예: "척추 디스크, 비수술 치료, 디스크"
    keywords: str = Field(nullable=False)

    # AI가 정리한 핵심 내용
    # 예: "척추 디스크 치료는 광화문 자생한방병원에서..."
    content: str = Field(nullable=False)

    # 유형별 추가 정보 (JSONB)
    # item: {"location": "냉장고", "quantity": 5}
    # place: {"place": "자생한방병원", "method": "서대문역 6번"}
    metadata_: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("metadata", JSONB, nullable=True),
    )

    # 원본 입력 텍스트
    original_text: str = Field(nullable=False)

    # 임베딩 벡터 (pgvector)
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(1024)),
    )

    # 사용자 ID (멀티유저 지원 시)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
