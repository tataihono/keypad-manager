"""KeypadManagerEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class KeypadManagerEntity(Entity):
    """KeypadManagerEntity class."""

    def __init__(self, config_entry) -> None:
        """Initialize."""
        self._attr_unique_id = config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    config_entry.entry_id,
                ),
            },
            name="Keypad Manager",
            manufacturer="Keypad Manager",
        )
