import gettext
from contextvars import ContextVar
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ["en", "ko"]

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)


def get_locale() -> str:
    """현재 요청의 locale을 반환합니다."""
    return _current_locale.get()


def set_locale(locale: str) -> None:
    """현재 요청의 locale을 설정합니다."""
    if locale in SUPPORTED_LOCALES:
        _current_locale.set(locale)
    else:
        _current_locale.set(DEFAULT_LOCALE)


def get_translator(locale: str) -> gettext.GNUTranslations | gettext.NullTranslations:
    """지정된 locale의 번역기를 반환합니다."""
    try:
        return gettext.translation(
            domain="messages",
            localedir=str(LOCALES_DIR),
            languages=[locale],
        )
    except FileNotFoundError:
        return gettext.NullTranslations()


def _(message: str) -> str:
    """메시지를 현재 locale로 번역합니다."""
    locale = get_locale()
    translator = get_translator(locale)
    return translator.gettext(message)


def parse_accept_language(header: str | None) -> str:
    """Accept-Language 헤더를 파싱하여 최적의 locale을 반환합니다."""
    if not header:
        return DEFAULT_LOCALE

    # "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7" 형식 파싱
    languages = []
    for part in header.split(","):
        part = part.strip()
        if ";q=" in part:
            lang, q = part.split(";q=")
            languages.append((lang.strip(), float(q)))
        else:
            languages.append((part, 1.0))

    # 우선순위 정렬
    languages.sort(key=lambda x: x[1], reverse=True)

    # 지원하는 locale 찾기
    for lang, _ in languages:
        lang_code = lang.split("-")[0].lower()
        if lang_code in SUPPORTED_LOCALES:
            return lang_code

    return DEFAULT_LOCALE
