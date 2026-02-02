from pathlib import Path

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account

from apps.exceptions import VoiceProcessingError
from apps.i18n import _
from apps.schemas.voice import (
    TranscribeDetailedResponse,
    TranscribeResponse,
    TranscribeSegment,
)
from apps.types.voice import LanguageCode, SpeechModel, VoiceConfig


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
        supported_values = [fmt.value for fmt in self.config.supported_formats]
        if ext not in supported_values:
            raise VoiceProcessingError(
                _("Unsupported format: {}. Supported: {}").format(ext, ", ".join(supported_values))
            )

        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise VoiceProcessingError(
                _("File too large: {:.1f}MB. Max: {}MB").format(file_size / 1024 / 1024, self.config.max_file_size_mb)
            )

    async def transcribe(
        self,
        audio_content: bytes,
        filename: str,
        language: LanguageCode | None = None,
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
        used_language = language or self.config.language
        response = self._recognize(audio_content, used_language)
        return self._build_response(response, used_language, detailed)

    def _build_recognition_config(self, language: LanguageCode) -> cloud_speech.RecognitionConfig:
        """Recognition 설정을 생성합니다."""
        return cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=[language.value],
            model=SpeechModel.LATEST_LONG.value,  # 최신 장시간 오디오 모델
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
            ),
        )

    def _recognize(self, audio_content: bytes, language: LanguageCode) -> cloud_speech.RecognizeResponse:
        """Google Speech API를 호출합니다."""
        config = self._build_recognition_config(language)
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{self.config.project_id}/locations/global/recognizers/_",
            config=config,
            content=audio_content,
        )

        try:
            return self.client.recognize(request=request)
        except Exception as e:
            raise VoiceProcessingError(_("Speech recognition failed: {}").format(e)) from e

    def _build_response(
        self,
        response: cloud_speech.RecognizeResponse,
        language: LanguageCode,
        detailed: bool,
    ) -> TranscribeResponse | TranscribeDetailedResponse:
        """API 응답을 TranscribeResponse로 변환합니다."""
        if not response.results:
            return TranscribeResponse(text="", language=language, confidence=None)

        texts, confidences, segments = self._extract_results(response)
        full_text = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        if detailed:
            return TranscribeDetailedResponse(
                text=full_text,
                language=language,
                confidence=avg_confidence,
                segments=segments,
            )

        return TranscribeResponse(
            text=full_text,
            language=language,
            confidence=avg_confidence,
        )

    def _extract_results(
        self, response: cloud_speech.RecognizeResponse
    ) -> tuple[list[str], list[float], list[TranscribeSegment]]:
        """API 응답에서 텍스트, 신뢰도, 세그먼트를 추출합니다."""
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

        return texts, confidences, segments
