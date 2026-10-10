# Copyright (c) 2025 Tataihono Nikora
# SPDX-License-Identifier: MIT
"""Exercise the integration through Home Assistant's real service registry."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import validate_selector
from homeassistant.util.yaml import load_yaml_dict

from custom_components.keypad_manager.services import async_setup_services
from custom_components.keypad_manager.services.schedule_management import (
    CREATE_SCHEDULE_SCHEMA,
    UPDATE_SCHEDULE_SCHEMA,
)
from custom_components.keypad_manager.storage import KeypadManagerStorage

SUNDAY = 6


@pytest.mark.asyncio
async def test_service_creates_and_removes_user_with_real_storage(
    tmp_path: Path,
) -> None:
    """Keep the service and storage APIs compatible with the supported HA runtime."""
    hass = HomeAssistant(str(tmp_path))
    entry = MagicMock()
    entry.entry_id = "native-service-fixture"
    storage = KeypadManagerStorage(hass, entry)
    entry.runtime_data = storage
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries.return_value = [entry]
    await storage.async_load()
    await async_setup_services(hass)

    await hass.services.async_call(
        "keypad_manager",
        "add_user",
        {"name": "Fixture", "code": "2468"},
        blocking=True,
    )
    assert storage.data is not None
    assert storage.data.users is not None
    user = next(iter(storage.data.users.values()))
    assert user.name == "Fixture"
    assert user.code_hash is not None
    assert user.code_salt is not None
    assert storage.security.verify_code("2468", user.code_hash, user.code_salt)

    await hass.services.async_call(
        "keypad_manager",
        "create_schedule",
        {
            "user_id": user.id,
            "day_of_week": "6",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
        blocking=True,
    )
    assert storage.data.schedules is not None
    assert len(storage.data.schedules) == 1
    assert storage.data.schedules[0].day_of_week == SUNDAY

    reloaded = KeypadManagerStorage(hass, entry)
    data = await reloaded.async_load()
    assert data.users is not None
    assert user.id in data.users
    assert reloaded.security.verify_code(
        "2468", data.users[user.id].code_hash, data.users[user.id].code_salt
    )

    assert data.schedules is not None
    assert data.schedules[0].user_id == user.id
    assert data.schedules[0].day_of_week == SUNDAY

    await hass.services.async_call(
        "keypad_manager",
        "update_schedule",
        {"schedule_index": 0, "day_of_week": "0", "active": False},
        blocking=True,
    )
    updated = await KeypadManagerStorage(hass, entry).async_load()
    assert updated.schedules is not None
    assert updated.schedules[0].day_of_week == 0
    assert updated.schedules[0].active is False

    await hass.services.async_call(
        "keypad_manager", "remove_schedule", {"schedule_index": 0}, blocking=True
    )
    removed = await KeypadManagerStorage(hass, entry).async_load()
    assert removed.schedules == []

    await hass.services.async_call(
        "keypad_manager", "remove_user", {"user_id": user.id}, blocking=True
    )
    assert user.id not in storage.data.users


def test_service_descriptions_use_valid_homeassistant_selectors() -> None:
    """Reject selector descriptions the real HA action editor cannot load."""
    descriptions = load_yaml_dict(
        str(
            Path(__file__).parents[1] / "custom_components/keypad_manager/services.yaml"
        )
    )
    for description in descriptions.values():
        for field in description["fields"].values():
            if "selector" in field:
                validate_selector(field["selector"])


@pytest.mark.parametrize("service_name", ["create_schedule", "update_schedule"])
def test_weekday_selector_values_match_service_schema(service_name: str) -> None:
    """Every action-editor weekday must coerce to its persisted integer value."""
    descriptions = load_yaml_dict(
        str(
            Path(__file__).parents[1] / "custom_components/keypad_manager/services.yaml"
        )
    )
    description = descriptions[service_name]
    assert "target" not in description
    options = description["fields"]["day_of_week"]["selector"]["select"]["options"]
    assert len(options) == SUNDAY + 1
    for weekday, option in enumerate(options):
        assert option["value"] == str(weekday)
        if service_name == "create_schedule":
            result = CREATE_SCHEDULE_SCHEMA(
                {
                    "user_id": "fixture",
                    "day_of_week": option["value"],
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                }
            )
        else:
            result = UPDATE_SCHEDULE_SCHEMA(
                {"schedule_index": 0, "day_of_week": option["value"]}
            )
        assert result["day_of_week"] == weekday
