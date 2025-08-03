"""Custom types for keypad_manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type KeypadManagerConfigEntry = ConfigEntry[KeypadManagerData]


@dataclass
class KeypadManagerData:
    """Data for the Keypad Manager integration."""

    # This will be expanded as we add user management and storage
    pass
