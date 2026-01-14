# 로컬 인프라 실행 (PostgreSQL + Redis)
up:
    docker compose -f compose/compose-local.yaml up -d

# 로컬 인프라 중지
down:
    docker compose -f compose/compose-local.yaml down

# 로컬 인프라 중지 및 볼륨 삭제
down-v:
    docker compose -f compose/compose-local.yaml down -v

# 로컬 인프라 로그 확인
logs:
    docker compose -f compose/compose-local.yaml logs -f

# FastAPI 개발 서버 실행
dev:
    uv run fastapi dev main.py

# FastAPI 프로덕션 서버 실행
run:
    uv run fastapi run main.py

# 인프라 실행 후 FastAPI 개발 서버 실행
start: up dev

# 마이그레이션 파일 생성
makemigrations message:
    ENV_FILE=local.yaml uv run alembic revision --autogenerate -m "{{message}}"

# 마이그레이션 적용
migrate:
    ENV_FILE=local.yaml uv run alembic upgrade head

# 마이그레이션 롤백 (1단계)
rollback:
    ENV_FILE=local.yaml uv run alembic downgrade -1

# 번역 메시지 추출
i18n-extract:
    uv run pybabel extract -F babel.cfg -o apps/i18n/messages.pot apps/

# 새 언어 추가 (예: just i18n-init en)
i18n-init locale:
    uv run pybabel init -i apps/i18n/messages.pot -d apps/i18n/locales -l {{locale}}

# 번역 파일 업데이트
i18n-update:
    uv run pybabel update -i apps/i18n/messages.pot -d apps/i18n/locales

# 번역 파일 컴파일
i18n-compile:
    uv run pybabel compile -d apps/i18n/locales