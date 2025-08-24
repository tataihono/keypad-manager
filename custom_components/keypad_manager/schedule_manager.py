"""Schedule management for keypad_manager."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .data import Schedule
from .schedule_validator import ScheduleValidator

if TYPE_CHECKING:
    from .storage import KeypadManagerStorage


class ScheduleManager:
    """Manages schedule operations for Keypad Manager."""

    def __init__(self, storage: KeypadManagerStorage) -> None:
        """Initialize schedule manager."""
        self.storage = storage
        self.validator = ScheduleValidator()

    async def create_schedule(
        self,
        user_id: str,
        day_of_week: int,
        start_time: str,
        end_time: str,
        active: bool = True,
    ) -> Schedule:
        """Create a new schedule."""
        await self.storage.async_load()

        schedule = Schedule(
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            active=active,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.validator.validate_schedule(schedule)
        self.storage.data.schedules.append(schedule)
        await self.storage.async_save()
        return schedule

    async def update_schedule(
        self,
        schedule_index: int,
        day_of_week: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        active: bool | None = None,
    ) -> Schedule:
        """Update a schedule."""
        await self.storage.async_load()

        if not self.storage.data.schedules or schedule_index >= len(
            self.storage.data.schedules
        ):
            message = f"Schedule at index {schedule_index} not found"
            raise ValueError(message)

        schedule = self.storage.data.schedules[schedule_index]

        updated_schedule = Schedule(
            user_id=schedule.user_id,
            day_of_week=day_of_week
            if day_of_week is not None
            else schedule.day_of_week,
            start_time=start_time if start_time is not None else schedule.start_time,
            end_time=end_time if end_time is not None else schedule.end_time,
            active=active if active is not None else schedule.active,
            created_at=schedule.created_at,
            updated_at=datetime.now(UTC),
        )

        self.validator.validate_schedule(updated_schedule)
        self.storage.data.schedules[schedule_index] = updated_schedule
        await self.storage.async_save()
        return updated_schedule

    async def remove_schedule(self, schedule_index: int) -> None:
        """Remove a schedule."""
        await self.storage.async_load()

        if not self.storage.data.schedules or schedule_index >= len(
            self.storage.data.schedules
        ):
            message = f"Schedule at index {schedule_index} not found"
            raise ValueError(message)

        del self.storage.data.schedules[schedule_index]
        await self.storage.async_save()

    async def get_schedules_by_user_id(self, user_id: str) -> list[Schedule]:
        """Get all schedules for a specific user."""
        await self.storage.async_load()

        if not self.storage.data.schedules:
            return []

        return [
            schedule
            for schedule in self.storage.data.schedules
            if schedule.user_id == user_id
        ]

    async def get_all_schedules(self) -> list[Schedule]:
        """Get all schedules."""
        await self.storage.async_load()
        return self.storage.data.schedules or []

    async def get_schedule_by_index(self, schedule_index: int) -> Schedule:
        """Get schedule by index."""
        await self.storage.async_load()

        if not self.storage.data.schedules or schedule_index >= len(
            self.storage.data.schedules
        ):
            message = f"Schedule at index {schedule_index} not found"
            raise ValueError(message)

        return self.storage.data.schedules[schedule_index]

    async def remove_schedules_by_user_id(self, user_id: str) -> None:
        """Remove all schedules for a specific user."""
        await self.storage.async_load()

        if not self.storage.data.schedules:
            return

        self.storage.data.schedules = [
            schedule
            for schedule in self.storage.data.schedules
            if schedule.user_id != user_id
        ]
        await self.storage.async_save()
