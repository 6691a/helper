import logging
import struct
from collections.abc import AsyncGenerator

from google.cloud.speech_v2 import SpeechAsyncClient
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account

from apps.schemas.voice import StreamingTranscribeResponse
from apps.types.voice import LanguageCode, SpeechModel, VoiceConfig

logger = logging.getLogger(__name__)


class StreamingVoiceService:
    """실시간 스트리밍 음성 인식 서비스 (Google Cloud Speech-to-Text v2)"""

    # 오디오 신호 감지 임계값 (RMS 평균 진폭)
    AUDIO_SILENCE_THRESHOLD = 100

    def __init__(self, config: VoiceConfig):
        self.config = config
        self._client: SpeechAsyncClient | None = None

    @property
    def client(self) -> SpeechAsyncClient:
        """Async Speech 클라이언트 지연 로딩"""
        if self._client is None:
            if self.config.credentials_path:
                credentials: service_account.Credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_path
                )
                self._client = SpeechAsyncClient(credentials=credentials)
            else:
                self._client = SpeechAsyncClient()
        return self._client

    def has_audio_signal(
        self,
        audio_bytes: bytes,
        threshold: int = AUDIO_SILENCE_THRESHOLD,
    ) -> bool:
        """
        오디오 데이터에 유효한 신호가 있는지 확인합니다.

        Args:
            audio_bytes: LINEAR16 (PCM 16-bit) 포맷의 오디오 데이터
            threshold: 무음 판정 임계값 (기본 100)

        Returns:
            True: 유효한 오디오 신호 존재
            False: 무음 또는 노이즈만 존재
        """
        if not audio_bytes or len(audio_bytes) < 2:
            return False

        # LINEAR16: 2바이트씩 int16 값으로 변환
        num_samples = len(audio_bytes) // 2
        samples = struct.unpack(f"<{num_samples}h", audio_bytes[: num_samples * 2])

        # 평균 절대값 계산 (RMS 대신 간단한 방법)
        avg_amplitude = sum(abs(sample) for sample in samples) / num_samples

        return avg_amplitude > threshold

    async def stream_transcribe(
        self,
        audio_generator: AsyncGenerator[bytes],
        language: LanguageCode | None = None,
        sample_rate: int = 16000,
    ) -> AsyncGenerator[StreamingTranscribeResponse]:
        """
        실시간 스트리밍 음성 인식을 수행합니다.

        Args:
            audio_generator: 오디오 청크를 생성하는 비동기 제너레이터
            language: 언어 코드 (None이면 설정 기본값 사용)
            sample_rate: 샘플레이트 (기본 16000Hz)

        Yields:
            StreamingTranscribeResponse: 실시간 인식 결과
        """
        used_language = language or self.config.language
        request_generator = self._create_request_generator(audio_generator, used_language, sample_rate)

        stream = await self.client.streaming_recognize(requests=request_generator)
        async for response in stream:
            for result in response.results:
                if not result.alternatives:
                    continue

                alt = result.alternatives[0]
                print(alt.transcript)
                yield StreamingTranscribeResponse(
                    text=alt.transcript,
                    is_final=result.is_final,
                    confidence=alt.confidence if alt.confidence else None,
                )

    async def _create_request_generator(
        self,
        audio_generator: AsyncGenerator[bytes],
        language: LanguageCode,
        sample_rate: int,
    ) -> AsyncGenerator[cloud_speech.StreamingRecognizeRequest]:
        """스트리밍 요청 제너레이터를 생성합니다."""
        # 첫 번째 요청: 설정 전송
        streaming_config = await self._build_streaming_config(language, sample_rate)
        yield cloud_speech.StreamingRecognizeRequest(
            recognizer=f"projects/{self.config.project_id}/locations/global/recognizers/_",
            streaming_config=streaming_config,
        )

        # 이후 요청: 오디오 청크 전송
        async for audio_chunk in audio_generator:
            yield cloud_speech.StreamingRecognizeRequest(audio=audio_chunk)

    async def _build_streaming_config(
        self, language: LanguageCode, sample_rate: int
    ) -> cloud_speech.StreamingRecognitionConfig:
        """스트리밍 Recognition 설정을 생성합니다."""
        recognition_config = cloud_speech.RecognitionConfig(
            explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                audio_channel_count=1,
            ),
            language_codes=[language.value],
            model=SpeechModel.LATEST_LONG.value,  # 스트리밍에 최적화된 최신 모델
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
            ),
        )

        return cloud_speech.StreamingRecognitionConfig(
            config=recognition_config,
            streaming_features=cloud_speech.StreamingRecognitionFeatures(
                interim_results=True,
            ),
        )
