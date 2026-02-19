from datetime import date
from typing import Any

from sqlalchemy import desc, func
from sqlmodel import col, select

from apps.models.memory import Memory
from apps.types.assistant import MemoryType
from database import Database


class MemoryRepository:
    """Memory 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def get_by_id(self, memory_id: int, user_id: int | None = None) -> Memory | None:
        """ID로 Memory를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Memory).where(Memory.id == memory_id)
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: int | None = None,
        type_filter: MemoryType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        """Memory 목록을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(Memory)
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            if type_filter:
                stmt = stmt.where(Memory.type == type_filter)
            stmt = stmt.order_by(desc(col(Memory.created_at))).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, memory: Memory) -> Memory:
        """Memory를 생성합니다."""
        async with self.database.session() as session:
            session.add(memory)
            await session.flush()
            await session.refresh(memory)
            return memory

    async def update(self, memory: Memory) -> Memory:
        """Memory를 수정합니다."""
        async with self.database.session() as session:
            session.add(memory)
            await session.flush()
            await session.refresh(memory)
            return memory

    async def delete(self, memory: Memory) -> None:
        """Memory를 삭제합니다."""
        async with self.database.session() as session:
            await session.delete(memory)

    async def search_by_vector(
        self,
        embedding: list[float],
        user_id: int | None = None,
        type_filter: MemoryType | None = None,
        limit: int = 5,
        threshold: float = 0.5,
    ) -> list[tuple[Memory, float]]:
        """벡터 유사도 검색을 수행합니다 (cosine similarity)."""
        async with self.database.session() as session:
            # cosine_distance: 0 = 동일, 2 = 정반대
            # similarity = 1 - cosine_distance
            distance_threshold = 1 - threshold

            # Memory.embedding은 sa_column으로 정의되어 Vector 타입
            embedding_col: Any = Memory.embedding

            stmt = select(
                Memory,
                (1 - embedding_col.cosine_distance(embedding)).label("similarity"),
            ).where(embedding_col.is_not(None))

            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            if type_filter:
                stmt = stmt.where(Memory.type == type_filter)

            stmt = stmt.where(embedding_col.cosine_distance(embedding) <= distance_threshold)
            stmt = stmt.order_by(embedding_col.cosine_distance(embedding))
            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            rows = result.all()

            return [(row[0], float(row[1])) for row in rows]

    async def get_by_date(
        self,
        target_date: date,
        user_id: int | None = None,
        timezone: str = "UTC",
        limit: int = 100,
    ) -> list[Memory]:
        """특정 날짜(사용자 시간대 기준)의 Memory 목록을 조회합니다."""
        async with self.database.session() as session:
            local_date_expr = func.date(func.timezone(timezone, col(Memory.created_at)))
            stmt = select(Memory).where(local_date_expr == target_date)
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            stmt = stmt.order_by(desc(col(Memory.created_at))).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_calendar_marks(
        self,
        user_id: int | None = None,
        timezone: str = "UTC",
    ) -> dict[str, int]:
        """메모리가 있는 날짜와 개수를 반환합니다 (캘린더 마킹용)."""
        async with self.database.session() as session:
            local_date_expr = func.date(func.timezone(timezone, col(Memory.created_at)))
            stmt = select(local_date_expr, func.count(col(Memory.id)))
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            stmt = stmt.group_by(local_date_expr)
            result = await session.execute(stmt)
            rows = result.all()
            return {str(row[0]): int(row[1]) for row in rows}

    async def search_by_keywords(
        self,
        keywords: str,
        user_id: int | None = None,
        type_filter: MemoryType | None = None,
        limit: int = 10,
    ) -> list[Memory]:
        """키워드로 검색합니다 (ILIKE)."""
        async with self.database.session() as session:
            stmt = select(Memory).where(col(Memory.keywords).ilike(f"%{keywords}%"))
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
            if type_filter:
                stmt = stmt.where(Memory.type == type_filter)
            stmt = stmt.order_by(desc(col(Memory.created_at))).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())
