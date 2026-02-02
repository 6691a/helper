from apps.exceptions import NotFoundError
from apps.i18n import _
from apps.models.reminder import Reminder
from apps.repositories.memory import MemoryRepository
from apps.repositories.reminder import ReminderRepository
from apps.schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate
from apps.types.reminder import ReminderStatus
from apps.utils.reminder_calculator import ReminderCalculator


class ReminderService:
    """Reminder 서비스"""

    def __init__(
        self,
        reminder_repository: ReminderRepository,
        memory_repository: MemoryRepository,
    ):
        self.reminder_repository = reminder_repository
        self.memory_repository = memory_repository

    async def get_reminder(self, reminder_id: int, user_id: int | None = None) -> ReminderResponse:
        """Reminder를 조회합니다."""
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            raise NotFoundError(_("Reminder not found."))
        return ReminderResponse.model_validate(reminder)

    async def get_reminders(
        self,
        user_id: int | None = None,
        status: ReminderStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReminderResponse]:
        """Reminder 목록을 조회합니다."""
        reminders = await self.reminder_repository.get_all(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return [ReminderResponse.model_validate(r) for r in reminders]

    async def create_reminder(self, data: ReminderCreate, user_id: int | None = None) -> ReminderResponse:
        """Reminder를 생성합니다."""
        # Memory 존재 확인
        memory = await self.memory_repository.get_by_id(data.memory_id, user_id)
        if not memory:
            raise NotFoundError(_("Memory not found."))

        reminder = Reminder(
            memory_id=data.memory_id,
            frequency=data.frequency,
            weekday=data.weekday,
            day_of_month=data.day_of_month,
            specific_date=data.specific_date,
            time=data.time,
            user_id=user_id,
        )
        reminder.next_run_at = ReminderCalculator.calculate_next_run_at(
            frequency=data.frequency,
            reminder_time=data.time,
            weekday=data.weekday,
            day_of_month=data.day_of_month,
            specific_date=data.specific_date,
        )
        saved = await self.reminder_repository.create(reminder)
        return ReminderResponse.model_validate(saved)

    async def update_reminder(
        self, reminder_id: int, data: ReminderUpdate, user_id: int | None = None
    ) -> ReminderResponse:
        """Reminder를 수정합니다."""
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            raise NotFoundError(_("Reminder not found."))

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)

        # next_run_at 재계산
        reminder.next_run_at = ReminderCalculator.calculate_next_run_at(
            frequency=reminder.frequency,
            reminder_time=reminder.time,
            weekday=reminder.weekday,
            day_of_month=reminder.day_of_month,
            specific_date=reminder.specific_date,
        )
        updated = await self.reminder_repository.update(reminder)
        return ReminderResponse.model_validate(updated)

    async def delete_reminder(self, reminder_id: int, user_id: int | None = None) -> None:
        """Reminder를 삭제합니다."""
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            raise NotFoundError(_("Reminder not found."))
        await self.reminder_repository.delete(reminder)

    async def pause_reminder(self, reminder_id: int, user_id: int | None = None) -> ReminderResponse:
        """Reminder를 일시정지합니다."""
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            raise NotFoundError(_("Reminder not found."))

        reminder.status = ReminderStatus.PAUSED
        updated = await self.reminder_repository.update(reminder)
        return ReminderResponse.model_validate(updated)

    async def resume_reminder(self, reminder_id: int, user_id: int | None = None) -> ReminderResponse:
        """Reminder를 재개합니다."""
        reminder = await self.reminder_repository.get_by_id(reminder_id, user_id)
        if not reminder:
            raise NotFoundError(_("Reminder not found."))

        reminder.status = ReminderStatus.ACTIVE
        reminder.next_run_at = ReminderCalculator.calculate_next_run_at(
            frequency=reminder.frequency,
            reminder_time=reminder.time,
            weekday=reminder.weekday,
            day_of_month=reminder.day_of_month,
            specific_date=reminder.specific_date,
        )
        updated = await self.reminder_repository.update(reminder)
        return ReminderResponse.model_validate(updated)
