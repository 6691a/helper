from pydantic import BaseModel, computed_field


class DatabaseConfig(BaseModel):
    user: str
    name: str
    host: str
    port: int
    password: str

    echo: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_psql_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
