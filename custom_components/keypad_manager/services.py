"""Services for keypad_manager integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import voluptuous as vol

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .storage import KeypadManagerStorage

from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, LOGGER

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


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the keypad_manager services."""

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
        user = storage.user_manager.get_user_by_code(code)
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
        schedule = storage.schedule_manager.get_schedule_by_user_id(user.id)
        if schedule and not schedule.is_active():
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "code": code,
                    "source": source,
                    "user_name": user.name,
                    "reason": "Outside schedule",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": "Outside schedule",
                "source": source,
            }

        # Success! Update last used and fire event
        storage.user_manager.update_user_last_used(user.id)
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
        user = storage.user_manager.get_user_by_tag(tag)
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
        schedule = storage.schedule_manager.get_schedule_by_user_id(user.id)
        if schedule and not schedule.is_active():
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "tag": tag,
                    "source": source,
                    "user_name": user.name,
                    "reason": "Outside schedule",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return {
                "valid": False,
                "user_name": user.name,
                "reason": "Outside schedule",
                "source": source,
            }

        # Success! Update last used and fire event
        storage.user_manager.update_user_last_used(user.id)
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

    # Register the services with better names and schemas
    hass.services.async_register(
        DOMAIN,
        "validate_by_code",  # Changed from validate_code
        validate_code_service,
        schema=VALIDATE_CODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "validate_by_tag",  # Changed from validate_tag
        validate_tag_service,
        schema=VALIDATE_TAG_SCHEMA,
    )

    LOGGER.info("Keypad Manager services registered")
