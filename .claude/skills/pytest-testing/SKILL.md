---
name: pytest-testing
description: Write and run pytest tests for FastAPI applications with SQLModel. Use when creating test files, writing test cases, running tests with coverage, or setting up test fixtures and factories.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__jetbrains__get_file_text_by_path, mcp__jetbrains__replace_text_in_file, mcp__jetbrains__execute_terminal_command
---

# Pytest Testing Skill for FastAPI + SQLModel

## Overview

이 스킬은 FastAPI와 SQLModel을 사용하는 Home Inventory API 프로젝트에서 pytest 테스트를 작성하고 실행하는 것을 도와줍니다.

## 설치된 테스트 패키지

- **pytest** - 테스트 프레임워크
- **pytest-asyncio>=1.3.0** - async 함수 테스트
- **pytest-cov>=7.0.0** - 코드 커버리지
- **pytest-mock>=3.15.1** - mocking 기능
- **factory-boy>=3.3.3** - 모델 팩토리 패턴
- **httpx** - FastAPI TestClient (이미 설치됨)

## 테스트 실행 명령어

```bash
# 모든 테스트 실행
uv run pytest

# 상세 출력
uv run pytest -v

# 커버리지와 함께 실행
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# 특정 테스트 파일 실행
uv run pytest tests/test_items.py -v

# 특정 테스트 함수 실행
uv run pytest tests/test_items.py::test_create_item -v

# 패턴 매칭 테스트 실행
uv run pytest -k "create" -v

# 비동기 테스트만 실행
uv run pytest -m asyncio

# 실패한 테스트만 재실행
uv run pytest --lf
```

## 테스트 구조

```
tests/
├── conftest.py           # 공통 fixtures
├── factories.py          # factory-boy 팩토리들
├── test_items.py         # Item 엔드포인트 테스트
├── test_locations.py     # Location 엔드포인트 테스트
├── test_categories.py    # Category 엔드포인트 테스트
└── test_services/        # 서비스 레이어 테스트
    └── test_item_service.py
```

## 핵심 패턴

### 1. conftest.py - 공통 Fixtures

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from main import app
from app.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """테스트용 인메모리 SQLite 세션"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """dependency override된 TestClient"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### 2. factories.py - Factory Boy 팩토리

```python
import factory
from factory import alchemy
from app.models import Location, Category, Item


class LocationFactory(factory.Factory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"장소{n}")
    description = factory.Faker("sentence", locale="ko_KR")


class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"카테고리{n}")
    default_expiry_days = factory.Faker("random_int", min=7, max=365)


class ItemFactory(factory.Factory):
    class Meta:
        model = Item

    name = factory.Sequence(lambda n: f"아이템{n}")
    quantity = factory.Faker("random_int", min=1, max=100)
    location_id = factory.LazyAttribute(lambda _: 1)
    category_id = factory.LazyAttribute(lambda _: 1)
```

### 3. API 엔드포인트 테스트 예시

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_create_item(client: TestClient, session: Session):
    """아이템 생성 테스트"""
    # Given: 위치와 카테고리 생성
    location = Location(name="냉장고")
    category = Category(name="채소")
    session.add(location)
    session.add(category)
    session.commit()

    # When: 아이템 생성 요청
    response = client.post(
        "/api/items/",
        json={
            "name": "양파",
            "quantity": 5,
            "location_id": location.id,
            "category_id": category.id,
        }
    )

    # Then: 성공 응답 확인
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "양파"
    assert data["quantity"] == 5


def test_get_items(client: TestClient, session: Session):
    """아이템 목록 조회 테스트"""
    # Given: 여러 아이템 생성
    location = Location(name="냉장고")
    session.add(location)
    session.commit()

    for i in range(3):
        item = Item(name=f"아이템{i}", quantity=10, location_id=location.id)
        session.add(item)
    session.commit()

    # When: 아이템 목록 조회
    response = client.get("/api/items/")

    # Then: 3개 아이템 반환
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_async_endpoint(client: TestClient):
    """비동기 엔드포인트 테스트"""
    response = client.get("/api/items/")
    assert response.status_code == 200
```

### 4. 서비스 레이어 유닛 테스트

```python
from unittest.mock import Mock, patch
from app.services.item_service import ItemService


def test_item_service_create():
    """서비스 레이어 아이템 생성 테스트"""
    # Given: Mock repository
    mock_repo = Mock()
    service = ItemService(mock_repo)

    # When: 아이템 생성
    service.create_item(name="테스트", quantity=10)

    # Then: repository 메서드 호출 확인
    mock_repo.create.assert_called_once()
```

### 5. Factory 사용 예시

```python
from tests.factories import ItemFactory, LocationFactory


def test_with_factories(session: Session, client: TestClient):
    """Factory를 사용한 테스트 데이터 생성"""
    # Given: Factory로 데이터 생성
    location = LocationFactory(name="냉장고")
    session.add(location)
    session.commit()

    items = [
        ItemFactory(location_id=location.id, quantity=i)
        for i in range(1, 4)
    ]
    for item in items:
        session.add(item)
    session.commit()

    # When & Then
    response = client.get("/api/items/")
    assert len(response.json()) == 3
```

## 테스트 작성 Best Practices

1. **Given-When-Then 패턴 사용**
   - Given: 테스트 데이터 준비
   - When: 테스트할 동작 수행
   - Then: 결과 검증

2. **명확한 테스트 함수명**
   - `test_<function>_<scenario>_<expected_result>`
   - 예: `test_create_item_with_valid_data_returns_201`

3. **하나의 테스트는 하나만 검증**
   - 단일 책임 원칙
   - 실패 시 원인 파악 용이

4. **Fixture 활용**
   - 공통 setup/teardown은 fixture로
   - `conftest.py`에 재사용 가능한 fixture 정의

5. **Factory 활용**
   - 복잡한 모델 객체는 Factory로 생성
   - 테스트 데이터 생성 간소화

6. **DB 격리**
   - 각 테스트는 독립적인 DB 세션 사용
   - 인메모리 SQLite 또는 트랜잭션 롤백

7. **외부 의존성 Mocking**
   - FCM, Gemini API 등은 Mock 처리
   - 테스트 속도 향상 및 격리

## pytest.ini 설정 예시

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "asyncio: marks tests as async",
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
asyncio_mode = "auto"
```

## 커버리지 목표

- **최소 목표**: 80% 이상
- **우선순위**: routers > services > repositories
- **제외 가능**: 설정 파일, migration 스크립트

## Troubleshooting

### ImportError
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run pytest
```

### Async 테스트 실패
- `@pytest.mark.asyncio` 마커 확인
- `pytest-asyncio` 설치 확인
- `asyncio_mode = "auto"` 설정 확인

### DB 관련 에러
- 테스트용 인메모리 DB 사용 확인
- Session fixture override 확인
- 각 테스트 후 rollback/cleanup 확인

### Factory 에러
- Model 클래스 import 확인
- Foreign key 관계 순서 확인 (먼저 부모 생성)

## 참고 자료

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest 공식 문서](https://docs.pytest.org/)
- [factory-boy 공식 문서](https://factoryboy.readthedocs.io/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
