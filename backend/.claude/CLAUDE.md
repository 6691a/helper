# CLAUDE.md

FastAPI + SQLModel 기반 홈 인벤토리 관리 및 AI 음성 비서 애플리케이션

## Development Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run fastapi dev main.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# Code quality
uv run ruff check --fix .
uv run mypy .
```

## Tech Stack

- **Python 3.13+**, FastAPI, SQLModel (SQLAlchemy + Pydantic)
- **PostgreSQL** with asyncpg, **Alembic** for migrations
- **Redis** for session/cache, **Celery** for background tasks
- **Google Gemini** for AI, **Google Cloud Speech-to-Text** for STT
- **uv** for package management, **Ruff** for linting/formatting

## Architecture

```
apps/
├── controllers/    # API endpoints (FastAPI routers)
├── services/       # Business logic
├── repositories/   # Database access layer
├── models/         # SQLModel ORM models
├── schemas/        # Pydantic request/response schemas
├── types/          # Enums, dataclasses, type definitions
├── i18n/           # Internationalization (gettext)
└── utils/          # Utility functions
```

**계층 구조:** Controller → Service → Repository → Model

## Type Design

### Enum 사용 (문자열 대신)

```python
# apps/types/*.py에 정의
class ReminderStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"

# ✅ 사용
status: ReminderStatus = ReminderStatus.ACTIVE

# ❌ 피하기
status: str = "active"
```

### 날짜/시간 타입

```python
from datetime import date, time, datetime

specific_date: date | None        # YYYY-MM-DD
reminder_time: time               # HH:MM:SS
next_run_at: datetime | None      # YYYY-MM-DD HH:MM:SS (timezone-aware)
```

## Database Guidelines

### 테이블 명명: 단수형

```python
class User(BaseModel, table=True):
    __tablename__ = "user"  # NOT "users"

user_id: int = Field(foreign_key="user.id")  # NOT "users.id"
```

### 모델 등록 필수

새 모델은 `apps/models/__init__.py`에 import 필수. 안 하면 Alembic 인식 실패.

### Many-to-Many 관계

```python
# Link Model - SQLModel 직접 상속 (BaseModel 아님)
class ConversationMemoryLink(SQLModel, table=True):
    __tablename__ = "conversation_memory_link"
    conversation_id: int = Field(foreign_key="conversation.id", primary_key=True)
    memory_id: int = Field(foreign_key="memory.id", primary_key=True)

# 양쪽 모델
class Conversation(BaseModel, table=True):
    memories: list[Memory] = Relationship(
        back_populates="conversations",
        link_model=ConversationMemoryLink
    )
```

Link 모델도 `apps/models/__init__.py`에 import 필수.

## Code Quality

### 함수 분리 원칙

- 50줄 이상이면 분리 고려
- 한 함수는 하나의 책임만
- Private 메서드: `_`로 시작 (예: `_get_`, `_create_`, `_validate_`)

```python
# ✅ 메인 흐름만 명확하게
async def process_voice(self, request, user_id):
    voice_session = await self._get_voice_session(request.session_id, user_id)
    final_text = self._determine_final_text(request.text, voice_session)
    extracted = self._extract_result_data(assistant_response)
    conversation = await self._create_conversation_record(...)
    return ConversationResponse(...)
```

## Mypy Strict

프로젝트는 `mypy --strict` 사용.

### Optional 값 Narrowing

```python
# ✅ 올바른 방법
saved_memory = await self.repository.create(memory)
memory_id = saved_memory.id
if memory_id is None:
    raise ValueError("Memory ID should not be None after creation")
await self._save_reminder(reminder_info, memory_id, user_id)

# ❌ 피하기
assert saved_memory.id is not None  # 프로덕션에서 무시될 수 있음
```

### 타입 파라미터 명시

```python
# ✅
parsed_data: dict[str, Any] = {}
tasks: list[asyncio.Task[Any]] = []

# ❌
parsed_data: dict = {}  # Missing type parameters
```

### 복잡한 반환값은 Dataclass

3개 이상 반환값은 `apps/types/`에 dataclass 정의.

```python
@dataclass
class ExtractedConversationData:
    intent: Intent
    assistant_text: str
    parsed_data: dict[str, Any]
    memory_ids: list[int]
    reminder_ids: list[int]

def _extract_result_data(...) -> ExtractedConversationData:
    return ExtractedConversationData(...)
```
