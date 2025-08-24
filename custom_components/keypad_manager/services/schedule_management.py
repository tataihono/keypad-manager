"""Schedule management services for keypad_manager integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from custom_components.keypad_manager.const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.keypad_manager.storage import KeypadManagerStorage


@dataclass
class ScheduleCreateParams:
    """Parameters for creating a schedule."""

    user_id: str
    day_of_week: int
    start_time: str
    end_time: str
    active: bool = True


@dataclass
class ScheduleUpdateParams:
    """Parameters for updating a schedule."""

    schedule_index: int
    day_of_week: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    active: bool | None = None


# Service schemas with validation
CREATE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(
            "user_id", description="The ID of the user this schedule applies to"
        ): cv.string,
        vol.Required(
            "day_of_week", description="Day of week (0=Monday, 6=Sunday)"
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=6)),
        vol.Required(
            "start_time", description="Start time in HH:MM:SS format"
        ): cv.string,
        vol.Required("end_time", description="End time in HH:MM:SS format"): cv.string,
        vol.Optional(
            "active", description="Whether the schedule is active", default=True
        ): cv.boolean,
    }
)

UPDATE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(
            "schedule_index", description="Index of the schedule to update"
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(
            "day_of_week", description="Day of week (0=Monday, 6=Sunday)"
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=6)),
        vol.Optional(
            "start_time", description="Start time in HH:MM:SS format"
        ): cv.string,
        vol.Optional("end_time", description="End time in HH:MM:SS format"): cv.string,
        vol.Optional(
            "active", description="Whether the schedule is active"
        ): cv.boolean,
    }
)

REMOVE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(
            "schedule_index", description="Index of the schedule to remove"
        ): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)

GET_SCHEDULES_SCHEMA = vol.Schema(
    {
        vol.Required(
            "user_id", description="The ID of the user to get schedules for"
        ): cv.string,
    }
)


def get_storage_instance(hass: HomeAssistant) -> KeypadManagerStorage | None:
    """Get the KeypadManagerStorage instance from runtime data."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if hasattr(entry, "runtime_data") and entry.runtime_data:
            return entry.runtime_data
    return None


async def _create_schedule_impl(
    storage: KeypadManagerStorage, params: ScheduleCreateParams
) -> dict:
    """Implement schedule creation logic."""
    # Ensure storage is loaded
    await storage.async_load()
    if storage.data is None:
        error_msg = "Storage data not available"
        raise RuntimeError(error_msg)

    # Check if user exists
    user = await storage.user_manager.get_by_id(params.user_id)
    if user is None:
        error_msg = f"User with ID '{params.user_id}' not found"
        raise ValueError(error_msg)

    # Create the schedule
    schedule = await storage.schedule_manager.create_schedule(
        user_id=params.user_id,
        day_of_week=params.day_of_week,
        start_time=params.start_time,
        end_time=params.end_time,
        active=params.active,
    )

    LOGGER.info(
        "Schedule created for user '%s' (ID: %s): %s %s-%s",
        user.name,
        params.user_id,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][params.day_of_week],
        params.start_time,
        params.end_time,
    )

    return {
        "success": True,
        "schedule": {
            "user_id": schedule.user_id,
            "day_of_week": schedule.day_of_week,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "active": schedule.active,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
        },
        "user_name": user.name,
        "message": f"Schedule created for user '{user.name}'",
    }


async def _update_schedule_impl(
    storage: KeypadManagerStorage, params: ScheduleUpdateParams
) -> dict:
    """Implement schedule update logic."""
    # Ensure storage is loaded
    await storage.async_load()
    if storage.data is None:
        error_msg = "Storage data not available"
        raise RuntimeError(error_msg)

    # Check if schedule exists
    if not storage.data.schedules or params.schedule_index >= len(
        storage.data.schedules
    ):
        error_msg = f"Schedule at index {params.schedule_index} not found"
        raise ValueError(error_msg)

    # Get the schedule and user info
    schedule = storage.data.schedules[params.schedule_index]
    user = await storage.user_manager.get_by_id(schedule.user_id)
    if user is None:
        error_msg = f"User with ID '{schedule.user_id}' not found"
        raise ValueError(error_msg)

    # Update the schedule
    updated_schedule = await storage.schedule_manager.update_schedule(
        schedule_index=params.schedule_index,
        day_of_week=params.day_of_week,
        start_time=params.start_time,
        end_time=params.end_time,
        active=params.active,
    )

    LOGGER.info(
        "Schedule updated for user '%s' (ID: %s): %s %s-%s",
        user.name,
        schedule.user_id,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][updated_schedule.day_of_week],
        updated_schedule.start_time,
        updated_schedule.end_time,
    )

    return {
        "success": True,
        "schedule": {
            "user_id": updated_schedule.user_id,
            "day_of_week": updated_schedule.day_of_week,
            "start_time": updated_schedule.start_time,
            "end_time": updated_schedule.end_time,
            "active": updated_schedule.active,
            "created_at": updated_schedule.created_at.isoformat(),
            "updated_at": updated_schedule.updated_at.isoformat(),
        },
        "user_name": user.name,
        "message": f"Schedule updated for user '{user.name}'",
    }


async def _remove_schedule_impl(
    storage: KeypadManagerStorage, schedule_index: int
) -> dict:
    """Implement schedule removal logic."""
    # Ensure storage is loaded
    await storage.async_load()
    if storage.data is None:
        error_msg = "Storage data not available"
        raise RuntimeError(error_msg)

    # Check if schedule exists
    if not storage.data.schedules or schedule_index >= len(storage.data.schedules):
        error_msg = f"Schedule at index {schedule_index} not found"
        raise ValueError(error_msg)

    # Get the schedule and user info before removal
    schedule = storage.data.schedules[schedule_index]
    user = await storage.user_manager.get_by_id(schedule.user_id)
    if user is None:
        error_msg = f"User with ID '{schedule.user_id}' not found"
        raise ValueError(error_msg)

    # Remove the schedule
    await storage.schedule_manager.remove_schedule(schedule_index)

    LOGGER.info(
        "Schedule removed for user '%s' (ID: %s): %s %s-%s",
        user.name,
        schedule.user_id,
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][schedule.day_of_week],
        schedule.start_time,
        schedule.end_time,
    )

    return {
        "success": True,
        "schedule_index": schedule_index,
        "user_name": user.name,
        "message": f"Schedule removed for user '{user.name}'",
    }


async def _get_schedules_impl(storage: KeypadManagerStorage, user_id: str) -> dict:
    """Implement get schedules logic."""
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

    # Get schedules for the user
    schedules = await storage.schedule_manager.get_schedules_by_user_id(user_id)

    # Convert schedules to serializable format
    schedule_list = [
        {
            "user_id": schedule.user_id,
            "day_of_week": schedule.day_of_week,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "active": schedule.active,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
        }
        for schedule in schedules
    ]

    return {
        "success": True,
        "user_id": user_id,
        "user_name": user.name,
        "schedules": schedule_list,
        "count": len(schedule_list),
        "message": f"Found {len(schedule_list)} schedules for user '{user.name}'",
    }


def _register_schedule_services(hass: HomeAssistant) -> None:
    """Register the schedule management services."""
    hass.services.async_register(
        DOMAIN,
        "create_schedule",
        _create_schedule_service,
        schema=CREATE_SCHEDULE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "update_schedule",
        _update_schedule_service,
        schema=UPDATE_SCHEDULE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "remove_schedule",
        _remove_schedule_service,
        schema=REMOVE_SCHEDULE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "get_schedules",
        _get_schedules_service,
        schema=GET_SCHEDULES_SCHEMA,
    )


async def _create_schedule_service(call: ServiceCall) -> dict:
    """Create a new schedule."""
    user_id = call.data["user_id"]
    day_of_week = call.data["day_of_week"]
    start_time = call.data["start_time"]
    end_time = call.data["end_time"]
    active = call.data.get("active", True)

    # Get storage instance
    storage = get_storage_instance(call.hass)
    if not storage:
        error_msg = "Keypad Manager storage not available"
        raise ServiceValidationError(error_msg)

    try:
        params = ScheduleCreateParams(
            user_id=user_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            active=active,
        )
        return await _create_schedule_impl(storage, params)
    except ValueError as e:
        error_msg = f"Validation error: {e!s}"
        LOGGER.error("Failed to create schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_id": user_id,
        }
    except RuntimeError as e:
        error_msg = f"Storage error: {e!s}"
        LOGGER.error("Failed to create schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_id": user_id,
        }


async def _update_schedule_service(call: ServiceCall) -> dict:
    """Update an existing schedule."""
    schedule_index = call.data["schedule_index"]
    day_of_week = call.data.get("day_of_week")
    start_time = call.data.get("start_time")
    end_time = call.data.get("end_time")
    active = call.data.get("active")

    # Get storage instance
    storage = get_storage_instance(call.hass)
    if not storage:
        error_msg = "Keypad Manager storage not available"
        raise ServiceValidationError(error_msg)

    try:
        params = ScheduleUpdateParams(
            schedule_index=schedule_index,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            active=active,
        )
        return await _update_schedule_impl(storage, params)
    except ValueError as e:
        error_msg = f"Validation error: {e!s}"
        LOGGER.error("Failed to update schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "schedule_index": schedule_index,
        }
    except RuntimeError as e:
        error_msg = f"Storage error: {e!s}"
        LOGGER.error("Failed to update schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "schedule_index": schedule_index,
        }


async def _remove_schedule_service(call: ServiceCall) -> dict:
    """Remove a schedule."""
    schedule_index = call.data["schedule_index"]

    # Get storage instance
    storage = get_storage_instance(call.hass)
    if not storage:
        error_msg = "Keypad Manager storage not available"
        raise ServiceValidationError(error_msg)

    try:
        return await _remove_schedule_impl(storage, schedule_index)
    except ValueError as e:
        error_msg = f"Validation error: {e!s}"
        LOGGER.error("Failed to remove schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "schedule_index": schedule_index,
        }
    except RuntimeError as e:
        error_msg = f"Storage error: {e!s}"
        LOGGER.error("Failed to remove schedule: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "schedule_index": schedule_index,
        }


async def _get_schedules_service(call: ServiceCall) -> dict:
    """Get schedules for a user."""
    user_id = call.data["user_id"]

    # Get storage instance
    storage = get_storage_instance(call.hass)
    if not storage:
        error_msg = "Keypad Manager storage not available"
        raise ServiceValidationError(error_msg)

    try:
        return await _get_schedules_impl(storage, user_id)
    except ValueError as e:
        error_msg = f"Validation error: {e!s}"
        LOGGER.error("Failed to get schedules: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_id": user_id,
        }
    except RuntimeError as e:
        error_msg = f"Storage error: {e!s}"
        LOGGER.error("Failed to get schedules: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "user_id": user_id,
        }


async def async_setup_schedule_management_services(hass: HomeAssistant) -> None:
    """Set up the schedule management services."""
    _register_schedule_services(hass)
    LOGGER.info("Keypad Manager schedule management services registered")
