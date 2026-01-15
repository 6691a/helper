import os
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
    SettingsConfigDict,
)

from apps.types.auth import AuthConfig
from apps.types.database import DatabaseConfig
from apps.types.redis import RedisConfig
from apps.types.social import SocialConfig
from apps.types.voice import VoiceConfig

ROOT_DIR = Path(__file__).parent.resolve()
ENV_FILE = os.getenv("ENV_FILE", "local.yaml")


class _Settings(BaseSettings):
    root_dir: Path = ROOT_DIR
    secret_key: str
    database: DatabaseConfig
    redis: RedisConfig
    social: SocialConfig
    auth: AuthConfig
    voice: VoiceConfig

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        *args: PydanticBaseSettingsSource,
        **kwargs: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(
                settings_cls=settings_cls,
                yaml_file=ROOT_DIR / "env" / ENV_FILE,
                yaml_file_encoding="utf-8",
            ),
        )


Settings = _Settings()
