from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
)
from starlette.requests import HTTPConnection

from apps.models.user import User
from apps.services.session import SessionService
from database import Database


class AuthenticatedUser(BaseUser):
    def __init__(self, user: User):
        self.user = user

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.user.nickname

    @property
    def identity(self) -> str:
        return str(self.user.id)


class SessionAuthBackend(AuthenticationBackend):
    def __init__(self, session_service: SessionService, database: Database):
        self.session_service = session_service
        self.database = database

    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        auth_header = conn.headers.get("Authorization")
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        user_id = await self.session_service.get_user_id(token)
        if user_id is None:
            return None

        async with self.database.session() as session:
            user = await session.get(User, user_id)
            if user is None:
                return None

        return AuthCredentials(["authenticated"]), AuthenticatedUser(user)
