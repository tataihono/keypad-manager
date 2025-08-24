"""Validation services for keypad_manager integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from custom_components.keypad_manager.const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.keypad_manager.storage import KeypadManagerStorage

# Service schemas with better descriptions and validation
VALIDATE_CODE_SCHEMA = vol.Schema(
    {
        vol.Required(
            "code", description="The numeric or alphanumeric code to validate"
        ): cv.string,
        vol.Optional(
            "source",
            description=(
                "Where this validation request came from "
                "(e.g., 'front_door', 'garage', 'office')"
            ),
        ): cv.string,
    }
)

VALIDATE_TAG_SCHEMA = vol.Schema(
    {
        vol.Required("tag", description="The RFID tag ID to validate"): cv.string,
        vol.Optional(
            "source",
            description=(
                "Where this validation request came from "
                "(e.g., 'front_door', 'garage', 'office')"
            ),
        ): cv.string,
    }
)


def get_storage_instance(hass: HomeAssistant) -> KeypadManagerStorage | None:
    """Get the KeypadManagerStorage instance from runtime data."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if hasattr(entry, "runtime_data") and entry.runtime_data:
            return entry.runtime_data
    return None


async def _check_user_schedule(
    storage: KeypadManagerStorage, user_id: str
) -> tuple[bool, str]:
    """
    Check if user has access based on their schedules.

    Returns:
        tuple: (has_access, reason)

    """
    schedules = await storage.schedule_manager.get_schedules_by_user_id(user_id)

    # If no schedules exist, allow access (no restrictions)
    if not schedules:
        return True, "No schedule restrictions"

    # Check if any schedule allows access
    current_time = datetime.now(UTC)
    current_day = current_time.weekday()  # 0=Monday, 6=Sunday
    current_time_str = current_time.strftime("%H:%M:%S")

    for schedule in schedules:
        if not schedule.active:
            continue

        # Check if current day matches schedule day
        if schedule.day_of_week != current_day:
            continue

        # Check if current time is within schedule window
        if schedule.start_time <= current_time_str <= schedule.end_time:
            return True, "Schedule allows access"

    # No active schedules allow access at current time
    return False, "Outside schedule"


async def async_setup_validation_services(hass: HomeAssistant) -> None:
    """Set up the validation services."""

    async def validate_code_service(call: ServiceCall) -> dict:
        """Validate a code and return the result."""
        code = call.data["code"]
        source = call.data.get("source", "unknown")

        # Get storage instance
        storage = get_storage_instance(hass)
        if not storage:
            error_msg = "Keypad Manager storage not available"
            raise ServiceValidationError(error_msg)

        # Validate the code
        user = await storage.user_manager.get_by_code(code)
        if not user:
            # Fire failure event
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "code": code,
                    "source": source,
                    "reason": "Invalid code",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": None,
                "reason": "Invalid code",
                "source": source,
            }

        # Check if user is active
        if not user.active:
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "code": code,
                    "source": source,
                    "user_name": user.name,
                    "reason": "User inactive",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": "User inactive",
                "source": source,
            }

        # Check schedule
        has_access, reason = await _check_user_schedule(storage, user.id)
        if not has_access:
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "code": code,
                    "source": source,
                    "user_name": user.name,
                    "reason": reason,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": reason,
                "source": source,
            }

        # Success! Update last used and fire event
        await storage.user_manager.update_last_used_at(user.id)
        hass.bus.async_fire(
            "keypad_manager_code_validated",
            {
                "code": code,
                "source": source,
                "user_name": user.name,
                "user_id": user.id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        return {
            "valid": True,
            "user_name": user.name,
            "user_id": user.id,
            "source": source,
        }

    async def validate_tag_service(call: ServiceCall) -> dict:
        """Validate a tag and return the result."""
        tag = call.data["tag"]
        source = call.data.get("source", "unknown")

        # Get storage instance
        storage = get_storage_instance(hass)
        if not storage:
            error_msg = "Keypad Manager storage not available"
            raise ServiceValidationError(error_msg)

        # Validate the tag
        user = await storage.user_manager.get_by_tag(tag)
        if not user:
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "tag": tag,
                    "source": source,
                    "reason": "Invalid tag",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": None,
                "reason": "Invalid tag",
                "source": source,
            }

        # Check if user is active
        if not user.active:
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "tag": tag,
                    "source": source,
                    "user_name": user.name,
                    "reason": "User inactive",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": "User inactive",
                "source": source,
            }

        # Check schedule
        has_access, reason = await _check_user_schedule(storage, user.id)
        if not has_access:
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "tag": tag,
                    "source": source,
                    "user_name": user.name,
                    "reason": reason,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": reason,
                "source": source,
            }

        # Success! Update last used and fire event
        await storage.user_manager.update_last_used_at(user.id)
        hass.bus.async_fire(
            "keypad_manager_tag_validated",
            {
                "tag": tag,
                "source": source,
                "user_name": user.name,
                "user_id": user.id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        return {
            "valid": True,
            "user_name": user.name,
            "user_id": user.id,
            "source": source,
        }

    # Register the validation services
    hass.services.async_register(
        DOMAIN,
        "validate_by_code",
        validate_code_service,
        schema=VALIDATE_CODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "validate_by_tag",
        validate_tag_service,
        schema=VALIDATE_TAG_SCHEMA,
    )

    LOGGER.info("Keypad Manager validation services registered")
