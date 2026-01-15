from pathlib import Path

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account

from apps.exceptions import VoiceProcessingError
from apps.i18n import _
from apps.schemas.voice import (
    TranscribeResponse,
    TranscribeDetailedResponse,
    TranscribeSegment,
)
from apps.types.voice import VoiceConfig


class VoiceService:
    """음성 인식 서비스 (Google Cloud Speech-to-Text v2)"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self._client: SpeechClient | None = None

    @property
    def client(self) -> SpeechClient:
        """Speech 클라이언트 지연 로딩"""
        if self._client is None:
            if self.config.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
                    self.config.credentials_path
                )
                self._client = SpeechClient(credentials=credentials)
            else:
                self._client = SpeechClient()
        return self._client

    def validate_file(self, filename: str, file_size: int) -> None:
        """파일 유효성 검사"""
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in self.config.supported_formats:
            raise VoiceProcessingError(
                _("Unsupported format: {}. Supported: {}").format(
                    ext, ", ".join(self.config.supported_formats)
                )
            )

        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise VoiceProcessingError(
                _("File too large: {:.1f}MB. Max: {}MB").format(
                    file_size / 1024 / 1024, self.config.max_file_size_mb
                )
            )

    async def transcribe(
        self,
        audio_content: bytes,
        filename: str,
        language: str | None = None,
        detailed: bool = False,
    ) -> TranscribeResponse | TranscribeDetailedResponse:
        """
        음성을 텍스트로 변환합니다.

        Args:
            audio_content: 오디오 파일 바이너리
            filename: 파일명
            language: 언어 코드 (None이면 설정 기본값 사용)
            detailed: True면 세그먼트 포함 응답

        Returns:
            TranscribeResponse 또는 TranscribeDetailedResponse
        """
        language_code = language or self.config.language

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=[language_code],
            model="short",  # 1분 이하 오디오용, 더 빠름
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
            ),
        )

        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{self.config.project_id}/locations/global/recognizers/_",
            config=config,
            content=audio_content,
        )

        try:
            response = self.client.recognize(request=request)
        except Exception as e:
            raise VoiceProcessingError(
                _("Speech recognition failed: {}").format(e)
            ) from e

        # 결과 처리
        if not response.results:
            return TranscribeResponse(
                text="",
                language=language_code,
                confidence=None,
            )

        # 전체 텍스트 및 신뢰도 계산
        texts: list[str] = []
        confidences: list[float] = []
        segments: list[TranscribeSegment] = []

        for result in response.results:
            if result.alternatives:
                alt = result.alternatives[0]
                texts.append(alt.transcript)
                if alt.confidence:
                    confidences.append(alt.confidence)
                segments.append(
                    TranscribeSegment(
                        text=alt.transcript,
                        confidence=alt.confidence if alt.confidence else None,
                    )
                )

        full_text = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        if detailed:
            return TranscribeDetailedResponse(
                text=full_text,
                language=language_code,
                confidence=avg_confidence,
                segments=segments,
            )

        return TranscribeResponse(
            text=full_text,
            language=language_code,
            confidence=avg_confidence,
        )
