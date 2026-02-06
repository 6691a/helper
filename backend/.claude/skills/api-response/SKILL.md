---
name: api-response
description: FastAPI API 엔드포인트 및 응답 작성 가이드. 컨트롤러, 스키마, 서비스 패턴을 사용하여 API를 구현할 때 사용합니다.
allowed-tools: Read, Write, Edit, Glob, Grep, mcp__jetbrains__get_file_text_by_path, mcp__jetbrains__replace_text_in_file
---

# API Response Skill for FastAPI

## Overview

이 스킬은 Home Inventory API 프로젝트에서 API 엔드포인트를 작성하는 패턴과 응답 형식을 안내합니다.

## 프로젝트 구조

```
apps/
├── controllers/         # API 라우터 (엔드포인트)
│   ├── __init__.py     # routers 리스트
│   ├── auth.py
│   └── voice.py
├── services/           # 비즈니스 로직
├── repositories/       # DB 접근 계층
├── schemas/            # Pydantic 스키마
│   ├── common.py       # Response, ResponseProvider
│   └── auth.py
├── types/              # 설정 타입, enum
└── exceptions.py       # 커스텀 예외
```

## 표준 응답 형식

### Response 스키마 (`apps/schemas/common.py`)

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    code: int
    message: str
    result: T | None = None
```

### ResponseProvider 유틸리티

```python
from apps.schemas.common import ResponseProvider

# 200 OK
return ResponseProvider.success(result)

# 201 Created
return ResponseProvider.created(result)

# 커스텀 에러
return ResponseProvider.failed(status_code=400, message="Error message")
```

## 컨트롤러 작성 패턴

### 기본 구조

```python
from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.schemas.common import Response, ResponseProvider
from apps.schemas.your_schema import YourRequest, YourResponse
from apps.services.your_service import YourService
from containers import Container

router = APIRouter(
    prefix="/api/v1/your-resource",
    tags=["your-resource"],
)


@router.post("/", response_model=Response[YourResponse], status_code=201)
@inject
async def create_resource(
    body: YourRequest,
    service: Annotated[
        YourService,
        Depends(Provide[Container.your_service]),
    ],
) -> JSONResponse:
    """리소스를 생성합니다."""
    result = await service.create(body)
    return ResponseProvider.created(YourResponse.model_validate(result))


@router.get("/{id}", response_model=Response[YourResponse])
@inject
async def get_resource(
    id: int,
    service: Annotated[
        YourService,
        Depends(Provide[Container.your_service]),
    ],
) -> JSONResponse:
    """리소스를 조회합니다."""
    result = await service.get_by_id(id)
    return ResponseProvider.success(YourResponse.model_validate(result))
```

### 인증 필요 엔드포인트

```python
from starlette.authentication import requires

@router.post("/protected", response_model=Response[YourResponse])
@requires("authenticated")
@inject
async def protected_endpoint(
    request: Request,
    service: Annotated[YourService, Depends(Provide[Container.your_service])],
) -> JSONResponse:
    """인증 필요 엔드포인트."""
    user = request.user.user  # 현재 로그인 사용자
    result = await service.do_something(user)
    return ResponseProvider.success(result)
```

### 파일 업로드 엔드포인트

```python
from fastapi import UploadFile, File, Query

@router.post("/upload", response_model=Response[UploadResponse])
@inject
async def upload_file(
    file: Annotated[UploadFile, File(description="업로드할 파일")],
    option: Annotated[str | None, Query(description="옵션")] = None,
    service: Annotated[
        YourService,
        Depends(Provide[Container.your_service]),
    ] = None,  # type: ignore[assignment]
) -> JSONResponse:
    """파일을 업로드합니다."""
    content = await file.read()
    result = await service.process(content, file.filename)
    return ResponseProvider.success(result)
```

## 스키마 작성 패턴

### Request 스키마

```python
from pydantic import BaseModel, Field

class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="아이템 이름")
    quantity: int = Field(..., ge=0, description="수량")
    location_id: int | None = Field(None, description="위치 ID")
```

### Response 스키마

```python
class ItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    location: LocationResponse | None = None
    created_at: datetime
```

## 예외 처리 패턴

### 커스텀 예외 정의

```python
# apps/exceptions.py
from apps.i18n import _

class AppException(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(
            message or _("Resource not found."),
            404,
        )

class ConflictError(AppException):
    def __init__(self, message: str | None = None):
        super().__init__(
            message or _("Resource already exists."),
            409,
        )
```

### 예외 사용

```python
from apps.exceptions import NotFoundError
from apps.i18n import _

async def get_item(self, id: int) -> Item:
    item = await self.repository.get_by_id(id)
    if not item:
        raise NotFoundError(_("Item not found."))
    return item
```

## 라우터 등록

### `apps/controllers/__init__.py`

```python
from . import auth, voice, items

routers = [
    auth.router,
    voice.router,
    items.router,
]

__all__ = ["routers"]
```

## 의존성 주입 (containers.py)

```python
from dependency_injector import containers, providers
from apps.services.your_service import YourService

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["apps"])
    config = providers.Configuration()

    your_service = providers.Factory(
        YourService,
        repository=your_repository,
    )
```

## 다국어 지원

### 에러 메시지 다국어 처리

```python
from apps.i18n import _

# 번역 가능한 문자열
raise AppException(_("Invalid request."))

# 파라미터 포함
raise AppException(_("Item '{}' not found.").format(item_name))
```

### Accept-Language 헤더

클라이언트가 `Accept-Language: ko-KR` 헤더를 보내면 한국어로 응답합니다.

## API 응답 예시

### 성공 (200 OK)

```json
{
  "code": 200,
  "message": "SUCCESS",
  "result": {
    "id": 1,
    "name": "사과",
    "quantity": 5
  }
}
```

### 생성 (201 Created)

```json
{
  "code": 201,
  "message": "CREATED",
  "result": {
    "id": 1,
    "name": "사과"
  }
}
```

### 에러 (4xx/5xx)

```json
{
  "code": 404,
  "message": "아이템을 찾을 수 없습니다.",
  "result": null
}
```

### 유효성 검증 에러 (422)

```json
{
  "code": 422,
  "message": "VALIDATION_ERROR",
  "result": [
    {
      "field": "body -> name",
      "message": "String should have at least 1 character"
    }
  ]
}
```

## Best Practices

1. **response_model 지정**: OpenAPI 문서 자동 생성
2. **Annotated 타입 힌트**: 의존성 주입에 사용
3. **docstring 작성**: Swagger UI에 설명 표시
4. **다국어 메시지**: `_()` 함수로 번역 가능한 문자열 사용
5. **status_code 명시**: 201, 204 등 성공 코드 명시
6. **Query/Path 설명**: description으로 파라미터 설명

## 참고 파일

- `apps/controllers/auth.py` - 인증 API 예시
- `apps/controllers/voice.py` - 파일 업로드 API 예시
- `apps/schemas/common.py` - 공통 응답 스키마
- `apps/exceptions.py` - 예외 정의
