from datetime import UTC, date, datetime, timedelta
from datetime import time as _time

from apps.types.assistant import ReminderFrequency, Weekday


class ReminderCalculator:
    """알림 실행 시간 계산 유틸리티"""

    @staticmethod
    def calculate_next_run_at(
        frequency: ReminderFrequency,
        reminder_time: _time,
        weekday: Weekday | None = None,
        day_of_month: int | None = None,
        specific_date: date | None = None,
    ) -> datetime | None:
        """
        다음 실행 시간을 계산합니다.

        Args:
            frequency: 알림 빈도
            reminder_time: 알림 시간
            weekday: 요일 (주간 알림용)
            day_of_month: 월의 날짜 (월간 알림용)
            specific_date: 특정 날짜 (1회성 알림용)

        Returns:
            다음 실행 시간 또는 None
        """
        now = datetime.now(UTC)

        if frequency == ReminderFrequency.ONCE:
            return ReminderCalculator._calculate_once(specific_date, reminder_time, now)
        elif frequency == ReminderFrequency.DAILY:
            return ReminderCalculator._calculate_daily(reminder_time, now)
        elif frequency == ReminderFrequency.WEEKLY:
            return ReminderCalculator._calculate_weekly(weekday, reminder_time, now)
        elif frequency == ReminderFrequency.MONTHLY:
            return ReminderCalculator._calculate_monthly(day_of_month, reminder_time, now)
        return None

    @staticmethod
    def _calculate_once(
        specific_date: date | None,
        reminder_time: _time,
        now: datetime,
    ) -> datetime | None:
        """1회성 알림의 다음 실행 시간을 계산합니다."""
        if not specific_date:
            return None
        next_dt = datetime.combine(specific_date, reminder_time, tzinfo=UTC)
        return next_dt if next_dt > now else None

    @staticmethod
    def _calculate_daily(reminder_time: _time, now: datetime) -> datetime:
        """매일 알림의 다음 실행 시간을 계산합니다."""
        today_run = datetime.combine(now.date(), reminder_time, tzinfo=UTC)
        if today_run > now:
            return today_run
        return today_run + timedelta(days=1)

    @staticmethod
    def _calculate_weekly(
        weekday: Weekday | None,
        reminder_time: _time,
        now: datetime,
    ) -> datetime | None:
        """매주 알림의 다음 실행 시간을 계산합니다."""
        if not weekday:
            return None

        weekday_map = {
            Weekday.MONDAY: 0,
            Weekday.TUESDAY: 1,
            Weekday.WEDNESDAY: 2,
            Weekday.THURSDAY: 3,
            Weekday.FRIDAY: 4,
            Weekday.SATURDAY: 5,
            Weekday.SUNDAY: 6,
        }
        target_weekday = weekday_map[weekday]
        days_until = (target_weekday - now.weekday()) % 7
        next_date = now.date() + timedelta(days=days_until)
        next_dt = datetime.combine(next_date, reminder_time, tzinfo=UTC)

        if next_dt <= now:
            next_dt += timedelta(days=7)
        return next_dt

    @staticmethod
    def _calculate_monthly(
        day_of_month: int | None,
        reminder_time: _time,
        now: datetime,
    ) -> datetime | None:
        """매월 알림의 다음 실행 시간을 계산합니다."""
        if not day_of_month:
            return None

        # 이번 달 시도
        try:
            next_date = now.date().replace(day=day_of_month)
            next_dt = datetime.combine(next_date, reminder_time, tzinfo=UTC)
            if next_dt > now:
                return next_dt
        except ValueError:
            pass

        # 다음 달로
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)

        try:
            next_date = next_month.date().replace(day=day_of_month)
            return datetime.combine(next_date, reminder_time, tzinfo=UTC)
        except ValueError:
            return None
