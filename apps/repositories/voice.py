from uuid import UUID

from sqlalchemy import desc
from sqlmodel import col, select

from apps.models.voice import VoiceSession
from database import Database


class VoiceSessionRepository:
    """VoiceSession 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def get_by_id(self, voice_session_id: int, user_id: int | None = None) -> VoiceSession | None:
        """ID로 VoiceSession을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(VoiceSession).where(VoiceSession.id == voice_session_id)
            if user_id is not None:
                stmt = stmt.where(VoiceSession.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: UUID) -> VoiceSession | None:
        """session_id(UUID)로 VoiceSession을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(VoiceSession).where(VoiceSession.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[VoiceSession]:
        """사용자의 VoiceSession 목록을 조회합니다."""
        async with self.database.session() as session:
            stmt = (
                select(VoiceSession)
                .where(VoiceSession.user_id == user_id)
                .order_by(desc(col(VoiceSession.created_at)))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, voice_session: VoiceSession) -> VoiceSession:
        """VoiceSession을 생성합니다."""
        async with self.database.session() as session:
            session.add(voice_session)
            await session.flush()
            await session.refresh(voice_session)
            return voice_session

    async def update(self, voice_session: VoiceSession) -> VoiceSession:
        """VoiceSession을 수정합니다 (사용자 확인 후 업데이트)."""
        async with self.database.session() as session:
            session.add(voice_session)
            await session.flush()
            await session.refresh(voice_session)
            return voice_session
