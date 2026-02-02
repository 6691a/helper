"""AI 처리 로그 저장소"""

from typing import Any

from sqlalchemy import desc
from sqlmodel import col, select

from apps.models.ai_log import AIProcessingLog
from database import Database


class AIProcessingLogRepository:
    """AI 처리 로그 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def create(self, log: AIProcessingLog) -> AIProcessingLog:
        """로그를 생성합니다."""
        async with self.database.session() as session:
            session.add(log)
            await session.flush()
            await session.refresh(log)
            return log

    async def create_log(
        self,
        step: str,
        input_text: str,
        output_data: dict[str, Any],
        user_id: int | None = None,
        conversation_id: int | None = None,
        model_name: str | None = None,
        processing_time_ms: int | None = None,
    ) -> AIProcessingLog:
        """로그를 간편하게 생성합니다."""
        log = AIProcessingLog(
            step=step,
            input_text=input_text,
            output_data=output_data,
            user_id=user_id,
            conversation_id=conversation_id,
            model_name=model_name,
            processing_time_ms=processing_time_ms,
        )
        return await self.create(log)

    async def get_by_conversation_id(self, conversation_id: int) -> list[AIProcessingLog]:
        """Conversation ID로 로그를 조회합니다."""
        async with self.database.session() as session:
            stmt = (
                select(AIProcessingLog)
                .where(AIProcessingLog.conversation_id == conversation_id)
                .order_by(col(AIProcessingLog.created_at))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: int,
        step: str | None = None,
        limit: int = 100,
    ) -> list[AIProcessingLog]:
        """사용자의 AI 처리 로그를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(AIProcessingLog).where(AIProcessingLog.user_id == user_id)
            if step:
                stmt = stmt.where(AIProcessingLog.step == step)
            stmt = stmt.order_by(desc(col(AIProcessingLog.created_at))).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
