# 통합 정보 기억 앱 - 요구사항 명세서

> **프로젝트명**: Memory Assistant API
> **기술스택**: FastAPI + PostgreSQL + LangChain + pgvector
> **최종 수정일**: 2025-01-17

---

## 1. 프로젝트 개요

### 1.1 목적

**다양한 정보를 AI가 자동으로 파싱하여 저장하고, 시맨틱 검색으로 자연어 질의에 응답**하는 통합 정보 기억 시스템

### 1.2 핵심 아이디어

**모든 정보는 Memory** - 물품, 장소, 일정, 메모 등 모든 것을 하나의 Memory 모델로 통합 관리

### 1.3 사용 시나리오

| 입력 예시 | 저장 (type) | 검색 예시 | 응답 |
|----------|-------------|----------|------|
| "냉장고에 사과 5개 넣었어" | item | "사과 어디있어?" | "냉장고에 5개 있어요" |
| "자생한방병원은 서대문역 6번 출구" | place | "척추 치료 어디가 좋아?" | "자생한방병원이요, 서대문역 6번 출구로 가세요" |
| "엄마 생일은 5월 3일" | person | "엄마 생일 언제야?" | "5월 3일이에요" |
| "다음 주 월요일 치과 예약" | schedule | "치과 언제 가?" | "다음 주 월요일이에요" |

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        처리 흐름                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [저장]                                                     │
│  사용자 입력 (음성/텍스트)                                    │
│      ↓                                                      │
│  LangChain + Gemini → 구조화 파싱 (type, keywords, content)  │
│      ↓                                                      │
│  Gemini Embedding → 벡터 생성                                │
│      ↓                                                      │
│  PostgreSQL + pgvector → 저장                                │
│                                                             │
│  [검색]                                                     │
│  사용자 질문                                                 │
│      ↓                                                      │
│  Gemini Embedding → 쿼리 벡터                                │
│      ↓                                                      │
│  pgvector 유사도 검색 → 관련 Memory 반환                      │
│      ↓                                                      │
│  LangChain + Gemini → 자연어 응답 생성                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터 모델

### 3.1 Memory (단일 통합 모델)

```
┌─────────────────────────────────────────────────────────────┐
│                        Memory                                │
├─────────────────────────────────────────────────────────────┤
│ id: int (PK)                                                │
│ type: str (item, place, schedule, person, memo)             │
│ keywords: str (검색용 키워드, 쉼표 구분)                       │
│ content: str (AI가 정리한 핵심 내용)                          │
│ metadata: JSONB (유형별 추가 정보, 유연한 확장)                │
│ original_text: str (원본 입력 텍스트)                         │
│ embedding: vector(768) (Gemini 임베딩)                       │
│ user_id: int (FK) | None                                    │
│ created_at: datetime                                        │
│ updated_at: datetime                                        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 metadata 예시 (유형별)

```python
# type: "item" (물품)
{"location": "냉장고", "quantity": 5, "expiry_date": "2025-01-20"}

# type: "place" (장소)
{"place": "자생한방병원", "method": "서대문역 6번 출구", "category": "병원"}

# type: "schedule" (일정)
{"date": "2025-01-20", "time": "14:00", "location": "강남역"}

# type: "person" (인물)
{"name": "엄마", "relation": "가족", "birthday": "05-03"}

# type: "memo" (일반)
{"tags": ["중요", "업무"]}
```

---

## 4. API 명세

### 4.1 Assistant API (핵심)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/assistant/chat` | 텍스트 입력 → AI가 저장/검색 자동 판단 |
| POST | `/api/assistant/voice` | 음성 입력 → STT → 저장/검색 |

**Request**:
```json
{ "message": "냉장고에 사과 5개 넣었어" }
```

**Response**:
```json
{
  "action": "save",
  "answer": "냉장고에 사과 5개 저장했어요!",
  "memory": { "id": 1, "type": "item", ... }
}
```

### 4.2 Memory API (직접 관리)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/memories` | 저장된 정보 목록 |
| GET | `/api/memories/{id}` | 특정 정보 상세 |
| DELETE | `/api/memories/{id}` | 정보 삭제 |

### 4.3 기존 API (구현 완료)

| API | 상태 |
|-----|------|
| Voice API (`/api/v1/voice/transcribe`) | ✅ 완료 |
| Auth API (`/api/v1/auth/*`) | ✅ 완료 |

---

## 5. 기술 스택

| 분류 | 기술 | 용도 |
|------|------|------|
| Framework | FastAPI | 웹 프레임워크 |
| ORM | SQLModel | DB 모델 |
| Database | PostgreSQL + pgvector | 데이터 + 벡터 저장 |
| AI | LangChain | AI 오케스트레이션 |
| LLM | langchain-google-genai | Gemini 연동 |
| Vector | langchain-postgres | pgvector 연동 |
| Session | Redis | 세션 저장소 |
| STT | Google Cloud Speech | 음성 인식 |

---

## 6. 구현 순서

```
1. pyproject.toml에 LangChain 패키지 추가
   - langchain, langchain-google-genai, langchain-postgres, pgvector

2. PostgreSQL에 pgvector 확장 설치

3. 설정 추가
   - apps/types/assistant.py (AssistantConfig)
   - settings.py, env/local.yaml 업데이트

4. Memory 모델 생성 및 마이그레이션
   - apps/models/memory.py
   - alembic revision & upgrade

5. Memory 스키마 생성
   - apps/schemas/memory.py

6. LangChain 서비스 구현
   - apps/services/assistant.py
   - 파싱, 임베딩, 검색, 응답 생성

7. Controller 구현
   - apps/controllers/assistant.py
   - apps/controllers/memory.py

8. DI 및 라우터 등록
   - containers.py
   - apps/controllers/__init__.py
```

---

## 7. 시맨틱 검색 예시

| 저장된 정보 | 검색 질문 | 매칭 (의미 기반) |
|------------|----------|-----------------|
| "냉장고에 사과 있어" | "과일 뭐 있어?" | 사과 ⊂ 과일 |
| "척추 디스크 - 자생한방병원" | "허리 아파 어디 가?" | 척추 ≈ 허리 |
| "엄마 생일 5월 3일" | "5월에 뭐 있어?" | 날짜 매칭 |

---

> **문서 버전**: 2.0