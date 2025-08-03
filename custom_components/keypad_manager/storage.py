"""Storage manager for keypad_manager."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER
from .data import KeypadManagerData, Schedule, User

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1


class KeypadManagerStorage:
    """Storage manager for Keypad Manager."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize storage."""
        self.hass = hass
        self.config_entry = config_entry
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: KeypadManagerData | None = None

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
                        code=user_data.get("code"),
                        tag=user_data.get("tag"),
                        active=user_data.get("active", True),
                        created=datetime.fromisoformat(user_data["created"]) if user_data.get("created") else None,
                        last_used=datetime.fromisoformat(user_data["last_used"]) if user_data.get("last_used") else None,
                    )

            schedules = []
            if "schedules" in stored_data:
                for schedule_data in stored_data["schedules"]:
                    schedules.append(Schedule(
                        user_id=schedule_data["user_id"],
                        day_of_week=schedule_data["day_of_week"],
                        start_time=schedule_data["start_time"],
                        end_time=schedule_data["end_time"],
                        active=schedule_data.get("active", True),
                    ))

            self.data = KeypadManagerData(users=users, schedules=schedules)
            return self.data

        except Exception as e:
            LOGGER.error("Error loading Keypad Manager data: %s", e)
            # Return empty data on error
            self.data = KeypadManagerData(users={}, schedules=[])
            return self.data

    async def async_save(self) -> None:
        """Save data to storage."""
        if self.data is None:
            return

        try:
            # Convert our data structures to JSON-serializable format
            stored_data = {
                "users": {},
                "schedules": [],
            }

            if self.data.users:
                for user_id, user in self.data.users.items():
                    stored_data["users"][user_id] = {
                        "id": user.id,
                        "name": user.name,
                        "code": user.code,
                        "tag": user.tag,
                        "active": user.active,
                        "created": user.created.isoformat() if user.created else None,
                        "last_used": user.last_used.isoformat() if user.last_used else None,
                    }

            if self.data.schedules:
                for schedule in self.data.schedules:
                    stored_data["schedules"].append({
                        "user_id": schedule.user_id,
                        "day_of_week": schedule.day_of_week,
                        "start_time": schedule.start_time,
                        "end_time": schedule.end_time,
                        "active": schedule.active,
                    })

            await self.store.async_save(stored_data)

        except Exception as e:
            LOGGER.error("Error saving Keypad Manager data: %s", e)

    async def async_add_user(self, user: User) -> None:
        """Add a user to storage."""
        if self.data is None:
            await self.async_load()
        
        if self.data.users is None:
            self.data.users = {}
        
        self.data.users[user.id] = user
        await self.async_save()

    async def async_remove_user(self, user_id: str) -> None:
        """Remove a user from storage."""
        if self.data is None:
            await self.async_load()
        
        if self.data.users and user_id in self.data.users:
            del self.data.users[user_id]
            await self.async_save()

    async def async_get_user_by_code(self, code: str) -> User | None:
        """Get user by code."""
        if self.data is None:
            await self.async_load()
        
        if self.data.users:
            for user in self.data.users.values():
                if user.code == code and user.active:
                    return user
        return None

    async def async_get_user_by_tag(self, tag: str) -> User | None:
        """Get user by tag."""
        if self.data is None:
            await self.async_load()
        
        if self.data.users:
            for user in self.data.users.values():
                if user.tag == tag and user.active:
                    return user
        return None

    async def async_update_user_last_used(self, user_id: str) -> None:
        """Update user's last used timestamp."""
        if self.data is None:
            await self.async_load()
        
        if self.data.users and user_id in self.data.users:
            self.data.users[user_id].last_used = datetime.now()
            await self.async_save() 