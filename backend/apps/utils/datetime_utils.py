"""Datetime 변환 유틸리티"""

from datetime import datetime
from zoneinfo import ZoneInfo


def format_datetime_for_timezone(dt: datetime, timezone: str) -> str:
    """
    UTC datetime을 지정된 시간대로 변환하여 포맷팅합니다.

    Args:
        dt: UTC datetime 객체 (timezone-aware)
        timezone: IANA 시간대 문자열 (예: "Asia/Seoul", "America/New_York")

    Returns:
        "YYYY.MM.DD HH:mm" 형식의 문자열 (해당 시간대 기준)
    """
    try:
        # 시간대 변환
        tz = ZoneInfo(timezone)
        local_dt = dt.astimezone(tz)
        # 포맷팅 (점으로 구분, 초 제외)
        return local_dt.strftime("%Y.%m.%d %H:%M")
    except Exception:
        # 잘못된 시간대인 경우 UTC로 폴백
        return dt.strftime("%Y.%m.%d %H:%M")
