from typing import Any

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    """Memory 생성 요청 (AI가 파싱한 결과)"""

    type: str = Field(description="정보 유형: item, place, schedule, person, memo")
    keywords: str = Field(description="검색용 키워드 (쉼표 구분)")
    content: str = Field(description="AI가 정리한 핵심 내용")
    metadata_: dict[str, Any] | None = Field(
        default=None, description="유형별 추가 정보"
    )
    original_text: str = Field(description="원본 입력 텍스트")


class MemoryUpdate(BaseModel):
    """Memory 수정 요청"""

    type: str | None = Field(default=None, description="정보 유형")
    keywords: str | None = Field(default=None, description="검색용 키워드")
    content: str | None = Field(default=None, description="핵심 내용")
    metadata_: dict[str, Any] | None = Field(default=None, description="추가 정보")


class MemoryResponse(BaseModel):
    """Memory 응답"""

    id: int = Field(description="Memory ID")
    type: str = Field(description="정보 유형")
    keywords: str = Field(description="검색용 키워드")
    content: str = Field(description="핵심 내용")
    metadata_: dict[str, Any] | None = Field(default=None, description="추가 정보")
    original_text: str = Field(description="원본 입력 텍스트")

    model_config = {"from_attributes": True}


class MemorySearchResult(BaseModel):
    """Memory 검색 결과 (유사도 포함)"""

    memory: MemoryResponse = Field(description="Memory 정보")
    similarity: float = Field(description="유사도 점수 (0.0 ~ 1.0)")
