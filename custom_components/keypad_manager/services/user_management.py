"""User management services for keypad_manager integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from custom_components.keypad_manager.const import DOMAIN, LOGGER
from custom_components.keypad_manager.data import User

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.keypad_manager.storage import KeypadManagerStorage

# Service schemas with better descriptions and validation
ADD_USER_SCHEMA = vol.Schema(
    {
        vol.Required("name", description="The user's display name"): cv.string,
        vol.Optional(
            "code", description="The user's access code (optional)"
        ): cv.string,
        vol.Optional("tag", description="The user's RFID tag ID (optional)"): cv.string,
        vol.Optional(
            "active", description="Whether the user is active", default=True
        ): cv.boolean,
    }
)

REMOVE_USER_SCHEMA = vol.Schema(
    {
        vol.Required("user_id", description="The ID of the user to remove"): cv.string,
    }
)


def get_storage_instance(hass: HomeAssistant) -> KeypadManagerStorage | None:
    """Get the KeypadManagerStorage instance from runtime data."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if hasattr(entry, "runtime_data") and entry.runtime_data:
            return entry.runtime_data
    return None


def _create_inactive_user(user: User) -> User:
    """Create an inactive copy of a user."""
    return User(
        id=user.id,
        name=user.name,
        code_hash=user.code_hash,
        code_salt=user.code_salt,
        tag=user.tag,
        active=False,
        created_at=user.created_at,
        updated_at=datetime.now(UTC),
        last_used_at=user.last_used_at,
    )


async def _add_user_impl(
    storage: KeypadManagerStorage,
    name: str,
    code: str | None,
    tag: str | None,
    *,  # Force keyword arguments
    active: bool,
) -> dict:
    """Implement add user logic."""
    # Ensure storage is loaded
    await storage.async_load()
    if storage.data is None:
        error_msg = "Storage data not available"
        raise RuntimeError(error_msg)

    # Create the user
    user = await storage.user_manager.create(
        name=name,
        code=code if code else None,
        tag=tag if tag else None,
    )

    # Set active status if different from default
    if not active and storage.data is not None and storage.data.users is not None:
        updated_user = _create_inactive_user(user)
        storage.data.users[user.id] = updated_user
        await storage.async_save()

    LOGGER.info("User '%s' created successfully with ID: %s", name, user.id)

    return {
        "success": True,
        "user_id": user.id,
        "user_name": user.name,
        "message": f"User '{name}' created successfully",
    }


async def _remove_user_impl(storage: KeypadManagerStorage, user_id: str) -> dict:
    """Implement remove user logic."""
    # Ensure storage is loaded
    await storage.async_load()
    if storage.data is None:
        error_msg = "Storage data not available"
        raise RuntimeError(error_msg)

    # Check if user exists
    user = await storage.user_manager.get_by_id(user_id)
    if user is None:
        error_msg = f"User with ID '{user_id}' not found"
        raise ValueError(error_msg)
    user_name = user.name

    # Remove the user
    await storage.user_manager.remove(user_id)

    # Clean up associated schedules
    await storage.schedule_manager.remove_schedules_by_user_id(user_id)

    LOGGER.info("User '%s' (ID: %s) removed successfully", user_name, user_id)

    return {
        "success": True,
        "user_id": user_id,
        "user_name": user_name,
        "message": f"User '{user_name}' removed successfully",
    }


async def async_setup_user_management_services(hass: HomeAssistant) -> None:
    """Set up the user management services."""

    async def add_user_service(call: ServiceCall) -> dict:
        """Add a new user to the system."""
        name = call.data["name"].strip()
        code = call.data.get("code", "").strip() if call.data.get("code") else None
        tag = call.data.get("tag", "").strip() if call.data.get("tag") else None
        active = call.data.get("active", True)

        # Get storage instance
        storage = get_storage_instance(hass)
        if not storage:
            error_msg = "Keypad Manager storage not available"
            raise ServiceValidationError(error_msg)

        try:
            return await _add_user_impl(storage, name, code, tag, active=active)
        except ValueError as e:
            error_msg = f"Validation error: {e!s}"
            LOGGER.error("Failed to create user '%s': %s", name, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "user_name": name,
            }
        except RuntimeError as e:
            error_msg = f"Storage error: {e!s}"
            LOGGER.error("Failed to create user '%s': %s", name, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "user_name": name,
            }

    async def remove_user_service(call: ServiceCall) -> dict:
        """Remove a user from the system."""
        user_id = call.data["user_id"]

        # Get storage instance
        storage = get_storage_instance(hass)
        if not storage:
            error_msg = "Keypad Manager storage not available"
            raise ServiceValidationError(error_msg)

        try:
            return await _remove_user_impl(storage, user_id)
        except ValueError as e:
            error_msg = f"User not found: {e!s}"
            LOGGER.error("Failed to remove user (ID: %s): %s", user_id, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "user_id": user_id,
            }
        except RuntimeError as e:
            error_msg = f"Storage error: {e!s}"
            LOGGER.error("Failed to remove user (ID: %s): %s", user_id, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "user_id": user_id,
            }

    # Register the user management services
    hass.services.async_register(
        DOMAIN,
        "add_user",
        add_user_service,
        schema=ADD_USER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "remove_user",
        remove_user_service,
        schema=REMOVE_USER_SCHEMA,
    )

    LOGGER.info("Keypad Manager user management services registered")
