"""Sensor platform for keypad_manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import KeypadManagerEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import KeypadManagerConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="active_users",
        name="Active Users",
        icon="mdi:account-group",
    ),
    SensorEntityDescription(
        key="access_count_today",
        name="Access Count Today",
        icon="mdi:counter",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: KeypadManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        KeypadManagerSensor(
            config_entry=entry,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class KeypadManagerSensor(KeypadManagerEntity, SensorEntity):
    """Keypad Manager Sensor class."""

    def __init__(
        self,
        config_entry: KeypadManagerConfigEntry,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(config_entry)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        # TODO(tataihono): Implement actual sensor values
        return "0"
