"""테스트 사용자 및 인증 토큰 생성 스크립트 (debug 모드에서만 동작)"""

import asyncio
import sys

from sqlmodel import select

from apps.models.user import User
from apps.types.social import SocialProvider
from containers import Container
from settings import Settings

TEST_USER_EMAIL = "test@example.com"
TEST_USER_NICKNAME = "test_user"


async def create_test_user_and_token() -> None:
    """테스트 사용자를 생성하고 인증 토큰을 발급합니다."""
    if not Settings.debug:
        print("Error: This script only works in debug mode.")
        print("Set 'debug: true' in your config file.")
        sys.exit(1)

    container = Container()
    container.config.from_dict(Settings.model_dump())

    database = container.database()
    session_service = container.session_service()

    async with database.session() as session:
        # 기존 테스트 사용자 확인
        stmt = select(User).where(User.email == TEST_USER_EMAIL)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            # 테스트 사용자 생성
            user = User(
                email=TEST_USER_EMAIL,
                nickname=TEST_USER_NICKNAME,
                social_provider=SocialProvider.GOOGLE,
                social_id="test_social_id_12345",
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            print(f"[Created] Test user: {user.email} (ID: {user.id})")
        else:
            print(f"[Exists] Test user: {user.email} (ID: {user.id})")

        user_id = user.id
        if user_id is None:
            raise ValueError("User ID should not be None")

        # 세션 토큰 생성
        token = await session_service.create_session(user_id)
        print(f"\n{'=' * 60}")
        print(f"Test User ID: {user_id}")
        print(f"Test Token: {token}")
        print(f"{'=' * 60}")
        print("\nUsage:")
        print(f'  curl -H "Authorization: Bearer {token}" http://localhost:8000/api/...')
        print("\nOr set environment variable:")
        print(f"  export TEST_TOKEN={token}")


if __name__ == "__main__":
    asyncio.run(create_test_user_and_token())
