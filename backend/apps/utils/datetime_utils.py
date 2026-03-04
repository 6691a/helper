"""Datetime 변환 유틸리티"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class TimezoneConverter:
    """UTC datetime을 사용자 시간대로 변환하는 유틸리티.

    Pydantic 응답 모델의 모든 datetime 필드를 재귀적으로 탐색하여
    지정된 시간대로 변환합니다.

    사용 예::

        result = TimezoneConverter.model_dump(reminder_response, request.state.timezone)
        return ResponseProvider.success(result)
    """

    @classmethod
    def model_dump(cls, model: BaseModel, timezone: str) -> dict[str, Any]:
        """Pydantic 모델의 datetime 필드를 지정 시간대로 변환하여 dict로 반환합니다."""
        tz = ZoneInfo(timezone)
        raw: dict[str, Any] = model.model_dump()
        return cls._convert_dict(raw, tz)

    @classmethod
    def _convert_dict(cls, d: dict[str, Any], tz: ZoneInfo) -> dict[str, Any]:
        return {k: cls._convert_value(v, tz) for k, v in d.items()}

    @classmethod
    def _convert_value(cls, value: Any, tz: ZoneInfo) -> Any:
        if isinstance(value, datetime):
            return value.astimezone(tz)
        if isinstance(value, dict):
            return cls._convert_dict(value, tz)
        if isinstance(value, list):
            return [cls._convert_value(item, tz) for item in value]
        return value


def format_datetime_for_timezone(dt: datetime, timezone: str) -> str:
    """
    UTC datetime을 지정된 시간대로 변환하여 ISO 8601 형식으로 반환합니다.

    Args:
        dt: UTC datetime 객체 (timezone-aware)
        timezone: IANA 시간대 문자열 (예: "Asia/Seoul", "America/New_York")

    Returns:
        ISO 8601 형식의 문자열 (예: "2026-02-24T15:30:00+09:00")
    """
    try:
        tz = ZoneInfo(timezone)
        return dt.astimezone(tz).isoformat()
    except Exception:
        return dt.isoformat()
