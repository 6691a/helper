# 가정용 물품 관리 앱 - 요구사항 명세서

> **프로젝트명**: Home Inventory API
> **기술스택**: FastAPI + Python + PostgreSQL
> **작성일**: 2025-01-12

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 기능](#2-핵심-기능)
3. [데이터 모델](#3-데이터-모델)
4. [API 명세](#4-api-명세)
5. [개발 단계](#5-개발-단계)
6. [기술 스택 상세](#6-기술-스택-상세)

---

## 1. 프로젝트 개요

### 1.1 목적

가정 내 물품의 위치, 수량, 유통기한을 관리하고, AI 음성 비서를 통해 자연어로 물품 정보를 조회할 수 있는 앱

### 1.2 주요 사용 시나리오

| 시나리오 | 설명 |
|---------|------|
| 물품 등록 | "냉장고에 사과 5개 넣었어" → 위치, 수량, 유통기한 등록 |
| 물품 검색 | "화장실 세제 어디있어?" → "신발장에 2개 있어요" |
| 알림 수신 | 유통기한 3일 전 푸시 알림: "사과가 3일 뒤 상해요" |
| 재고 관리 | 설정한 최소 수량 이하 시 알림: "우유 재고가 부족해요" |
| 교체 알림 | 칫솔, 필터 등 정기 교체 물품 알림 |

### 1.3 대상 사용자

- 1인 가구 ~ 가족 단위 사용자
- 물품 관리가 필요한 소규모 사업장

---

## 2. 핵심 기능

### 2.1 Phase 1: 기본 CRUD (MVP)

#### 2.1.1 위치(Location) 관리

물품이 보관된 장소를 관리합니다.

```
예시: 냉장고, 냉동실, 신발장, 욕실 수납장, 주방 서랍
```

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 위치 목록 조회 | 등록된 모든 위치 조회 | 필수 |
| 위치 상세 조회 | 특정 위치 정보 조회 | 필수 |
| 위치 등록 | 새로운 위치 추가 | 필수 |
| 위치 수정 | 위치 이름/설명 변경 | 필수 |
| 위치 삭제 | 위치 삭제 (물품은 유지, 위치만 null) | 필수 |

#### 2.1.2 카테고리(Category) 관리

물품의 종류를 분류합니다.

```
예시: 과일, 유제품, 생활용품, 세제류, 냉동식품
```

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 카테고리 목록 조회 | 모든 카테고리 조회 | 필수 |
| 카테고리 등록 | 새 카테고리 추가 (기본 유통기한 설정 가능) | 필수 |
| 카테고리 수정 | 카테고리 정보 변경 | 필수 |
| 카테고리 삭제 | 카테고리 삭제 | 필수 |

#### 2.1.3 물품(Item) 관리

실제 물품 정보를 관리합니다.

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 물품 목록 조회 | 모든 물품 조회 | 필수 |
| 물품 상세 조회 | 특정 물품 상세 정보 | 필수 |
| 물품 등록 | 새 물품 추가 | 필수 |
| 물품 수정 | 물품 정보 변경 | 필수 |
| 물품 삭제 | 물품 삭제 | 필수 |
| 물품 검색 | 이름으로 물품 검색 | 필수 |
| 위치별 물품 조회 | 특정 위치의 물품 목록 | 필수 |
| 카테고리별 물품 조회 | 특정 카테고리의 물품 목록 | 필수 |

#### 2.1.4 수량 관리

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 수량 증가 | 물품 추가 구매 시 | 필수 |
| 수량 감소 | 물품 사용 시 | 필수 |
| 재고 부족 목록 | 최소 수량 이하 물품 조회 | 필수 |

---

### 2.2 Phase 2: 알림 시스템

#### 2.2.1 유통기한/교체주기 관리

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 유통기한 임박 목록 | N일 이내 만료 물품 조회 | 필수 |
| 교체 필요 목록 | 교체 주기 도래 물품 조회 | 필수 |
| 교체 완료 처리 | 교체 후 날짜 갱신 | 필수 |

#### 2.2.2 알림 설정(Reminder)

사용자별 알림 규칙을 설정합니다.

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 알림 설정 조회 | 설정된 알림 목록 | 높음 |
| 알림 설정 등록 | 새 알림 규칙 추가 | 높음 |
| 알림 설정 수정 | 알림 규칙 변경 | 높음 |
| 알림 설정 삭제 | 알림 규칙 삭제 | 높음 |
| 알림 on/off 토글 | 개별 알림 활성화/비활성화 | 높음 |

**알림 유형**:
- `EXPIRY`: 유통기한 임박
- `LOW_STOCK`: 재고 부족
- `REPLACEMENT`: 교체 시기

#### 2.2.3 푸시 알림 (FCM)

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| FCM 토큰 등록 | 디바이스 토큰 저장 | 높음 |
| FCM 토큰 삭제 | 로그아웃 시 토큰 제거 | 높음 |
| 알림 발송 스케줄러 | 매일 정해진 시간에 체크 | 높음 |

**스케줄러 동작**:
```
매일 오전 9시 실행 (APScheduler 또는 Celery Beat):
1. 유통기한 N일 이내 물품 체크 → 푸시 발송
2. 재고 부족 물품 체크 → 푸시 발송
3. 교체 필요 물품 체크 → 푸시 발송
```

---

### 2.3 Phase 3: AI 음성 비서

#### 2.3.1 텍스트 질의

자연어로 물품 정보를 질의합니다.

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 텍스트 채팅 | 텍스트로 질문 → AI 응답 | 높음 |

**처리 흐름**:
```
사용자 입력 → LLM (의도 파악) → Function Calling → DB 조회 → 자연어 응답
```

**지원 질의 예시**:
```
"세제 어디있어?" → search_item("세제")
"이번 주 상하는 거 뭐야?" → list_expiring_items(7)
"냉장고에 뭐 있어?" → list_items_by_location("냉장고")
"재고 부족한 거 알려줘" → get_low_stock_items()
"칫솔 갈아야 해?" → get_replacement_needed()
```

#### 2.3.2 음성 질의 (STT + AI + TTS)

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 음성 입력 | 음성 → 텍스트 변환 (STT) | 중간 |
| AI 처리 | 의도 파악 + DB 조회 | 중간 |
| 음성 출력 | 텍스트 → 음성 변환 (TTS) | 중간 |

**AI Function 정의**:

| Function | 파라미터 | 설명 |
|----------|---------|------|
| `search_item` | query: str | 물품 이름으로 검색 |
| `list_expiring_items` | days: int | N일 이내 만료 물품 |
| `list_items_by_location` | location: str | 위치별 물품 조회 |
| `get_low_stock_items` | - | 재고 부족 물품 |
| `get_replacement_needed` | - | 교체 필요 물품 |

---

### 2.4 Phase 4: 사용자 인증 (세션 기반)

멀티유저 지원 시 필요합니다.

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 회원가입 | 이메일/비밀번호 가입 | 선택 |
| 로그인 | 세션 생성 및 쿠키 발급 | 선택 |
| 로그아웃 | 세션 삭제 | 선택 |
| 세션 검증 | 요청 시 세션 유효성 확인 | 선택 |
| 소셜 로그인 | 카카오/구글/애플 (OAuth2 + 세션) | 선택 |

**세션 관리 방식**:
```
- 세션 저장소: Redis (권장) 또는 DB
- 세션 ID는 HTTP-Only, Secure 쿠키로 전달
- 세션 만료 시간: 설정 가능 (기본 24시간)
- 자동 세션 갱신: 활동 시 만료 시간 연장
```

---

### 2.5 Phase 5: 부가 기능 (선택)

#### 2.5.1 통계/대시보드

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 위치별 물품 수 | 위치별 통계 | 선택 |
| 카테고리별 물품 수 | 카테고리별 통계 | 선택 |
| 이번 주 만료 예정 | 주간 요약 | 선택 |

#### 2.5.2 바코드 스캔

| 기능 | 설명 | 우선순위 |
|------|------|---------|
| 바코드 조회 | 바코드로 상품 정보 조회 | 선택 |
| 바코드 정보 캐싱 | 조회된 정보 저장 | 선택 |

---

## 3. 데이터 모델

### 3.1 ERD

```
┌─────────────────┐       ┌─────────────────┐
│    Location     │       │    Category     │
├─────────────────┤       ├─────────────────┤
│ id: int (PK)    │       │ id: int (PK)    │
│ name: str       │       │ name: str       │
│ description:    │       │ default_expiry_ │
│   str | None    │       │   days: int?    │
│ created_at      │       │ created_at      │
│ updated_at      │       │ updated_at      │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │ 1:N                     │ 1:N
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────┐
│                    Item                      │
├─────────────────────────────────────────────┤
│ id: int (PK)                                │
│ name: str                                   │
│ location_id: int (FK) ──────────────────────┤
│ category_id: int (FK) ──────────────────────┤
│ quantity: int                               │
│ min_quantity: int                           │
│ expiry_date: date | None                    │
│ purchased_at: date | None                   │
│ replacement_cycle_days: int | None          │
│ last_replaced_at: date | None               │
│ memo: str | None                            │
│ created_at: datetime                        │
│ updated_at: datetime                        │
└─────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────┐
│                  Reminder                    │
├─────────────────────────────────────────────┤
│ id: int (PK)                                │
│ item_id: int (FK)                           │
│ reminder_type: Enum                         │
│   (EXPIRY, LOW_STOCK, REPLACEMENT)          │
│ days_before: int                            │
│ is_active: bool                             │
│ last_notified_at: datetime | None           │
│ created_at: datetime                        │
│ updated_at: datetime                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                   Device                     │
├─────────────────────────────────────────────┤
│ id: int (PK)                                │
│ fcm_token: str (Unique)                     │
│ device_type: Enum (IOS, ANDROID)            │
│ created_at: datetime                        │
│ updated_at: datetime                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                    User                      │
├─────────────────────────────────────────────┤
│ id: int (PK)                                │
│ email: str (Unique)                         │
│ nickname: str (Unique)                      │
│                             │
│ created_at: datetime                        │
│ updated_at: datetime                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                   Session                    │
├─────────────────────────────────────────────┤
│ id: str (PK)  # UUID                        │
│ user_id: int (FK)                           │
│ expires_at: datetime                        │
│ created_at: datetime                        │
└─────────────────────────────────────────────┘
```

### 3.2 Model 상세

#### Location (위치)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| name | str | NotNull, Unique, max_length=100 | 위치 이름 |
| description | str \| None | max_length=500 | 설명 |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### Category (카테고리)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| name | str | NotNull, Unique, max_length=100 | 카테고리 이름 |
| default_expiry_days | int \| None | ge=1 | 기본 유통기한 (일) |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### Item (물품)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| name | str | NotNull, max_length=200 | 물품 이름 |
| location_id | int \| None | FK | 보관 위치 |
| category_id | int \| None | FK | 카테고리 |
| quantity | int | NotNull, ge=0 | 현재 수량 |
| min_quantity | int | NotNull, ge=0 | 최소 수량 (알림 기준) |
| expiry_date | date \| None | - | 유통기한 |
| purchased_at | date \| None | - | 구매일 |
| replacement_cycle_days | int \| None | ge=1 | 교체 주기 (일) |
| last_replaced_at | date \| None | - | 마지막 교체일 |
| memo | str \| None | max_length=500 | 메모 |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### Reminder (알림 설정)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| item_id | int | FK, NotNull | 대상 물품 |
| reminder_type | Enum | NotNull | 알림 유형 |
| days_before | int | NotNull, default=3 | 며칠 전 알림 |
| is_active | bool | NotNull, default=True | 활성화 여부 |
| last_notified_at | datetime \| None | - | 마지막 알림 발송일 |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### Device (디바이스)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| fcm_token | str | NotNull, Unique | FCM 토큰 |
| device_type | Enum | NotNull | IOS / ANDROID |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### User (사용자)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | int | PK, Auto | 고유 식별자 |
| email | str | NotNull, Unique | 이메일 |
| hashed_password | str | NotNull | 해시된 비밀번호 |
| is_active | bool | NotNull, default=True | 활성화 여부 |
| created_at | datetime | NotNull | 생성일시 |
| updated_at | datetime | NotNull | 수정일시 |

#### Session (세션)

| 필드 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | str | PK | 세션 ID (UUID) |
| user_id | int | FK, NotNull | 사용자 ID |
| expires_at | datetime | NotNull | 만료 시간 |
| created_at | datetime | NotNull | 생성일시 |

---

## 4. API 명세

### 4.1 Location API

| Method | Endpoint | 설명 | Request | Response |
|--------|----------|------|---------|----------|
| GET | `/api/locations` | 목록 조회 | - | `list[LocationResponse]` |
| GET | `/api/locations/{id}` | 상세 조회 | - | `LocationResponse` |
| POST | `/api/locations` | 등록 | `LocationRequest` | `LocationResponse` |
| PUT | `/api/locations/{id}` | 수정 | `LocationRequest` | `LocationResponse` |
| DELETE | `/api/locations/{id}` | 삭제 | - | `204 No Content` |
| GET | `/api/locations/{id}/items` | 위치별 물품 | - | `list[ItemResponse]` |

**LocationRequest** (Pydantic Schema):
```python
class LocationRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)
```

**LocationResponse**:
```json
{
  "id": 1,
  "name": "냉장고",
  "description": "주방 냉장고",
  "created_at": "2025-01-12T10:00:00",
  "updated_at": "2025-01-12T10:00:00"
}
```

---

### 4.2 Category API

| Method | Endpoint | 설명 | Request | Response |
|--------|----------|------|---------|----------|
| GET | `/api/categories` | 목록 조회 | - | `list[CategoryResponse]` |
| GET | `/api/categories/{id}` | 상세 조회 | - | `CategoryResponse` |
| POST | `/api/categories` | 등록 | `CategoryRequest` | `CategoryResponse` |
| PUT | `/api/categories/{id}` | 수정 | `CategoryRequest` | `CategoryResponse` |
| DELETE | `/api/categories/{id}` | 삭제 | - | `204 No Content` |
| GET | `/api/categories/{id}/items` | 카테고리별 물품 | - | `list[ItemResponse]` |

**CategoryRequest**:
```python
class CategoryRequest(BaseModel):
    name: str = Field(..., max_length=100)
    default_expiry_days: int | None = Field(None, ge=1)
```

---

### 4.3 Item API

| Method | Endpoint | 설명 | Request | Response |
|--------|----------|------|---------|----------|
| GET | `/api/items` | 목록 조회 | - | `list[ItemResponse]` |
| GET | `/api/items/{id}` | 상세 조회 | - | `ItemResponse` |
| POST | `/api/items` | 등록 | `ItemCreateRequest` | `ItemResponse` |
| PUT | `/api/items/{id}` | 수정 | `ItemUpdateRequest` | `ItemResponse` |
| DELETE | `/api/items/{id}` | 삭제 | - | `204 No Content` |
| GET | `/api/items/search` | 검색 | query: str | `list[ItemResponse]` |
| GET | `/api/items/low-stock` | 재고 부족 | - | `list[ItemResponse]` |
| GET | `/api/items/expiring` | 유통기한 임박 | days: int = 7 | `list[ItemResponse]` |
| GET | `/api/items/needs-replacement` | 교체 필요 | - | `list[ItemResponse]` |
| PATCH | `/api/items/{id}/quantity/add` | 수량 증가 | `QuantityRequest` | `ItemResponse` |
| PATCH | `/api/items/{id}/quantity/subtract` | 수량 감소 | `QuantityRequest` | `ItemResponse` |
| PATCH | `/api/items/{id}/replace` | 교체 완료 | - | `ItemResponse` |

**ItemCreateRequest**:
```python
class ItemCreateRequest(BaseModel):
    name: str = Field(..., max_length=200)
    location_id: int | None = None
    category_id: int | None = None
    quantity: int = Field(..., ge=0)
    min_quantity: int = Field(0, ge=0)
    expiry_date: date | None = None
    purchased_at: date | None = None
    replacement_cycle_days: int | None = Field(None, ge=1)
    last_replaced_at: date | None = None
    memo: str | None = Field(None, max_length=500)
```

**ItemResponse**:
```json
{
  "id": 1,
  "name": "사과",
  "location": {
    "id": 1,
    "name": "냉장고"
  },
  "category": {
    "id": 1,
    "name": "과일"
  },
  "quantity": 5,
  "min_quantity": 2,
  "expiry_date": "2025-01-20",
  "purchased_at": "2025-01-12",
  "replacement_cycle_days": null,
  "last_replaced_at": null,
  "memo": "후지 사과",
  "is_low_stock": false,
  "needs_replacement": false,
  "created_at": "2025-01-12T10:00:00",
  "updated_at": "2025-01-12T10:00:00"
}
```

**QuantityRequest**:
```python
class QuantityRequest(BaseModel):
    amount: int = Field(..., gt=0)
```

---

### 4.4 Reminder API (Phase 2)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/reminders` | 알림 설정 목록 |
| POST | `/api/reminders` | 알림 설정 등록 |
| PUT | `/api/reminders/{id}` | 알림 설정 수정 |
| DELETE | `/api/reminders/{id}` | 알림 설정 삭제 |
| PATCH | `/api/reminders/{id}/toggle` | 알림 on/off |

---

### 4.5 Device API (Phase 2)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/devices` | FCM 토큰 등록 |
| DELETE | `/api/devices/{token}` | FCM 토큰 삭제 |

---

### 4.6 Auth API (Phase 4 - 세션 기반)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 (세션 생성) |
| POST | `/api/auth/logout` | 로그아웃 (세션 삭제) |
| GET | `/api/auth/me` | 현재 사용자 정보 |

**Login Request**:
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

**Login Response**:
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com"
  },
  "message": "로그인 성공"
}
```
- 세션 ID는 `Set-Cookie` 헤더로 전달 (HttpOnly, Secure, SameSite=Lax)

---

### 4.7 Assistant API (Phase 3)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/assistant/chat` | 텍스트 질의 |
| POST | `/api/assistant/voice` | 음성 질의 (multipart) |

**Chat Request**:
```python
class ChatRequest(BaseModel):
    message: str
```

**Chat Response**:
```json
{
  "answer": "화장실 세제는 신발장에 있어요. 2개 남았어요!",
  "original_query": "세제 어디있어?"
}
```

---

### 4.8 공통 응답 형식

**성공 응답**:
```json
{
  "success": true,
  "data": { ... }
}
```

**에러 응답**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Item(id=999)를 찾을 수 없습니다"
  }
}
```

**에러 코드**:

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| NOT_FOUND | 404 | 리소스 없음 |
| DUPLICATE | 409 | 중복 데이터 |
| VALIDATION_ERROR | 400 | 유효성 검증 실패 |
| UNAUTHORIZED | 401 | 인증 필요 |
| SESSION_EXPIRED | 401 | 세션 만료 |
| INTERNAL_ERROR | 500 | 서버 에러 |

---

## 5. 개발 단계

### 5.1 Phase 1: MVP

```
Week 1:
├── 프로젝트 세팅 (FastAPI, Poetry/uv, 패키지 구조)
├── SQLAlchemy Model 생성 (Location, Category, Item)
├── Pydantic Schema 정의
├── Repository 패턴 구현 (CRUD)
├── Service 계층 구현
└── Router (Controller) 구현

Week 2:
├── 예외 처리 (Exception Handler)
├── Validation 적용 (Pydantic)
├── Swagger/ReDoc 자동 문서화 확인
├── 테스트 코드 작성 (pytest)
└── SQLite → PostgreSQL 전환
```

**완료 조건**:
- [ ] Location CRUD API 동작
- [ ] Category CRUD API 동작
- [ ] Item CRUD API 동작
- [ ] Item 검색, 필터 API 동작
- [ ] 수량 증감 API 동작
- [ ] Swagger UI (`/docs`)에서 테스트 가능

---

### 5.2 Phase 2: 알림 시스템

```
Week 3:
├── Reminder Model 추가
├── Reminder CRUD API
├── Device Model 추가
├── FCM 토큰 관리 API
└── firebase-admin SDK 연동

Week 4:
├── APScheduler 또는 Celery Beat 설정
├── 알림 체크 로직 구현
├── FCM 푸시 발송 구현
└── 테스트
```

**완료 조건**:
- [ ] Reminder CRUD API 동작
- [ ] FCM 토큰 등록/삭제 동작
- [ ] 매일 알림 스케줄러 동작
- [ ] 실제 푸시 알림 수신 확인

---

### 5.3 Phase 3: AI 비서

```
Week 5:
├── Google Gemini API 연동 (google-generativeai)
├── Function Calling 정의
├── /api/assistant/chat 구현
├── 프롬프트 튜닝
└── 테스트
```

**완료 조건**:
- [ ] 텍스트 질의 → AI 응답 동작
- [ ] 다양한 질의 패턴 테스트
- [ ] 응답 자연스러움 확인

---

### 5.4 Phase 4: 세션 기반 인증

```
Week 6:
├── User Model 추가
├── Session Model 추가 (또는 Redis 연동)
├── 비밀번호 해싱 (passlib + bcrypt)
├── 세션 미들웨어 구현
├── 로그인/로그아웃 API
└── 보호된 엔드포인트에 Depends 적용
```

**완료 조건**:
- [ ] 회원가입/로그인/로그아웃 동작
- [ ] 세션 쿠키 발급 확인
- [ ] 인증 필요 API 보호 동작

---

### 5.5 Phase 5: 확장 (선택)

```
부가기능:
├── 통계 API
├── 소셜 로그인 (Authlib)
└── 바코드 스캔
```

---

## 6. 기술 스택 상세

### 6.1 Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 주 개발 언어 |
| FastAPI | 0.110+ | 웹 프레임워크 |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.0+ | 데이터 검증 및 직렬화 |
| PostgreSQL | 16.x | 운영 DB |
| SQLite | - | 개발/테스트 DB |
| Alembic | - | DB 마이그레이션 |
| uvicorn | - | ASGI 서버 |

### 6.2 인증 (세션 기반)

| 기술 | 용도 |
|------|------|
| Redis | 세션 저장소 (선택) |
| passlib[bcrypt] | 비밀번호 해싱 |
| itsdangerous | 세션 ID 서명 (선택) |

### 6.3 알림

| 기술 | 용도 |
|------|------|
| APScheduler | 정기 배치 (단일 인스턴스) |
| Celery + Redis | 정기 배치 (분산 환경) |
| firebase-admin | FCM 푸시 발송 |

### 6.4 AI

| 기술 | 용도 | 비용 |
|------|------|------|
| Gemini 1.5 Flash | LLM (의도 파악, 응답 생성) | $0.075/1M input |
| (대안) GPT-4o-mini | LLM | $0.15/1M input |

### 6.5 개발 도구

| 도구 | 용도 |
|------|------|
| VS Code / PyCharm | IDE |
| uv / Poetry | 패키지 관리 |
| Docker | 컨테이너화 |
| Git | 버전 관리 |
| pytest | 테스트 |
| Ruff | 린터/포매터 |

---

## 프로젝트 구조 (권장)

```
home-inventory-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 생성
│   ├── config.py               # 설정 (Pydantic Settings)
│   ├── database.py             # DB 연결
│   ├── dependencies.py         # 공통 의존성 (세션 검증 등)
│   ├── exceptions.py           # 커스텀 예외
│   │
│   ├── models/                 # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── item.py
│   │   ├── reminder.py
│   │   ├── device.py
│   │   ├── user.py
│   │   └── session.py
│   │
│   ├── schemas/                # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── item.py
│   │   ├── reminder.py
│   │   ├── device.py
│   │   ├── auth.py
│   │   └── common.py
│   │
│   ├── repositories/           # DB 접근 계층
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── item.py
│   │   └── ...
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── item.py
│   │   ├── auth.py
│   │   ├── notification.py
│   │   └── assistant.py
│   │
│   └── routers/                # API 라우터
│       ├── __init__.py
│       ├── location.py
│       ├── category.py
│       ├── item.py
│       ├── reminder.py
│       ├── device.py
│       ├── auth.py
│       └── assistant.py
│
├── alembic/                    # DB 마이그레이션
├── tests/                      # 테스트
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 문서](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2 문서](https://docs.pydantic.dev/latest/)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup)
- [Gemini API 문서](https://ai.google.dev/docs)
- [APScheduler 문서](https://apscheduler.readthedocs.io/)
---

> **문서 버전**: 1.0
> **최종 수정일**: 2025-01-12