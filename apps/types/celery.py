from pydantic import BaseModel, Field


class CeleryConfig(BaseModel):
    """Celery 설정"""

    broker_db: int = Field(description="Redis DB for broker")
    result_db: int = Field(description="Redis DB for result backend")
    timezone: str = Field(description="Celery timezone")
    task_track_started: bool = Field(default=True)
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    accept_content: list[str] = Field(default=["json"])
    result_expires: int = Field(default=3600, description="Result expiry in seconds")
