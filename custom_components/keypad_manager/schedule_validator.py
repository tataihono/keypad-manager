"""Schedule validation for keypad_manager integration."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .const import LOGGER

if TYPE_CHECKING:
    from .data import Schedule

# Constants
MAX_DAY_OF_WEEK = 6  # Sunday (0=Monday, 6=Sunday)


class ScheduleValidationError(Exception):
    """Raised when schedule validation fails."""


class ScheduleValidator:
    """Validates schedule data for Keypad Manager."""

    def validate_day_of_week(self, day_of_week: int) -> None:
        """Validate day of week (0-6, Monday-Sunday)."""
        if not isinstance(day_of_week, int):
            message = "Day of week must be an integer"
            raise ScheduleValidationError(message)

        if day_of_week < 0 or day_of_week > MAX_DAY_OF_WEEK:
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
        """Validate a schedule."""

        def _raise_error(message: str) -> None:
            """Raise a ScheduleValidationError with the given message."""
            raise ScheduleValidationError(message)

        try:
            # Validate day of week
            if not isinstance(schedule.day_of_week, int):
                _raise_error("Day of week must be an integer")

            if schedule.day_of_week < 0 or schedule.day_of_week > MAX_DAY_OF_WEEK:
                _raise_error("Day of week must be between 0 (Monday) and 6 (Sunday)")

            # Validate time format
            time_pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$"
            if not re.match(time_pattern, schedule.start_time):
                _raise_error("Start time must be in HH:MM:SS format")

            if not re.match(time_pattern, schedule.end_time):
                _raise_error("End time must be in HH:MM:SS format")

            # Validate time logic
            if schedule.start_time >= schedule.end_time:
                _raise_error("Start time must be before end time")

            # Validate active field
            if not isinstance(schedule.active, bool):
                _raise_error("Active must be a boolean")

        except ScheduleValidationError as err:
            LOGGER.error("Schedule validation failed: %s", err)
            raise
