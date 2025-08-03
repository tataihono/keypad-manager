"""Storage manager for keypad_manager."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER
from .data import KeypadManagerData, Schedule, User
from .security import SecurityManager
from .validation import (
    validate_code,
    validate_tag,
    validate_user_name_and_access_method,
)

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
                        created_at=datetime.fromisoformat(user_data["created"])
                        if user_data.get("created")
                        else None,
                        updated_at=datetime.fromisoformat(user_data["created"])
                        if user_data.get("created")
                        else None,
                        last_used_at=datetime.fromisoformat(user_data["last_used"])
                        if user_data.get("last_used")
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
                        "created": user.created_at.isoformat()
                        if user.created_at
                        else None,
                        "last_used": user.last_used_at.isoformat()
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
                        }
                    )

            await self.store.async_save(stored_data)

        except (ValueError, KeyError, TypeError) as e:
            LOGGER.error("Error saving Keypad Manager data: %s", e)

    async def async_create_user(
        self, name: str, code: str | None = None, tag: str | None = None
    ) -> User:
        """Create a user with optional encrypted code and/or plain text tag."""
        code_hash, code_salt = None, None
        if code:
            validate_code(code, self.data.users, self.security)
            code_hash, code_salt = self.security.encrypt_code(code)

        if tag:
            validate_tag(tag, self.data.users)

        user = User(
            id=secrets.token_hex(16),
            name=name,
            code_hash=code_hash,
            code_salt=code_salt,
            tag=tag,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        if self.data is None:
            await self.async_load()

        if self.data.users is None:
            self.data.users = {}

        validate_user_name_and_access_method(user)
        self.data.users[user.id] = user
        await self.async_save()
        return user

    async def async_update_user_name(self, user_id: str, name: str) -> User:
        """Update a user in storage."""
        user = await self.async_get_user_by_id(user_id)

        updated_user = User(
            id=user.id,
            name=name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        validate_user_name_and_access_method(updated_user)
        self.data.users[user_id] = updated_user
        await self.async_save()
        return updated_user

    async def async_update_user_code(
        self, user_id: str, code: str | None = None
    ) -> User:
        """Update user credentials with validation and encryption."""
        user = await self.async_get_user_by_id(user_id)

        code_hash, code_salt = user.code_hash, user.code_salt

        if code and code.strip() != "":
            validate_code(code, self.data.users, self.security, user_id)
            code_hash, code_salt = self.security.encrypt_code(code)
        else:
            code_hash, code_salt = None, None

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=code_hash,
            code_salt=code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        validate_user_name_and_access_method(updated_user)
        self.data.users[user_id] = updated_user
        await self.async_save()
        return updated_user

    async def async_update_user_tag(self, user_id: str, tag: str | None = None) -> User:
        """Update user tag."""
        user = await self.async_get_user_by_id(user_id)

        if tag and tag.strip() != "":
            validate_tag(tag, self.data.users, user_id)
        else:
            tag = None

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        validate_user_name_and_access_method(updated_user)
        self.data.users[user_id] = updated_user
        await self.async_save()
        return updated_user

    async def async_update_user_last_used_at(self, user_id: str) -> User:
        """Update user's last used timestamp."""
        user = await self.async_get_user_by_id(user_id)

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=datetime.now(UTC),
        )
        validate_user_name_and_access_method(updated_user)
        self.data.users[user_id] = updated_user
        await self.async_save()
        return updated_user

    async def async_remove_user(self, user_id: str) -> None:
        """Remove a user from storage."""
        if self.data is None:
            await self.async_load()

        if self.data.users and user_id in self.data.users:
            del self.data.users[user_id]
            await self.async_save()

    async def async_get_user_by_code(self, code: str) -> User | None:
        """Get user by code using secure verification."""
        if self.data is None:
            await self.async_load()

        if self.data.users:
            for user in self.data.users.values():
                if not user.active:
                    continue

                if (
                    user.code_hash
                    and user.code_salt
                    and self.security.verify_code(code, user.code_hash, user.code_salt)
                ):
                    return user
        return None

    async def async_get_user_by_tag(self, tag: str) -> User | None:
        """Get user by tag using plain text comparison."""
        if self.data is None:
            await self.async_load()

        if self.data.users:
            for user in self.data.users.values():
                if not user.active:
                    continue

                if user.tag == tag:
                    return user
        return None

    async def async_get_all_users(self) -> dict[str, User]:
        """Get all users."""
        if self.data is None:
            await self.async_load()

        return self.data.users or {}

    async def async_get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        if self.data is None:
            await self.async_load()

        if self.data.users and user_id in self.data.users:
            return self.data.users[user_id]

        message = f"User with ID '{user_id}' not found"
        raise ValueError(message)
