from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"onupdate": func.now()},
    )
