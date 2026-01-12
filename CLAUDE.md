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