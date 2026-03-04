import asyncio
import logging

from apps.celery import celery_app
from apps.repositories.device_token import DeviceTokenRepository
from apps.repositories.reminder import ReminderRepository
from apps.services.push import PushService
from apps.types.assistant import ReminderFrequency
from apps.types.reminder import ReminderStatus
from apps.utils.reminder_calculator import ReminderCalculator
from database import Database
from settings import Settings

logger = logging.getLogger(__name__)


@celery_app.task(name="apps.tasks.reminder.process_due_reminders")  # type: ignore[untyped-decorator]
def process_due_reminders() -> None:
    """실행 시각이 된 리마인더를 처리하고 FCM 푸시 알림을 전송합니다."""
    asyncio.run(_async_process())


async def _async_process() -> None:
    database = Database(Settings.database)
    reminder_repo = ReminderRepository(database)
    device_repo = DeviceTokenRepository(database)
    push_svc = PushService(Settings.firebase.credentials_path)

    reminders = await reminder_repo.get_due_reminders()
    logger.info("처리할 리마인더: %d건", len(reminders))

    for reminder in reminders:
        try:
            user_id = reminder.user_id
            if user_id is None:
                logger.warning("리마인더 %d에 user_id가 없습니다.", reminder.id)
                continue

            tokens = await device_repo.get_by_user(user_id)
            if tokens:
                push_svc.send_multicast(
                    tokens=[t.token for t in tokens],
                    title="알림",
                    body=reminder.memory.content,
                )
            else:
                logger.info("리마인더 %d: 등록된 기기 토큰 없음 (user_id=%d)", reminder.id, user_id)

            # next_run_at 갱신 또는 완료 처리
            if reminder.frequency == ReminderFrequency.ONCE:
                reminder.status = ReminderStatus.COMPLETED
                reminder.next_run_at = None
            else:
                reminder.next_run_at = ReminderCalculator.calculate_next_run(
                    frequency=reminder.frequency,
                    time=reminder.time,
                    weekdays=reminder.weekdays,
                    day_of_month=reminder.day_of_month,
                    specific_date=reminder.specific_date,
                )

            await reminder_repo.update(reminder)
            logger.info("리마인더 %d 처리 완료", reminder.id)
        except Exception:
            logger.exception("리마인더 %d 처리 중 오류", reminder.id)
            continue
