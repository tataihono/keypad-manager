"""KeypadManagerEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

if TYPE_CHECKING:
    from .data import KeypadManagerConfigEntry


class KeypadManagerEntity(Entity):
    """KeypadManagerEntity class."""

    def __init__(self, config_entry: KeypadManagerConfigEntry, entity_key: str) -> None:
        """Initialize."""
        self._attr_unique_id = f"{config_entry.entry_id}_{entity_key}"
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
