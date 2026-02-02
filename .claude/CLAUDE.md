# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Helper - 가정용 물품 관리 및 AI 음성 비서 애플리케이션 (모노레포)

## Repository Structure

```
helper/
├── backend/     # FastAPI + SQLModel API 서버
└── frontend/    # Expo React Native 앱 (file-based routing)
```

## Development Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Dependencies & Infrastructure
uv sync                          # Install dependencies
just up                          # Start PostgreSQL + Redis (Docker)
just down                        # Stop infrastructure
just down-v                      # Stop + delete volumes

# Development
just dev                         # Run FastAPI dev server
just start                       # Infrastructure + dev server

# Database
just migrate                     # Apply migrations
just makemigrations "message"    # Create migration

# Background Tasks
just celery-dev                  # Celery worker + beat (dev)

# Code Quality
pre-commit run --all-files
uv run ruff check --fix .
uv run mypy .
```

### Frontend (Expo/React Native)

```bash
cd frontend

npm install                      # Install dependencies
npx expo start                   # Start Expo dev server
npm run ios                      # iOS simulator
npm run android                  # Android emulator
npm run lint                     # ESLint
```

## Architecture

### Backend

- **Stack:** Python 3.13+, FastAPI, SQLModel, PostgreSQL, Redis, Celery
- **AI:** Google Gemini (LLM), Google Cloud Speech-to-Text
- **Package Manager:** uv, just (task runner)

계층 구조: Controller → Service → Repository → Model

상세 가이드라인은 `backend/.claude/CLAUDE.md` 참조.

### Frontend

- **Stack:** Expo SDK 54, React Native 0.81, React 19, TypeScript
- **Routing:** expo-router (file-based routing)
- **Navigation:** @react-navigation/bottom-tabs

```
frontend/
├── app/                 # File-based routes (expo-router)
│   ├── (tabs)/          # Tab navigator screens
│   └── _layout.tsx      # Root layout
├── components/          # Reusable components
│   └── ui/              # UI primitives
├── constants/           # Theme, colors, fonts
└── hooks/               # Custom hooks
```

## Local Services

| Service    | Host      | Port  | Credentials      |
|------------|-----------|-------|------------------|
| PostgreSQL | localhost | 45432 | helper/helper/helper |
| Redis      | localhost | 46379 | -                |

## Key Conventions

- **Backend:** Enum 사용, 단수형 테이블명, mypy strict 모드
- **Frontend:** Path aliases (`@/components`, `@/hooks` 등)

## Git & Commit Convention

### 초기 설정

```bash
# 루트에서 의존성 설치 (husky, lint-staged)
npm install

# pre-commit 설치 (Python 훅용)
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Conventional Commits

커밋 메시지는 다음 형식을 따릅니다:

```
type(scope): message
```

**Type (대문자):**
- `Feat` - 새로운 기능
- `Fix` - 버그 수정
- `Docs` - 문서 변경
- `Style` - 코드 포맷팅 (기능 변경 없음)
- `Refactor` - 리팩토링
- `Perf` - 성능 개선
- `Test` - 테스트 추가/수정
- `Build` - 빌드 시스템/의존성 변경
- `CI` - CI 설정 변경
- `Chore` - 기타 변경

**Scope (선택):** `frontend`, `backend`

**예시:**
```bash
git commit -m "Feat(frontend): add user profile screen"
git commit -m "Fix(backend): resolve database connection issue"
git commit -m "Docs: update README"
```

### Pre-commit Hooks

커밋 시 자동으로 실행되는 검사:
- **공통:** trailing whitespace, YAML/JSON 검증, 대용량 파일 검사
- **Backend:** ruff (lint + format), mypy
- **Frontend:** ESLint, Prettier

## Claude Code 지침

### 파일 수정 시 Edit 도구 사용

파일을 수정할 때는 IDE에서 변경 내역(diff)을 확인할 수 있도록 `Edit` 도구를 사용합니다. `mcp__jetbrains__replace_text_in_file` 도구는 사용하지 않습니다.