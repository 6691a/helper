from dependency_injector import containers, providers

from apps.auth import SessionAuthBackend
from apps.cache import RedisCache
from apps.repositories.ai_log import AIProcessingLogRepository
from apps.repositories.conversation import ConversationRepository
from apps.repositories.memory import MemoryRepository
from apps.repositories.reminder import ReminderRepository
from apps.repositories.user import UserRepository
from apps.repositories.voice import VoiceSessionRepository
from apps.services.assistant import AssistantService
from apps.services.auth import AuthService
from apps.services.conversation import ConversationService
from apps.services.reminder import ReminderService
from apps.services.session import SessionService
from apps.services.social import SocialAuthService
from apps.services.streaming_voice import StreamingVoiceService
from apps.services.voice import VoiceService
from apps.services.voice_session import VoiceSessionService
from apps.types.assistant import AssistantConfig
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

    redis_cache = providers.Singleton(
        RedisCache,
        config=providers.Factory(
            lambda c: RedisConfig(**c),
            config.redis,
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
        allowed_redirect_schemes=config.social.allowed_redirect_schemes,
        allowed_redirect_hosts=config.social.allowed_redirect_hosts,
        session_service=session_service,
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

    memory_repository = providers.Factory(
        MemoryRepository,
        database=database,
    )

    reminder_repository = providers.Factory(
        ReminderRepository,
        database=database,
    )

    streaming_voice_service = providers.Singleton(
        StreamingVoiceService,
        config=providers.Factory(
            lambda c: VoiceConfig(**c),
            config.voice,
        ),
    )

    assistant_service = providers.Singleton(
        AssistantService,
        config=providers.Factory(
            lambda c: AssistantConfig(**c),
            config.assistant,
        ),
        memory_repository=memory_repository,
        reminder_repository=reminder_repository,
    )

    reminder_service = providers.Factory(
        ReminderService,
        reminder_repository=reminder_repository,
        memory_repository=memory_repository,
    )

    voice_session_repository = providers.Factory(
        VoiceSessionRepository,
        database=database,
    )

    conversation_repository = providers.Factory(
        ConversationRepository,
        database=database,
    )

    ai_log_repository = providers.Factory(
        AIProcessingLogRepository,
        database=database,
    )

    voice_session_service = providers.Factory(
        VoiceSessionService,
        voice_session_repository=voice_session_repository,
    )

    conversation_service = providers.Factory(
        ConversationService,
        voice_session_service=voice_session_service,
        conversation_repository=conversation_repository,
        assistant_service=assistant_service,
    )
