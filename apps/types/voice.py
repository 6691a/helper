from pydantic import BaseModel, Field


class VoiceConfig(BaseModel):
    """음성 인식 설정"""

    project_id: str = Field(description="GCP 프로젝트 ID")
    language: str = Field(description="기본 언어 코드")
    max_file_size_mb: int = Field(ge=1, le=100, description="최대 파일 크기 (MB)")
    supported_formats: list[str] = Field(description="지원 오디오 포맷")
    credentials_path: str | None = Field(
        default=None, description="GCP 서비스 계정 키 파일 경로"
    )
