from dependency_injector import containers, providers

from apps.services.social import SocialAuthService
from apps.types.social import Social
from database import Database


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["apps"])

    config = providers.Configuration()

    database = providers.Singleton(
        Database,
        db_url=config.database.async_psql_database_url,
        echo=True,
    )

    social_auth_service = providers.Singleton(
        SocialAuthService,
        socials=providers.Factory(
            lambda providers: [Social(**p) for p in providers],
            config.social.providers,
        ),
        redirect_uri_base=config.social.redirect_uri_base,
    )
