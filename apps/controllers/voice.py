from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.schemas.common import Response, ResponseProvider
from apps.schemas.voice import (
    TranscribeRequest,
    TranscribeResponse,
    TranscribeDetailedResponse,
)
from apps.services.voice import VoiceService
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

    result: (
        TranscribeResponse | TranscribeDetailedResponse
    ) = await voice_service.transcribe(
        audio_content=content,
        filename=request.voice.filename or "audio.wav",
        language=request.language,
        detailed=request.detailed,
    )
    return ResponseProvider.success(result)
