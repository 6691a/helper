from enum import Enum

from pydantic import BaseModel, Field


class LanguageCode(str, Enum):
    """지원 언어 코드"""

    KO_KR = "ko-KR"  # 한국어
    EN_US = "en-US"  # 영어 (미국)


class AudioFormat(str, Enum):
    """지원 오디오 포맷"""

    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    WEBM = "webm"
    OGG = "ogg"
    FLAC = "flac"


class SpeechModel(str, Enum):
    """Speech-to-Text 모델"""

    SHORT = "short"  # 1분 이하 오디오
    LONG = "long"  # 장시간 오디오


class VoiceConfig(BaseModel):
    """음성 인식 설정"""

    project_id: str = Field(description="GCP 프로젝트 ID")
    language: LanguageCode = Field(description="기본 언어 코드")
    max_file_size_mb: int = Field(ge=1, le=100, description="최대 파일 크기 (MB)")
    supported_formats: list[AudioFormat] = Field(description="지원 오디오 포맷")
    credentials_path: str | None = Field(
        default=None, description="GCP 서비스 계정 키 파일 경로"
    )
