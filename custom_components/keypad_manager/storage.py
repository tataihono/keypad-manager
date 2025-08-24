"""Storage manager for keypad_manager."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER
from .data import KeypadManagerData, Schedule, User
from .schedule_manager import ScheduleManager
from .security import SecurityManager
from .user_manager import UserManager

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1


class KeypadManagerStorage:
    """Storage manager for Keypad Manager."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize storage."""
        self.hass = hass
        self.config_entry = config_entry
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.security = SecurityManager(hass)
        self.data: KeypadManagerData | None = None

        # Initialize managers
        self.user_manager = UserManager(self, self.security)
        self.schedule_manager = ScheduleManager(self)

    async def async_load(self) -> KeypadManagerData:
        """Load data from storage."""
        if self.data is not None:
            return self.data

        try:
            stored_data = await self.store.async_load()
            if stored_data is None:
                # Initialize with empty data
                self.data = KeypadManagerData(users={}, schedules=[])
                return self.data

            # Convert stored data to our data structures
            users = {}
            if "users" in stored_data:
                for user_id, user_data in stored_data["users"].items():
                    users[user_id] = User(
                        id=user_data["id"],
                        name=user_data["name"],
                        code_hash=user_data.get("code_hash"),
                        code_salt=user_data.get("code_salt"),
                        tag=user_data.get("tag"),
                        active=user_data.get("active", True),
                        created_at=datetime.fromisoformat(user_data["created_at"]),
                        updated_at=datetime.fromisoformat(user_data["updated_at"]),
                        last_used_at=datetime.fromisoformat(user_data["last_used_at"])
                        if user_data.get("last_used_at")
                        else None,
                    )

            schedules = []
            if "schedules" in stored_data:
                schedules.extend(
                    Schedule(
                        user_id=schedule_data["user_id"],
                        day_of_week=schedule_data["day_of_week"],
                        start_time=schedule_data["start_time"],
                        end_time=schedule_data["end_time"],
                        active=schedule_data.get("active", True),
                        created_at=datetime.fromisoformat(schedule_data["created_at"]),
                        updated_at=datetime.fromisoformat(schedule_data["updated_at"]),
                    )
                    for schedule_data in stored_data["schedules"]
                )

            self.data = KeypadManagerData(users=users, schedules=schedules)
        except (ValueError, KeyError, TypeError) as e:
            LOGGER.error("Error loading Keypad Manager data: %s", e)
            # Return empty data on error
            self.data = KeypadManagerData(users={}, schedules=[])

        return self.data

    async def async_save(self) -> None:
        """Save data to storage."""
        if self.data is None:
            return

        try:
            stored_data = {
                "users": {},
                "schedules": [],
            }

            if self.data.users:
                for user_id, user in self.data.users.items():
                    stored_data["users"][user_id] = {
                        "id": user.id,
                        "name": user.name,
                        "code_hash": user.code_hash,
                        "code_salt": user.code_salt,
                        "tag": user.tag,
                        "active": user.active,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat(),
                        "last_used_at": user.last_used_at.isoformat()
                        if user.last_used_at
                        else None,
                    }

            if self.data.schedules:
                for schedule in self.data.schedules:
                    stored_data["schedules"].append(
                        {
                            "user_id": schedule.user_id,
                            "day_of_week": schedule.day_of_week,
                            "start_time": schedule.start_time,
                            "end_time": schedule.end_time,
                            "active": schedule.active,
                            "created_at": schedule.created_at.isoformat(),
                            "updated_at": schedule.updated_at.isoformat(),
                        }
                    )

            await self.store.async_save(stored_data)

        except (ValueError, KeyError, TypeError) as e:
            LOGGER.error("Error saving Keypad Manager data: %s", e)
