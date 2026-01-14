from pydantic import BaseModel, computed_field


class Database(BaseModel):
    user: str
    name: str
    host: str
    port: int
    password: str

    @computed_field
    def async_psql_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
