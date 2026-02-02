"""WebSocket 음성 스트리밍 Consumer (Django Channels 패턴)"""

import asyncio
import json
import logging
import wave
from collections.abc import AsyncGenerator, MutableMapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from apps.models.voice import VoiceSession
from apps.services.streaming_voice import StreamingVoiceService
from apps.services.voice_session import VoiceSessionService
from apps.types.voice import LanguageCode
from settings import Settings

logger = logging.getLogger(__name__)


class VoiceStreamConsumer:
    """
    실시간 음성 인식 WebSocket Consumer

    Django Channels의 Consumer 패턴을 따라 설계되었습니다.
    """

    # WAV 파일 저장 설정
    WAV_CHANNELS = 1  # 모노
    WAV_SAMPLE_WIDTH = 2  # 16-bit (2 bytes)

    # 오디오 큐 타임아웃 (초)
    AUDIO_QUEUE_TIMEOUT = 30.0

    def __init__(
        self,
        websocket: WebSocket,
        streaming_voice_service: StreamingVoiceService,
        voice_session_service: VoiceSessionService,
        user_id: int,
        language: LanguageCode | None,
        sample_rate: int,
    ):
        """
        Consumer 초기화

        Args:
            websocket: FastAPI WebSocket 연결
            streaming_voice_service: 음성 인식 서비스
            voice_session_service: VoiceSession 서비스
            user_id: 사용자 ID
            language: 언어 코드
            sample_rate: 샘플레이트 (Hz)
        """
        self.websocket = websocket
        self.streaming_voice_service = streaming_voice_service
        self.voice_session_service = voice_session_service
        self.user_id = user_id
        self.language = language
        self.sample_rate = sample_rate

        # 상태 관리
        self.audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self.audio_chunks: list[bytes] = []
        self.is_streaming = True
        self.session_id = uuid4()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # STT 결과 저장
        self.final_transcript = ""
        self.final_confidence = 0.0

        # WebSocket 상태
        self._websocket_closed = False

    async def handle(self) -> None:
        """
        메인 핸들러 메서드 (Django Channels의 Consumer.receive와 유사)

        WebSocket 연결을 처리하고 오디오 수신/전송 태스크를 관리합니다.
        """
        receive_task = asyncio.create_task(self._receive_audio())
        send_task = asyncio.create_task(self._send_results())

        try:
            await asyncio.gather(receive_task, send_task)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.exception(e)
        finally:
            await self._cleanup(receive_task, send_task)

    async def _receive_audio(self) -> None:
        """
        WebSocket에서 오디오 바이트를 수신합니다.

        클라이언트는 오디오 바이트를 전송하고,
        녹음 종료 시 {"type": "stop"} JSON 메시지를 전송합니다.
        """
        try:
            while self.is_streaming:
                message = await self.websocket.receive()

                if message["type"] == "websocket.disconnect":
                    self._websocket_closed = True
                    break

                if message["type"] != "websocket.receive":
                    continue

                should_stop = await self._process_websocket_message(message)
                if should_stop:
                    break

        except WebSocketDisconnect:
            self._websocket_closed = True
        finally:
            self.is_streaming = False
            await self.audio_queue.put(None)

    async def _process_websocket_message(self, message: MutableMapping[str, Any]) -> bool:
        """
        WebSocket 메시지를 처리합니다.

        Returns:
            True if should stop receiving, False otherwise
        """
        # 오디오 바이너리 데이터 처리
        if "bytes" in message and message["bytes"]:
            await self._handle_audio_data(message["bytes"])
            return False

        # JSON 텍스트 메시지 처리
        if "text" in message and message["text"]:
            return self._handle_text_message(message["text"])

        return False

    async def _handle_audio_data(self, audio_data: bytes) -> None:
        """오디오 데이터를 처리하고 큐에 추가합니다."""
        self.audio_chunks.append(audio_data)

        if self.streaming_voice_service.has_audio_signal(audio_data):
            await self.audio_queue.put(audio_data)

    def _handle_text_message(self, text: str) -> bool:
        """
        텍스트 메시지를 처리합니다.

        Returns:
            True if stop signal received, False otherwise
        """
        try:
            data = json.loads(text)
            if data.get("type") == "stop":
                logger.info(f"Stop signal received: session_id={self.session_id}")
                return True
        except json.JSONDecodeError:
            logger.debug(f"Invalid JSON message received: {text[:100]}")
        return False

    async def _send_results(self) -> None:
        """
        음성 인식 결과를 WebSocket으로 전송합니다.
        """

        logging.info(f"📤 _send_results 시작 - session_id={self.session_id}")

        try:
            # 첫 번째 유효한 오디오 청크 대기
            chunk = await self.audio_queue.get()
            if chunk is None:
                return

            # Google Cloud API 스트리밍 시작
            async for result in self.streaming_voice_service.stream_transcribe(
                audio_generator=self._audio_generator(chunk),
                language=self.language,
                sample_rate=self.sample_rate,
            ):
                # Final result 저장
                if result.is_final:
                    self.final_transcript = result.text
                    self.final_confidence = result.confidence or 0.0

                # STT 결과 전송 (WebSocket이 열려있을 때만)
                if not self._websocket_closed:
                    try:
                        await self.websocket.send_json(result.model_dump())
                    except Exception:
                        self._websocket_closed = True
        except Exception as e:
            logger.error(
                f"❌ 음성 인식 에러 - session_id={self.session_id}, error={e}",
                exc_info=True,
            )
            await self._send_error(str(e))
        finally:
            self.is_streaming = False

    async def _audio_generator(self, first_chunk: bytes) -> AsyncGenerator[bytes]:
        """
        오디오 청크를 생성하는 비동기 제너레이터

        Args:
            first_chunk: 첫 번째 오디오 청크

        Yields:
            오디오 청크 (bytes)
        """
        # 첫 번째 청크 전송
        yield first_chunk

        # 이후 큐에서 계속 가져옴
        while self.is_streaming:
            try:
                chunk = await asyncio.wait_for(
                    self.audio_queue.get(),
                    timeout=self.AUDIO_QUEUE_TIMEOUT,
                )
                if chunk is None:
                    break
                yield chunk
            except TimeoutError:
                logger.warning(f"Audio queue timeout: session_id={self.session_id}")
                break

    async def _cleanup(
        self,
        receive_task: asyncio.Task[Any],
        send_task: asyncio.Task[Any],
    ) -> None:
        """리소스 정리 및 종료 처리"""
        await self._cancel_tasks(receive_task, send_task)
        audio_path = await self._save_audio()

        if audio_path and self.final_transcript:
            voice_session = await self._create_voice_session(audio_path)
            if voice_session and not self._websocket_closed:
                await self._send_session_created_notification()
        elif not self._websocket_closed:
            # No speech detected - send empty result
            await self._send_no_speech_notification()

        await self._close_websocket()

    async def _cancel_tasks(self, receive_task: asyncio.Task[Any], send_task: asyncio.Task[Any]) -> None:
        """실행 중인 태스크를 취소합니다."""
        self.is_streaming = False
        for task in [receive_task, send_task]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _save_audio(self) -> str | None:
        """
        오디오 파일을 WAV 형식으로 저장합니다.

        Returns:
            저장된 파일 경로 (실패 시 None)
        """
        if not self.audio_chunks:
            return None

        try:
            # recordings 디렉토리 생성
            recordings_dir = Settings.root_dir / "recordings"
            recordings_dir.mkdir(exist_ok=True)

            # 파일명: {timestamp}_{session_id}_{language}.wav
            lang_code = self.language.value if self.language else "ko-KR"
            filename = f"{self.timestamp}_{self.session_id}_{lang_code}.wav"
            filepath = recordings_dir / filename

            # WAV 파일로 저장
            with wave.open(str(filepath), "wb") as wav_file:
                wav_file.setnchannels(self.WAV_CHANNELS)
                wav_file.setsampwidth(self.WAV_SAMPLE_WIDTH)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(b"".join(self.audio_chunks))

            audio_path = str(filepath)
            logger.info(f"Audio saved: {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"Failed to save audio file: {e}", exc_info=True)
            return None

    async def _create_voice_session(self, audio_path: str) -> VoiceSession | None:
        """
        VoiceSession을 생성합니다.

        Returns:
            생성된 VoiceSession (실패 시 None)
        """
        try:
            saved_session = await self.voice_session_service.create_session(
                user_id=self.user_id,
                audio_path=audio_path,
                stt_text=self.final_transcript,
                stt_confidence=self.final_confidence,
                session_id=self.session_id,
            )
            return saved_session

        except Exception as e:
            logger.error(f"Failed to create VoiceSession: {e}", exc_info=True)
            return None

    async def _send_session_created_notification(self) -> None:
        """클라이언트에게 session_id를 전송합니다."""
        if self._websocket_closed:
            return

        try:
            await self.websocket.send_json(
                {
                    "type": "session_created",
                    "session_id": str(self.session_id),
                    "transcript": self.final_transcript,
                    "confidence": self.final_confidence,
                }
            )
        except Exception as e:
            self._websocket_closed = True
            logger.warning(f"Failed to send session created notification: {e}")

    async def _send_no_speech_notification(self) -> None:
        """음성이 감지되지 않았음을 클라이언트에게 알립니다."""
        if self._websocket_closed:
            return

        try:
            await self.websocket.send_json(
                {
                    "type": "no_speech",
                    "message": "음성이 감지되지 않았습니다",
                }
            )
        except Exception as e:
            self._websocket_closed = True
            logger.warning(f"Failed to send no speech notification: {e}")

    async def _send_error(self, error_message: str) -> None:
        """
        에러 메시지를 전송합니다.

        Args:
            error_message: 에러 메시지
        """
        if self._websocket_closed:
            return

        try:
            await self.websocket.send_json({"error": error_message})
        except Exception as e:
            self._websocket_closed = True
            logger.warning(f"Failed to send error message: {e}")

    async def _close_websocket(self) -> None:
        """WebSocket 연결을 종료합니다."""
        if self._websocket_closed:
            return

        self._websocket_closed = True
        try:
            await self.websocket.close()
        except Exception as e:
            logger.warning(f"Failed to close websocket: {e}")
