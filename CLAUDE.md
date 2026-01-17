# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Inventory API - A FastAPI application for managing household items, tracking locations, quantities, expiration dates, and replacement cycles. Includes planned features for notifications (FCM), AI voice assistant (Gemini), and session-based authentication.

## Development Commands

```bash
# Install dependencies (using uv)
uv sync

# Run development server
uv run fastapi dev main.py

# Run production server
uv run fastapi run main.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Tech Stack

- **Python 3.13+** with FastAPI
- **SQLModel** (SQLAlchemy + Pydantic combined)
- **PostgreSQL** (production) with asyncpg driver
- **Alembic** for migrations
- **uv** for package management

## Architecture (Planned)

The project follows a layered architecture:

```
app/
├── routers/        # API endpoints (controllers)
├── services/       # Business logic
├── repositories/   # Database access layer
├── models/         # SQLModel database models
├── schemas/        # Pydantic request/response schemas
├── config.py       # Settings (Pydantic Settings)
├── database.py     # DB connection
├── dependencies.py # FastAPI dependencies
└── exceptions.py   # Custom exceptions
```

## Core Domain Models

- **Location**: Storage places (냉장고, 신발장, etc.)
- **Category**: Item types with optional default expiry days
- **Item**: Items with quantity, expiry date, replacement cycle tracking
- **Reminder**: Notification settings (EXPIRY, LOW_STOCK, REPLACEMENT types)

## API Design

- Base path: `/api/`
- Standard REST endpoints for CRUD operations
- Special item endpoints: `/items/search`, `/items/low-stock`, `/items/expiring`, `/items/needs-replacement`
- Quantity management: PATCH `/items/{id}/quantity/add` and `/quantity/subtract`

## Development Phases

1. **Phase 1 (MVP)**: Location, Category, Item CRUD with search/filter
2. **Phase 2**: Reminder system with FCM push notifications (APScheduler)
3. **Phase 3**: AI assistant with Gemini function calling
4. **Phase 4**: Session-based auth with Redis
5. **Phase 5**: Statistics, social login, barcode scanning

## Internationalization (i18n)

이 프로젝트는 GNU gettext 기반 다국어 지원을 사용합니다.

### 지원 언어

- `en` (English) - 기본값
- `ko` (한국어)

### 사용법

```python
from apps.i18n import _

# 코드에서 번역 가능한 문자열 사용
raise AppException(_("Resource not found."))
```

### 번역 파일 구조

```
apps/i18n/
├── __init__.py          # get_locale(), set_locale(), _() 함수
├── middleware.py        # Accept-Language 헤더 처리
└── locales/
    ├── en/LC_MESSAGES/
    │   └── messages.po  # 영어 번역
    └── ko/LC_MESSAGES/
        └── messages.po  # 한국어 번역
```

### 번역 파일 생성/업데이트

```bash
# 소스에서 번역 대상 문자열 추출
uv run pybabel extract -F babel.cfg -o messages.pot .

# 새 언어 추가
uv run pybabel init -i messages.pot -d apps/i18n/locales -l ko

# 기존 번역 업데이트
uv run pybabel update -i messages.pot -d apps/i18n/locales

# .po → .mo 컴파일
uv run pybabel compile -d apps/i18n/locales
```

### 클라이언트 요청

클라이언트는 `Accept-Language` 헤더로 언어를 지정:

```
Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8
```

## API Response Format

### 성공 응답

```json
{
  "code": 200,
  "message": "SUCCESS",
  "result": { ... }
}
```

### 에러 응답

```json
{
  "code": 400,
  "message": "에러 메시지 (다국어 지원)",
  "result": null
}
```

### ResponseProvider 사용

```python
from apps.schemas.common import ResponseProvider

# 200 OK
return ResponseProvider.success(result)

# 201 Created
return ResponseProvider.created(result)

# 에러
return ResponseProvider.failed(status_code, message)
```

### 예외 처리

```python
from apps.exceptions import AppException, NotFoundError, VoiceProcessingError

# 일반 예외
raise AppException(_("Something went wrong."))

# 404 Not Found
raise NotFoundError(_("Item not found."))

# 음성 처리 에러
raise VoiceProcessingError(_("Voice processing failed."))
```

## Type Design Guidelines

### 적절한 타입 사용

코드의 타입 안정성과 가독성을 위해 문자열 대신 적절한 타입을 사용합니다.

| 용도 | ❌ str | ✅ 적절한 타입 |
|------|--------|---------------|
| 상태값 | `status: str = "active"` | `status: ReminderStatus` |
| 선택지 | `type: str = "weekly"` | `type: ReminderFrequency` |
| 날짜 | `date: str = "2025-01-20"` | `date: datetime.date` |
| 시간 | `time: str = "09:00"` | `time: datetime.time` |
| 일시 | `datetime: str` | `datetime: datetime.datetime` |

### Enum 작성 규칙

1. **위치**: `apps/types/` 폴더에 도메인별로 분리
2. **상속**: `(str, Enum)`으로 상속하여 JSON 직렬화 호환
3. **명명**: 클래스는 PascalCase, 값은 snake_case

```python
from enum import Enum

class ReminderStatus(str, Enum):
    """알림 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
```

### 날짜/시간 타입

```python
from datetime import date, time, datetime

# 날짜만 (YYYY-MM-DD)
specific_date: date | None = Field(default=None)

# 시간만 (HH:MM:SS)
reminder_time: time = Field(default=time(9, 0))

# 일시 (YYYY-MM-DD HH:MM:SS)
next_run_at: datetime | None = Field(default=None)
```

SQLModel에서 자동으로 DB 타입 매핑됨.