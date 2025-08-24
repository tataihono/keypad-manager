"""Schedule validation for keypad_manager."""

from __future__ import annotations

import re

from .const import LOGGER
from .data import Schedule


class ScheduleValidationError(Exception):
    """Raised when schedule validation fails."""


class ScheduleValidator:
    """Validates schedule data for Keypad Manager."""

    def validate_day_of_week(self, day_of_week: int) -> None:
        """Validate day of week (0-6, Monday-Sunday)."""
        if not isinstance(day_of_week, int):
            message = "Day of week must be an integer"
            raise ScheduleValidationError(message)

        if day_of_week < 0 or day_of_week > 6:
            message = "Day of week must be between 0 (Monday) and 6 (Sunday)"
            raise ScheduleValidationError(message)

    def validate_time_format(self, time_str: str) -> None:
        """Validate time format (HH:MM:SS)."""
        if not isinstance(time_str, str):
            message = "Time must be a string"
            raise ScheduleValidationError(message)

        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", time_str):
            message = "Time must be in HH:MM:SS format (e.g., '09:30:00')"
            raise ScheduleValidationError(message)

    def validate_time_range(self, start_time: str, end_time: str) -> None:
        """Validate that start time is before end time."""
        try:
            # Parse times to compare them
            start_parts = [int(x) for x in start_time.split(":")]
            end_parts = [int(x) for x in end_time.split(":")]

            start_seconds = start_parts[0] * 3600 + start_parts[1] * 60 + start_parts[2]
            end_seconds = end_parts[0] * 3600 + end_parts[1] * 60 + end_parts[2]

            if start_seconds >= end_seconds:
                message = "Start time must be before end time"
                raise ScheduleValidationError(message)

        except (ValueError, IndexError) as err:
            message = "Invalid time format"
            raise ScheduleValidationError(message) from err

    def validate_schedule(self, schedule: Schedule) -> None:
        """Validate complete schedule data."""
        try:
            self.validate_day_of_week(schedule.day_of_week)
            self.validate_time_format(schedule.start_time)
            self.validate_time_format(schedule.end_time)
            self.validate_time_range(schedule.start_time, schedule.end_time)

            if not isinstance(schedule.active, bool):
                message = "Active must be a boolean"
                raise ScheduleValidationError(message)

        except ScheduleValidationError as err:
            LOGGER.error("Schedule validation failed: %s", err)
            raise
