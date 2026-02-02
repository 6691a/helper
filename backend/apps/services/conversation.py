import logging
from typing import Any
from uuid import UUID

from apps.exceptions import NotFoundError
from apps.models.conversation import Conversation
from apps.models.voice import VoiceSession
from apps.repositories.conversation import ConversationRepository
from apps.schemas.assistant import AssistantResponse
from apps.schemas.conversation import ConversationResponse, ProcessVoiceRequest
from apps.services.assistant import AssistantService
from apps.services.voice_session import VoiceSessionService
from apps.types.assistant import IntentType
from apps.types.conversation import ExtractedConversationData, Intent
from database import transactional

logger = logging.getLogger(__name__)


class ConversationService:
    """대화 처리 서비스 - VoiceSession과 AssistantService를 연결"""

    def __init__(
        self,
        voice_session_service: VoiceSessionService,
        conversation_repository: ConversationRepository,
        assistant_service: AssistantService,
    ):
        self.voice_session_service = voice_session_service
        self.conversation_repository = conversation_repository
        self.assistant_service = assistant_service

    @transactional
    async def process_voice(self, request: ProcessVoiceRequest, user_id: int) -> ConversationResponse:
        """음성 세션을 처리하여 대화 기록을 생성합니다. (트랜잭션 적용)"""
        voice_session = await self._get_voice_session(request.session_id, user_id)
        final_text = self._determine_final_text(request.text, voice_session)
        await self._update_voice_session_confirmation(voice_session, final_text)

        assistant_response = await self.assistant_service.process(final_text, user_id)
        extracted = self._extract_result_data(assistant_response)

        voice_session_id = voice_session.id
        if voice_session_id is None:
            raise ValueError("VoiceSession ID should not be None")

        conversation = await self._create_conversation_record(
            voice_session_id=voice_session_id,
            user_id=user_id,
            intent=extracted.intent,
            parsed_data=extracted.parsed_data,
            assistant_text=extracted.assistant_text,
            memory_ids=extracted.memory_ids,
            reminder_ids=extracted.reminder_ids,
        )

        conversation_id = conversation.id
        if conversation_id is None:
            raise ValueError("Conversation ID should not be None after creation")

        return ConversationResponse(
            conversation_id=conversation_id,
            intent=extracted.intent,
            assistant_response=extracted.assistant_text,
            created_memory_ids=extracted.memory_ids,
            created_reminder_ids=extracted.reminder_ids,
        )

    async def _get_voice_session(self, session_id: UUID, user_id: int) -> VoiceSession:
        """VoiceSession을 조회하고 권한을 검증합니다."""
        voice_session = await self.voice_session_service.get_by_session_id(session_id)

        if not voice_session or voice_session.user_id != user_id:
            raise NotFoundError("VoiceSession not found")

        return voice_session

    def _determine_final_text(self, user_text: str | None, voice_session: VoiceSession) -> str:
        """최종 텍스트를 결정합니다 (사용자 수정본 or STT 원본)."""
        return user_text if user_text else voice_session.stt_text

    async def _update_voice_session_confirmation(self, voice_session: VoiceSession, final_text: str) -> None:
        """VoiceSession의 확인 상태를 업데이트합니다."""
        await self.voice_session_service.update_confirmation(voice_session, final_text)

    def _extract_result_data(self, assistant_response: AssistantResponse) -> ExtractedConversationData:
        """Assistant 응답에서 필요한 데이터를 추출합니다."""
        intent = Intent(type=assistant_response.intent)
        memory_ids: list[int] = []
        reminder_ids: list[int] = []
        assistant_text = ""
        parsed_data: dict[str, Any] = {}

        if assistant_response.intent == IntentType.SAVE:
            if assistant_response.save_result:
                memory_ids = [assistant_response.save_result.memory.id]
                if assistant_response.save_result.reminder:
                    reminder_ids = [assistant_response.save_result.reminder.id]
                assistant_text = assistant_response.save_result.message
                parsed_data = {
                    "type": assistant_response.save_result.memory.type.value,
                    "keywords": assistant_response.save_result.memory.keywords,
                    "content": assistant_response.save_result.memory.content,
                    "metadata": assistant_response.save_result.memory.metadata_,
                }
        elif assistant_response.intent == IntentType.QUERY:
            if assistant_response.query_result:
                assistant_text = assistant_response.query_result.answer
                parsed_data = {
                    "related_memory_ids": [
                        result.memory.id for result in assistant_response.query_result.related_memories
                    ]
                }
        else:
            assistant_text = assistant_response.error_message or "요청을 이해하지 못했습니다."

        return ExtractedConversationData(
            intent=intent,
            assistant_text=assistant_text,
            parsed_data=parsed_data,
            memory_ids=memory_ids,
            reminder_ids=reminder_ids,
        )

    async def _create_conversation_record(
        self,
        voice_session_id: int,
        user_id: int,
        intent: Intent,
        parsed_data: dict[str, Any],
        assistant_text: str,
        memory_ids: list[int],
        reminder_ids: list[int],
    ) -> Conversation:
        """Conversation 레코드를 생성하고 관계를 연결합니다."""
        conversation = Conversation(
            voice_session_id=voice_session_id,
            user_id=user_id,
            intent=intent.model_dump(mode="json"),
            parsed_data=parsed_data,
            assistant_response=assistant_text,
        )

        saved_conversation = await self.conversation_repository.create(
            conversation=conversation,
            memory_ids=memory_ids,
            reminder_ids=reminder_ids,
        )

        logger.info(
            f"Conversation created: id={saved_conversation.id}, "
            f"intent={intent.type}, "
            f"memories={len(memory_ids)}, "
            f"reminders={len(reminder_ids)}"
        )

        return saved_conversation
