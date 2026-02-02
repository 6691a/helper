# Home Inventory API

가정용 물품 관리 API - FastAPI + PostgreSQL + Redis

## 요구사항

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- Docker & Docker Compose
- pre-commit (글로벌 설치)

## 프로젝트 세팅

```bash
# 의존성 설치
uv sync

# pre-commit 훅 설치
pre-commit install

# 로컬 인프라 실행 (PostgreSQL + Redis)
just up
```

## 개발 서버 실행

```bash
# FastAPI 개발 서버
just dev

# 또는 인프라 + 서버 한번에
just start
```

## 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `just up` | 인프라 실행 (DB, Redis) |
| `just down` | 인프라 중지 |
| `just down-v` | 인프라 중지 + 볼륨 삭제 |
| `just logs` | 인프라 로그 확인 |
| `just dev` | FastAPI 개발 서버 |
| `just run` | FastAPI 프로덕션 서버 |

## 로컬 접속 정보

| 서비스 | 호스트 | 포트 | 인증 |
|--------|--------|------|------|
| PostgreSQL | localhost | 45432 | helper/helper/helper |
| Redis | localhost | 46379 | - |

## Pre-commit

```bash
# 수동 실행
pre-commit run --all-files

# 특정 훅만 실행
pre-commit run ruff --all-files
pre-commit run ty --all-files
```