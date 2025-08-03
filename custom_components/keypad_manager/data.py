"""Custom types for keypad_manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry

    from .storage import KeypadManagerStorage


type KeypadManagerConfigEntry = ConfigEntry[KeypadManagerStorage]


@dataclass
class User:
    """User data structure."""

    id: str
    name: str
    code: str | None = None
    tag: str | None = None
    active: bool = True
    created: datetime | None = None
    last_used: datetime | None = None


@dataclass
class Schedule:
    """Schedule data structure."""

    user_id: str
    day_of_week: int  # 0-6 (Monday-Sunday)
    start_time: str  # HH:MM:SS format
    end_time: str  # HH:MM:SS format
    active: bool = True


@dataclass
class KeypadManagerData:
    """Data for the Keypad Manager integration."""

    users: dict[str, User] | None = None
    schedules: list[Schedule] | None = None
