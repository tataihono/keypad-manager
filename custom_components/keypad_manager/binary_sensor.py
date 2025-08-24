"""Binary sensor platform for keypad_manager."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import KeypadManagerConfigEntry

from .entity import KeypadManagerEntity

# Constants
ACCESS_TIMEOUT_SECONDS = 300  # 5 minutes

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="last_access",
        name="Last Access",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KeypadManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    entities = [
        KeypadManagerBinarySensor(
            config_entry=entry,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    ]

    async_add_entities(entities)

    # Set up event listeners for the binary sensor
    for entity in entities:
        if entity.entity_description.key == "last_access":
            # Listen for both successful code and tag validations
            # Note: Private member access is intentional for event listener setup
            hass.bus.async_listen(
                "keypad_manager_code_validated",
                entity._handle_access_event,  # noqa: SLF001
            )
            hass.bus.async_listen(
                "keypad_manager_tag_validated",
                entity._handle_access_event,  # noqa: SLF001
            )


class KeypadManagerBinarySensor(KeypadManagerEntity, BinarySensorEntity):
    """Keypad Manager binary_sensor class."""

    def __init__(
        self,
        config_entry: KeypadManagerConfigEntry,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(config_entry, entity_description.key)
        self.entity_description = entity_description
        self._last_access_time: datetime | None = None
        self._last_user_name: str | None = None
        self._last_source: str | None = None

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        # Return True if there was access in the last 5 minutes
        if self._last_access_time is None:
            return False

        time_since_access = datetime.now(UTC) - self._last_access_time
        return time_since_access.total_seconds() < ACCESS_TIMEOUT_SECONDS

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return entity specific state attributes."""
        return {
            "last_access_time": self._last_access_time.isoformat()
            if self._last_access_time
            else None,
            "last_user_name": self._last_user_name,
            "last_source": self._last_source,
        }

    def _handle_access_event(self, event: Event) -> None:
        """Handle access events to update the sensor state."""
        event_data = event.data

        # Update the last access time
        self._last_access_time = datetime.now(UTC)
        self._last_user_name = event_data.get("user_name")
        self._last_source = event_data.get("source")

        # Schedule a state update
        if self.hass:
            self.async_write_ha_state()
