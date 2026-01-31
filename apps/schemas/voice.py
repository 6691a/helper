from dataclasses import dataclass

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field

from apps.types.voice import LanguageCode


@dataclass
class TranscribeRequest:
    """음성 인식 요청 (multipart/form-data)"""

    voice: UploadFile = File(description="음성 파일 (mp3, wav, m4a, webm, ogg, flac)")
    language: LanguageCode | None = Form(
        default=None,
        description="언어 코드. 미지정시 설정 기본값 사용",
    )
    detailed: bool = Form(default=False, description="세그먼트 포함 여부")


class TranscribeResponse(BaseModel):
    """음성 인식 응답"""

    text: str = Field(description="인식된 텍스트")
    language: LanguageCode = Field(description="사용된 언어 코드")
    confidence: float | None = Field(default=None, description="인식 신뢰도 (0.0 ~ 1.0)")


class TranscribeSegment(BaseModel):
    """음성 인식 세그먼트"""

    text: str = Field(description="세그먼트 텍스트")
    confidence: float | None = Field(default=None, description="세그먼트 신뢰도")


class TranscribeDetailedResponse(TranscribeResponse):
    """상세 음성 인식 응답 (세그먼트 포함)"""

    segments: list[TranscribeSegment] = Field(default_factory=list, description="인식 세그먼트 목록")


class StreamingTranscribeResponse(BaseModel):
    """스트리밍 음성 인식 응답 (WebSocket)"""

    text: str = Field(description="인식된 텍스트")
    is_final: bool = Field(description="최종 결과 여부")
    confidence: float | None = Field(default=None, description="인식 신뢰도")
