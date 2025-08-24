"""Sensor platform for keypad_manager integration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

if TYPE_CHECKING:
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import KeypadManagerConfigEntry

from .entity import KeypadManagerEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="active_users",
        name="Active Users",
        icon="mdi:account-group",
    ),
    SensorEntityDescription(
        key="access_valid_today",
        name="Access Valid Today",
        icon="mdi:lock-check",
    ),
    SensorEntityDescription(
        key="access_invalid_today",
        name="Access Invalid Today",
        icon="mdi:lock-alert",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KeypadManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entities = [
        KeypadManagerSensor(
            config_entry=entry,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    ]

    async_add_entities(entities)

    # Set up event listeners for the sensors
    for entity in entities:
        if entity.entity_description.key == "access_valid_today":
            # Listen for successful validations to increment valid access count
            # Note: Private member access is intentional for event listener setup
            hass.bus.async_listen(
                "keypad_manager_code_validated",
                entity._handle_access_event,  # noqa: SLF001
            )
            hass.bus.async_listen(
                "keypad_manager_tag_validated",
                entity._handle_access_event,  # noqa: SLF001
            )
        elif entity.entity_description.key == "access_invalid_today":
            # Listen for failed attempts to increment invalid access count
            hass.bus.async_listen(
                "keypad_manager_code_failed",
                entity._handle_access_event,  # noqa: SLF001
            )
            hass.bus.async_listen(
                "keypad_manager_tag_failed",
                entity._handle_access_event,  # noqa: SLF001
            )


class KeypadManagerSensor(KeypadManagerEntity, SensorEntity):
    """Keypad Manager Sensor class."""

    def __init__(
        self,
        config_entry: KeypadManagerConfigEntry,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(config_entry, entity_description.key)
        self.entity_description = entity_description
        self._access_valid_today = 0
        self._access_invalid_today = 0
        self._last_reset_date = datetime.now(UTC).date()
        self._config_entry = config_entry

    @property
    def native_value(self) -> str | int:
        """Return the native value of the sensor."""
        if self.entity_description.key == "active_users":
            # Get active user count from storage
            if (
                hasattr(self._config_entry, "runtime_data")
                and self._config_entry.runtime_data
            ):
                storage = self._config_entry.runtime_data
                if storage.data and storage.data.users:
                    active_count = sum(
                        1 for user in storage.data.users.values() if user.active
                    )
                    return str(active_count)
            return "0"

        if self.entity_description.key == "access_valid_today":
            # Check if we need to reset the valid access counter for a new day
            current_date = datetime.now(UTC).date()
            if current_date != self._last_reset_date:
                self._access_valid_today = 0
                self._last_reset_date = current_date

            return self._access_valid_today

        if self.entity_description.key == "access_invalid_today":
            # Check if we need to reset the invalid access counter for a new day
            current_date = datetime.now(UTC).date()
            if current_date != self._last_reset_date:
                self._access_invalid_today = 0
                self._last_reset_date = current_date

            return self._access_invalid_today

        return "0"

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        """Return entity specific state attributes."""
        if self.entity_description.key == "active_users":
            # Get detailed user statistics
            if (
                hasattr(self._config_entry, "runtime_data")
                and self._config_entry.runtime_data
            ):
                storage = self._config_entry.runtime_data
                if storage.data and storage.data.users:
                    users_with_codes = sum(
                        1
                        for user in storage.data.users.values()
                        if user.active and user.code_hash
                    )
                    users_with_tags = sum(
                        1
                        for user in storage.data.users.values()
                        if user.active and user.tag
                    )
                    total_users = len(storage.data.users)

                    return {
                        "total_users": total_users,
                        "users_with_codes": users_with_codes,
                        "users_with_tags": users_with_tags,
                    }

            return {
                "total_users": 0,
                "users_with_codes": 0,
                "users_with_tags": 0,
            }

        if self.entity_description.key == "access_valid_today":
            return {
                "last_reset_date": self._last_reset_date.isoformat(),
            }

        if self.entity_description.key == "access_invalid_today":
            return {
                "last_reset_date": self._last_reset_date.isoformat(),
            }

        return {}

    def _handle_access_event(self, _event: Event) -> None:
        """Handle access events to increment the appropriate counter."""
        if self.entity_description.key == "access_valid_today":
            # Increment valid access count
            self._access_valid_today += 1
        elif self.entity_description.key == "access_invalid_today":
            # Increment invalid access count
            self._access_invalid_today += 1
        self.schedule_update_ha_state()
