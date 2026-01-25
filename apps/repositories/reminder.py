from datetime import UTC, datetime

from sqlalchemy import and_
from sqlmodel import col, desc, select

from apps.models.reminder import Reminder
from apps.types.reminder import ReminderStatus
from database import Database


class ReminderRepository:
    """Reminder 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def get_by_id(self, reminder_id: int, user_id: int | None = None) -> Reminder | None:
        """ID로 Reminder를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Reminder).where(Reminder.id == reminder_id)
            if user_id is not None:
                stmt = stmt.where(Reminder.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: int | None = None,
        status: ReminderStatus | None = None,
        memory_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Reminder]:
        """Reminder 목록을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Reminder)
            if user_id is not None:
                stmt = stmt.where(Reminder.user_id == user_id)
            if status is not None:
                stmt = stmt.where(Reminder.status == status)
            if memory_id is not None:
                stmt = stmt.where(Reminder.memory_id == memory_id)
            stmt = stmt.order_by(desc(col(Reminder.created_at))).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_due_reminders(self, limit: int = 100) -> list[Reminder]:
        """실행 시간이 된 활성 리마인더를 조회합니다."""
        async with self.database.session() as session:
            now = datetime.now(UTC)
            stmt = (
                select(Reminder)
                .where(
                    and_(
                        col(Reminder.next_run_at) <= now,
                        col(Reminder.status) == ReminderStatus.ACTIVE,
                    )
                )
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, reminder: Reminder) -> Reminder:
        """Reminder를 생성합니다."""
        async with self.database.session() as session:
            session.add(reminder)
            await session.flush()
            await session.refresh(reminder)
            return reminder

    async def update(self, reminder: Reminder) -> Reminder:
        """Reminder를 수정합니다."""
        async with self.database.session() as session:
            session.add(reminder)
            await session.flush()
            await session.refresh(reminder)
            return reminder

    async def delete(self, reminder: Reminder) -> None:
        """Reminder를 삭제합니다."""
        async with self.database.session() as session:
            await session.delete(reminder)

    async def get_by_memory_id(self, memory_id: int, user_id: int | None = None) -> Reminder | None:
        """Memory ID로 Reminder를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Reminder).where(Reminder.memory_id == memory_id)
            if user_id is not None:
                stmt = stmt.where(Reminder.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
