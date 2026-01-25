import logging
from uuid import UUID

from apps.models.voice import VoiceSession
from apps.repositories.voice import VoiceSessionRepository

logger = logging.getLogger(__name__)


class VoiceSessionService:
    """VoiceSession 비즈니스 로직 서비스"""

    def __init__(self, voice_session_repository: VoiceSessionRepository):
        self.repository = voice_session_repository

    async def create_session(
        self,
        user_id: int,
        audio_path: str,
        stt_text: str,
        stt_confidence: float,
    ) -> VoiceSession:
        """VoiceSession을 생성합니다."""
        voice_session = VoiceSession(
            user_id=user_id,
            audio_path=audio_path,
            stt_text=stt_text,
            stt_confidence=stt_confidence,
        )

        saved_session = await self.repository.create(voice_session)

        logger.info(
            f"VoiceSession created: id={saved_session.id}, session_id={saved_session.session_id}, user_id={user_id}"
        )

        return saved_session

    async def get_by_session_id(self, session_id: UUID) -> VoiceSession | None:
        """session_id로 VoiceSession을 조회합니다."""
        return await self.repository.get_by_session_id(session_id)

    async def update_confirmation(self, voice_session: VoiceSession, confirmed_text: str) -> VoiceSession:
        """사용자 확인 텍스트를 업데이트합니다."""
        voice_session.user_confirmed_text = confirmed_text
        return await self.repository.update(voice_session)
