from enum import Enum


class ReminderStatus(str, Enum):
    """알림 상태"""

    ACTIVE = "active"  # 활성
    PAUSED = "paused"  # 일시 정지
    COMPLETED = "completed"  # 완료
