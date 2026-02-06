from sqlmodel import select

from apps.models.user import User
from apps.types.social import SocialProvider
from database import Database


class UserRepository:
    def __init__(self, database: Database):
        self.database = database

    async def get_by_id(self, user_id: int) -> User | None:
        """ID로 사용자를 조회합니다."""
        async with self.database.session() as session:
            return await session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """이메일로 사용자를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_social(self, provider: SocialProvider, social_id: str) -> User | None:
        """소셜 로그인 정보로 사용자를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(User).where(
                User.social_provider == provider,
                User.social_id == social_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_nickname(self, nickname: str) -> User | None:
        """닉네임으로 사용자를 조회합니다."""
        async with self.database.session() as session:
            stmt = select(User).where(User.nickname == nickname)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """사용자를 생성합니다."""
        async with self.database.session() as session:
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    async def update(self, user: User) -> User:
        """사용자 정보를 수정합니다."""
        async with self.database.session() as session:
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
