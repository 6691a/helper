from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request, WebSocket
from fastapi.responses import JSONResponse
from starlette.authentication import requires

from apps.consumers.voice_stream_consumer import VoiceStreamConsumer
from apps.schemas.common import Response, ResponseProvider
from apps.schemas.voice import (
    TranscribeDetailedResponse,
    TranscribeRequest,
    TranscribeResponse,
)
from apps.services.streaming_voice import StreamingVoiceService
from apps.services.voice import VoiceService
from apps.services.voice_session import VoiceSessionService
from apps.types.voice import LanguageCode
from containers import Container

router = APIRouter(
    prefix="/api/v1/voice",
    tags=["voice"],
)


@router.post("/transcribe", response_model=Response[TranscribeResponse])
@inject
async def transcribe(
    voice_service: Annotated[
        VoiceService,
        Depends(Provide[Container.voice_service]),
    ],
    request: TranscribeRequest = Depends(),
) -> JSONResponse:
    """음성 파일을 텍스트로 변환합니다."""
    voice_service.validate_file(request.voice.filename or "", request.voice.size or 0)
    content = await request.voice.read()

    result: TranscribeResponse | TranscribeDetailedResponse = await voice_service.transcribe(
        audio_content=content,
        filename=request.voice.filename or "audio.wav",
        language=request.language,
        detailed=request.detailed,
    )
    return ResponseProvider.success(result)


@router.websocket("/stream")
@requires("authenticated")
@inject
async def stream_transcribe(
    websocket: WebSocket,
    request: Request,
    streaming_voice_service: Annotated[
        StreamingVoiceService,
        Depends(Provide[Container.streaming_voice_service]),
    ],
    voice_session_service: Annotated[
        VoiceSessionService,
        Depends(Provide[Container.voice_session_service]),
    ],
    language: LanguageCode | None = Query(default=None),
    sample_rate: int = Query(default=16000),
) -> None:
    """
    실시간 음성 인식 WebSocket 엔드포인트.

    - 클라이언트에서 오디오 청크(bytes)를 전송
    - 서버에서 실시간으로 인식 결과를 JSON으로 반환

    Query Parameters:
        language: 언어 코드 (ko-KR, en-US). 미지정시 설정 기본값 사용
        sample_rate: 샘플레이트 (기본 16000Hz)

    오디오 요구사항:
        - 포맷: LINEAR16 (PCM 16-bit)
        - 샘플레이트: 16000Hz (또는 query로 지정)
        - 채널: 모노
    """
    await websocket.accept()

    # 인증된 사용자 정보 추출
    user_id = request.user.user.id

    # Consumer 패턴으로 WebSocket 처리
    consumer = VoiceStreamConsumer(
        websocket=websocket,
        streaming_voice_service=streaming_voice_service,
        voice_session_service=voice_session_service,
        user_id=user_id,
        language=language,
        sample_rate=sample_rate,
    )
    await consumer.handle()
