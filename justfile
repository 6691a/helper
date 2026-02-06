# Helper Monorepo Commands

# =====================
# Frontend (Expo)
# =====================

# Start Expo dev server
frontend-start:
    cd frontend && npm start

# Run on iOS
frontend-ios:
    cd frontend && npm run ios

# Run on Android
frontend-android:
    cd frontend && npm run android

# Lint frontend
frontend-lint:
    cd frontend && npm run lint

# Install frontend dependencies
frontend-install:
    cd frontend && npm install

# =====================
# Backend (FastAPI)
# =====================

# Start backend dev server
backend-dev:
    cd backend && just dev

# Start infrastructure (PostgreSQL, Redis)
backend-up:
    cd backend && just up

# Stop infrastructure
backend-down:
    cd backend && just down

# Run migrations
backend-migrate:
    cd backend && just migrate

# =====================
# All
# =====================

# Install all dependencies
install:
    cd frontend && npm install
    cd backend && uv sync

# Lint all
lint:
    cd frontend && npm run lint
    cd backend && uv run ruff check .
