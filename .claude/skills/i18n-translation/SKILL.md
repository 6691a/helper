---
name: i18n-translation
description: 다국어(i18n) 번역 관리 스킬. 메시지 추출, 번역 파일 생성/업데이트, .mo 컴파일을 포함한 전체 번역 워크플로우를 처리합니다.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# i18n Translation Skill

## Overview

GNU gettext 기반 다국어 지원 시스템. 지원 언어: `en` (English, 기본값), `ko` (한국어)

## 프로젝트 구조

```
apps/i18n/
├── __init__.py          # get_locale(), set_locale(), _() 함수
├── middleware.py        # Accept-Language 헤더 처리
└── locales/
    ├── en/LC_MESSAGES/
    │   ├── messages.po  # 영어 번역 (소스)
    │   └── messages.mo  # 영어 컴파일 (바이너리)
    └── ko/LC_MESSAGES/
        ├── messages.po  # 한국어 번역 (소스)
        └── messages.mo  # 한국어 컴파일 (바이너리)
```

## 번역 워크플로우

### 1. 코드에 번역 가능한 문자열 작성

```python
from apps.i18n import _

# 기본 사용
raise AppException(_("Resource not found."))

# 파라미터 포함 (Python format)
message = _("'{}' information has been saved.").format(memory_type)

# f-string은 사용 불가 (번역 추출 안 됨)
# ❌ message = _(f"User {name} created")  # 안 됨
```

### 2. 메시지 추출 (.pot 템플릿 생성)

```bash
# 모든 Python 파일에서 _() 함수로 감싼 문자열 추출
uv run pybabel extract -F babel.cfg -o messages.pot .
```

**결과:** `messages.pot` 파일 생성 (번역 템플릿)

### 3. 번역 파일 생성/업데이트

#### 새 언어 추가

```bash
# 일본어 추가 예시
uv run pybabel init -i messages.pot -d apps/i18n/locales -l ja
```

**결과:** `apps/i18n/locales/ja/LC_MESSAGES/messages.po` 생성

#### 기존 번역 업데이트

```bash
# 기존 .po 파일에 새 메시지 추가 (기존 번역 유지)
uv run pybabel update -i messages.pot -d apps/i18n/locales
```

**결과:** 모든 언어의 `.po` 파일에 새 메시지 추가, 기존 번역은 보존

### 4. 번역 작성

`.po` 파일을 열어 `msgstr`에 번역 추가:

```po
# apps/i18n/locales/ko/LC_MESSAGES/messages.po

#: apps/services/assistant.py:162
msgid ""
"Sorry, I didn't understand your request. "
"Please remember information or ask a question."
msgstr "죄송합니다, 요청을 이해하지 못했습니다. 정보를 기억하거나 질문해주세요."

#: apps/services/assistant.py:260
#, python-brace-format
msgid "'{}' information has been saved."
msgstr "'{}' 정보를 저장했습니다."
```

**중요:**
- `msgid`: 원본 문자열 (영어, 코드에서 추출)
- `msgstr`: 번역된 문자열 (각 언어)
- `#, python-brace-format`: `{}` 포맷 사용 표시

### 5. 번역 컴파일 (.mo 생성)

```bash
# .po → .mo (바이너리) 변환
uv run pybabel compile -d apps/i18n/locales
```

**결과:** 각 언어의 `messages.mo` 파일 생성/갱신 (런타임에서 사용)

## 전체 워크플로우 (한 번에)

```bash
# 1. 메시지 추출
uv run pybabel extract -F babel.cfg -o messages.pot .

# 2. 기존 번역 업데이트
uv run pybabel update -i messages.pot -d apps/i18n/locales

# 3. .po 파일 편집 (수동)
# apps/i18n/locales/ko/LC_MESSAGES/messages.po 열어서 msgstr 번역

# 4. 컴파일
uv run pybabel compile -d apps/i18n/locales
```

## 클라이언트 사용법

### HTTP 헤더

```http
Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7
```

- 우선순위가 높은 언어부터 나열
- 서버는 지원하는 언어 중 최우선 언어 선택

### 응답 예시

```json
// Accept-Language: ko
{
  "code": 404,
  "message": "리소스를 찾을 수 없습니다.",
  "result": null
}

// Accept-Language: en
{
  "code": 404,
  "message": "Resource not found.",
  "result": null
}
```

## 지원 언어 추가하기

### 1. `apps/i18n/__init__.py`에 언어 코드 추가

```python
SUPPORTED_LOCALES = ["en", "ko", "ja"]  # 일본어 추가
```

### 2. 번역 파일 생성

```bash
uv run pybabel init -i messages.pot -d apps/i18n/locales -l ja
```

### 3. 번역 작성 → 컴파일

```bash
# apps/i18n/locales/ja/LC_MESSAGES/messages.po 편집
uv run pybabel compile -d apps/i18n/locales
```

## 번역 파일 구조

### babel.cfg

```ini
[python: apps/**.py]
encoding = utf-8
```

프로젝트 루트에 위치. pybabel이 어느 파일에서 메시지를 추출할지 정의.

### messages.pot (템플릿)

```pot
#: apps/services/assistant.py:162
msgid "Sorry, I didn't understand your request."
msgstr ""
```

- 번역 대상 문자열 목록
- `msgstr`은 비어있음 (템플릿)

### messages.po (번역 소스)

```po
msgid "Sorry, I didn't understand your request."
msgstr "죄송합니다, 요청을 이해하지 못했습니다."
```

- 언어별 번역 작성
- 사람이 직접 편집

### messages.mo (컴파일된 바이너리)

- `.po`를 컴파일한 바이너리 파일
- 런타임에서 빠르게 로드
- Git에 커밋하지 않음 (보통 `.gitignore`에 추가)

## Best Practices

1. **코드에서 _() 사용**: 모든 사용자 대면 메시지는 `_()` 함수로 감싸기
2. **파라미터화**: f-string 대신 `.format()` 사용
   ```python
   # ✅
   _("User {} created").format(name)

   # ❌
   _(f"User {name} created")  # 추출 안 됨
   ```
3. **짧고 명확한 메시지**: 번역하기 쉽게 작성
4. **컨텍스트 제공**: 동일한 영어 단어가 다른 의미일 때 주석 추가
   ```python
   # Translators: 버튼 레이블
   _("Save")

   # Translators: 데이터 저장 완료 메시지
   _("Save")
   ```
5. **정기적인 업데이트**: 새 메시지 추가 시 즉시 번역 워크플로우 실행

## 참고 파일

- `apps/i18n/__init__.py` - i18n 핵심 함수
- `apps/i18n/middleware.py` - Accept-Language 처리
- `apps/exceptions.py` - 예외 메시지 다국어 처리 예시
- `babel.cfg` - pybabel 설정