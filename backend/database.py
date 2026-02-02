from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps

from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.types.database import DatabaseConfig

# 현재 트랜잭션 세션을 저장하는 컨텍스트 변수
_current_session: ContextVar[AsyncSession | None] = ContextVar("current_session", default=None)


def transactional[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """
    Spring의 @Transactional과 유사한 트랜잭션 데코레이터.

    Database는 DI 컨테이너에서 자동 주입됩니다.

    사용 예:
        class ConversationService:
            @transactional
            async def process_voice(self, request, user_id):
                await self.memory_repo.create(...)
                await self.reminder_repo.create(...)
                # 모든 작업이 하나의 트랜잭션으로 처리됨
    """

    @wraps(func)
    @inject
    async def wrapper(  # type: ignore[valid-type]
        *args: P.args,
        database: "Database" = Provide["database"],
        **kwargs: P.kwargs,
    ) -> R:
        async with database.transaction():
            return await func(*args, **kwargs)  # type: ignore[misc, no-any-return]

    return wrapper  # type: ignore[return-value]


class Database:
    def __init__(self, database_config: DatabaseConfig) -> None:
        self.database_config = database_config
        self._engine = create_async_engine(database_config.async_psql_database_url, echo=database_config.echo)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        세션을 가져옵니다.

        - 트랜잭션 컨텍스트 내부: 기존 세션 재사용 (커밋 안 함)
        - 트랜잭션 컨텍스트 외부: 새 세션 생성 후 자동 커밋
        """
        existing_session = _current_session.get()

        if existing_session is not None:
            # 트랜잭션 내부 - 기존 세션 사용, 커밋하지 않음
            yield existing_session
        else:
            # 트랜잭션 외부 - 새 세션 생성, 자동 커밋
            session: AsyncSession = self._session_factory()
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """
        Django의 @transaction.atomic과 유사한 트랜잭션 컨텍스트.

        사용 예:
            async with database.transaction():
                await repo1.create(item1)  # 세션 자동 공유
                await repo2.create(item2)  # 같은 트랜잭션
                # 모든 작업 성공 시에만 커밋

        중첩 가능:
            async with database.transaction():
                await repo1.create(item1)
                async with database.transaction():  # 같은 세션 재사용
                    await repo2.create(item2)
        """
        existing_session = _current_session.get()

        if existing_session is not None:
            # 이미 트랜잭션 내부 - 같은 세션 사용 (중첩 트랜잭션)
            yield existing_session
        else:
            # 새 트랜잭션 시작
            session: AsyncSession = self._session_factory()
            token = _current_session.set(session)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                _current_session.reset(token)
                await session.close()
