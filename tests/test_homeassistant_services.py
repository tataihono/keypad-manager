"""Exercise the integration through Home Assistant's real service registry."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.keypad_manager.services import async_setup_services
from custom_components.keypad_manager.storage import KeypadManagerStorage

if TYPE_CHECKING:
    from pathlib import Path


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

    reloaded = KeypadManagerStorage(hass, entry)
    data = await reloaded.async_load()
    assert data.users is not None
    assert user.id in data.users
    assert reloaded.security.verify_code(
        "2468", data.users[user.id].code_hash, data.users[user.id].code_salt
    )

    await hass.services.async_call(
        "keypad_manager", "remove_user", {"user_id": user.id}, blocking=True
    )
    assert user.id not in storage.data.users
