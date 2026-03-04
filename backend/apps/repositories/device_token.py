from sqlmodel import col, select

from apps.models.device_token import DeviceToken
from database import Database


class DeviceTokenRepository:
    """DeviceToken 저장소"""

    def __init__(self, database: Database):
        self.database = database

    async def get_all_active(self) -> list[DeviceToken]:
        """활성화된 모든 FCM 토큰을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(DeviceToken).where(col(DeviceToken.is_active) == True)  # noqa: E712
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> list[DeviceToken]:
        """사용자의 활성화된 FCM 토큰을 조회합니다."""
        async with self.database.session() as session:
            stmt = select(DeviceToken).where(
                col(DeviceToken.user_id) == user_id,
                col(DeviceToken.is_active) == True,  # noqa: E712
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def upsert(self, user_id: int, token: str, platform: str) -> DeviceToken:
        """FCM 토큰을 등록하거나 업데이트합니다."""
        async with self.database.session() as session:
            stmt = select(DeviceToken).where(col(DeviceToken.token) == token)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is not None:
                existing.user_id = user_id
                existing.platform = platform
                session.add(existing)
                await session.flush()
                await session.refresh(existing)
                return existing

            device_token = DeviceToken(user_id=user_id, token=token, platform=platform)
            session.add(device_token)
            await session.flush()
            await session.refresh(device_token)
            return device_token

    async def update_is_active(self, token: str, is_active: bool) -> DeviceToken | None:
        """FCM 토큰의 알림 활성화 여부를 변경합니다."""
        async with self.database.session() as session:
            stmt = select(DeviceToken).where(col(DeviceToken.token) == token)
            result = await session.execute(stmt)
            device_token = result.scalar_one_or_none()
            if device_token is None:
                return None
            device_token.is_active = is_active
            session.add(device_token)
            await session.flush()
            await session.refresh(device_token)
            return device_token

    async def delete_by_token(self, token: str) -> None:
        """FCM 토큰을 삭제합니다."""
        async with self.database.session() as session:
            stmt = select(DeviceToken).where(col(DeviceToken.token) == token)
            result = await session.execute(stmt)
            device_token = result.scalar_one_or_none()
            if device_token is not None:
                await session.delete(device_token)
