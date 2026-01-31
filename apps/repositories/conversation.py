from sqlalchemy import desc
from sqlmodel import col, select

from apps.models.conversation import Conversation
from apps.models.links import ConversationMemoryLink, ConversationReminderLink
from database import Database


class ConversationRepository:
    """Conversation 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def get_by_id(self, conversation_id: int, user_id: int | None = None) -> Conversation | None:
        """ID로 Conversation을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            if user_id is not None:
                stmt = stmt.where(Conversation.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_voice_session_id(self, voice_session_id: int) -> Conversation | None:
        """VoiceSession ID로 Conversation을 조회합니다 (1:1)."""
        async with self.database.session() as session:
            stmt = select(Conversation).where(Conversation.voice_session_id == voice_session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[Conversation]:
        """사용자의 Conversation 목록을 조회합니다."""
        async with self.database.session() as session:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(col(Conversation.created_at)))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(
        self,
        conversation: Conversation,
        memory_ids: list[int] | None = None,
        reminder_ids: list[int] | None = None,
    ) -> Conversation:
        """Conversation을 생성하고 Memory/Reminder와 연결합니다."""
        async with self.database.session() as session:
            session.add(conversation)
            await session.flush()

            conversation_id = conversation.id
            if conversation_id is None:
                raise ValueError("Conversation ID should not be None after flush")

            # Memory 연결 (Link 테이블 직접 사용)
            if memory_ids:
                for memory_id in memory_ids:
                    memory_link = ConversationMemoryLink(
                        conversation_id=conversation_id,
                        memory_id=memory_id,
                    )
                    session.add(memory_link)

            # Reminder 연결 (Link 테이블 직접 사용)
            if reminder_ids:
                for reminder_id in reminder_ids:
                    reminder_link = ConversationReminderLink(
                        conversation_id=conversation_id,
                        reminder_id=reminder_id,
                    )
                    session.add(reminder_link)

            await session.flush()
            await session.refresh(conversation)
            return conversation
