"""Main services file for keypad_manager integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import LOGGER
from .services.user_management import async_setup_user_management_services
from .services.validation import async_setup_validation_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up all keypad_manager services."""
    # Set up validation services
    await async_setup_validation_services(hass)

    # Set up user management services
    await async_setup_user_management_services(hass)

    LOGGER.info("All Keypad Manager services registered")
