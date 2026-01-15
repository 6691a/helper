from dependency_injector import containers, providers

from apps.auth import SessionAuthBackend
from apps.repositories.user import UserRepository
from apps.services.auth import AuthService
from apps.services.session import SessionService
from apps.services.social import SocialAuthService
from apps.services.voice import VoiceService
from apps.types.database import DatabaseConfig
from apps.types.redis import RedisConfig
from apps.types.social import Social
from apps.types.voice import VoiceConfig
from database import Database


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["apps"])

    config = providers.Configuration()

    database = providers.Singleton(
        Database,
        database_config=providers.Factory(
            lambda c: DatabaseConfig(**c),
            config.database,
        ),
    )
    session_service = providers.Singleton(
        SessionService,
        redis_config=providers.Factory(
            lambda c: RedisConfig(**c),
            config.redis,
        ),
        token_max_age=config.auth.token_max_age_seconds,
        auth_code_max_age=config.auth.auth_code_max_age_seconds,
    )

    user_repository = providers.Factory(
        UserRepository,
        database=database,
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        session_service=session_service,
    )

    social_auth_service = providers.Singleton(
        SocialAuthService,
        socials=providers.Factory(
            lambda providers: [Social(**p) for p in providers],
            config.social.providers,
        ),
        redirect_uri_base=config.social.redirect_uri_base,
        allowed_redirect_hosts=config.social.allowed_redirect_hosts,
    )

    auth_backend = providers.Singleton(
        SessionAuthBackend,
        session_service=session_service,
        database=database,
    )

    voice_service = providers.Singleton(
        VoiceService,
        config=providers.Factory(
            lambda c: VoiceConfig(**c),
            config.voice,
        ),
    )
