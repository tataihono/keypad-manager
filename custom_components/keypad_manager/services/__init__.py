"""Services package for keypad_manager integration."""

from homeassistant.core import HomeAssistant

from .user_management import async_setup_user_management_services
from .validation import async_setup_validation_services

__all__ = [
    "async_setup_services",
    "async_setup_user_management_services",
    "async_setup_validation_services",
]


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up all keypad manager services."""
    await async_setup_user_management_services(hass)
    await async_setup_validation_services(hass)
