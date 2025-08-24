"""Services for keypad_manager integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from .data import KeypadManagerConfigEntry

# Service schemas
VALIDATE_CODE_SCHEMA = vol.Schema(
    {
        vol.Required("code"): cv.string,
        vol.Optional("source", default="unknown"): cv.string,
    }
)

VALIDATE_TAG_SCHEMA = vol.Schema(
    {
        vol.Required("tag"): cv.string,
        vol.Optional("source", default="unknown"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the keypad_manager services."""

    async def validate_code_service(call: ServiceCall) -> None:
        """Validate a user code and check access permissions."""
        code = call.data["code"]
        source = call.data["source"]

        LOGGER.info("Validating code from source: %s", source)

        # Get the storage instance from any config entry
        config_entries = hass.config_entries.async_entries(DOMAIN)
        if not config_entries:
            raise ServiceValidationError("No Keypad Manager configuration found")

        storage = config_entries[0].runtime_data

        # Validate the code using the user manager
        user = await storage.user_manager.get_by_code(code)

        if user is None:
            LOGGER.warning(
                "Code validation failed: invalid code from source %s", source
            )
            # Fire failure event
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": "invalid_code",
                },
            )
            return

        # Check if user has access based on schedules
        user_schedules = await storage.schedule_manager.get_schedules_by_user_id(
            user.id
        )

        if not user_schedules:
            # No schedules means always allow access
            access_granted = True
            reason = "no_schedules"
        else:
            # Check if current time falls within any active schedule
            now = datetime.now(UTC)
            current_day = now.weekday()
            current_time = now.strftime("%H:%M:%S")

            access_granted = False
            reason = "outside_schedule"

            for schedule in user_schedules:
                if not schedule.active:
                    continue

                if schedule.day_of_week == current_day:
                    if schedule.start_time <= current_time <= schedule.end_time:
                        access_granted = True
                        reason = "within_schedule"
                        break

        if access_granted:
            # Update last used timestamp
            await storage.user_manager.update_last_used_at(user.id)

            LOGGER.info(
                "Code validation successful for user %s from source %s (reason: %s)",
                user.name,
                source,
                reason,
            )

            # Fire success event
            hass.bus.async_fire(
                "keypad_manager_code_validated",
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": reason,
                },
            )
        else:
            LOGGER.warning(
                "Code validation failed for user %s from source %s: outside schedule",
                user.name,
                source,
            )

            # Fire failure event
            hass.bus.async_fire(
                "keypad_manager_code_failed",
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": reason,
                },
            )

    async def validate_tag_service(call: ServiceCall) -> None:
        """Validate a user tag and check access permissions."""
        tag = call.data["tag"]
        source = call.data["source"]

        LOGGER.info("Validating tag from source: %s", source)

        # Get the storage instance from any config entry
        config_entries = hass.config_entries.async_entries(DOMAIN)
        if not config_entries:
            raise ServiceValidationError("No Keypad Manager configuration found")

        storage = config_entries[0].runtime_data

        # Validate the tag using the user manager
        user = await storage.user_manager.get_by_tag(tag)

        if user is None:
            LOGGER.warning("Tag validation failed: invalid tag from source %s", source)
            # Fire failure event
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": "invalid_tag",
                },
            )
            return

        # Check if user has access based on schedules
        user_schedules = await storage.schedule_manager.get_schedules_by_user_id(
            user.id
        )

        if not user_schedules:
            # No schedules means always allow access
            access_granted = True
            reason = "no_schedules"
        else:
            # Check if current time falls within any active schedule
            now = datetime.now(UTC)
            current_day = now.weekday()
            current_time = now.strftime("%H:%M:%S")

            access_granted = False
            reason = "outside_schedule"

            for schedule in user_schedules:
                if not schedule.active:
                    continue

                if schedule.day_of_week == current_day:
                    if schedule.start_time <= current_time <= schedule.end_time:
                        access_granted = True
                        reason = "within_schedule"
                        break

        if access_granted:
            # Update last used timestamp
            await storage.user_manager.update_last_used_at(user.id)

            LOGGER.info(
                "Tag validation successful for user %s from source %s (reason: %s)",
                user.name,
                source,
                reason,
            )

            # Fire success event
            hass.bus.async_fire(
                "keypad_manager_tag_validated",
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": reason,
                },
            )
        else:
            LOGGER.warning(
                "Tag validation failed for user %s from source %s: outside schedule",
                user.name,
                source,
            )

            # Fire failure event
            hass.bus.async_fire(
                "keypad_manager_tag_failed",
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "source": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "reason": reason,
                },
            )

    # Register the services
    hass.services.async_register(
        DOMAIN,
        "validate_code",
        validate_code_service,
        schema=VALIDATE_CODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "validate_tag",
        validate_tag_service,
        schema=VALIDATE_TAG_SCHEMA,
    )

    LOGGER.info("Keypad Manager services registered")
