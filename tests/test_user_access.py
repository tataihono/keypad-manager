# Copyright (c) 2026 Tataihono Nikora
# SPDX-License-Identifier: MIT
"""Exercise credential access through the current manager and storage boundary."""

from unittest.mock import AsyncMock

import pytest

from custom_components.keypad_manager.storage import KeypadManagerStorage
from custom_components.keypad_manager.user_validator import UserValidationError


@pytest.mark.asyncio
async def test_credentials_survive_storage_round_trip(
    storage_manager: KeypadManagerStorage,
) -> None:
    """Persist hashes and verify access after reloading the serialized record."""
    storage_manager.store.async_load = AsyncMock(return_value=None)
    user = await storage_manager.user_manager.create(
        "Fixture User", code="2468", tag="5678"
    )
    saved = storage_manager.store.async_save.call_args.args[0]
    assert saved["users"][user.id]["code_hash"] != "2468"
    storage_manager.data = None
    storage_manager.store.async_load = AsyncMock(return_value=saved)
    restored = await storage_manager.user_manager.get_by_code("2468")
    assert restored is not None
    assert restored.id == user.id
    assert await storage_manager.user_manager.get_by_code("9999") is None
    assert await storage_manager.user_manager.get_by_tag("5678") == restored


@pytest.mark.asyncio
async def test_inactive_user_cannot_authenticate(
    storage_manager: KeypadManagerStorage,
) -> None:
    """Inactive users must fail both code and tag lookup."""
    storage_manager.store.async_load = AsyncMock(return_value=None)
    user = await storage_manager.user_manager.create(
        "Fixture User", code="2468", tag="5678"
    )
    user.active = False
    assert await storage_manager.user_manager.get_by_code("2468") is None
    assert await storage_manager.user_manager.get_by_tag("5678") is None


@pytest.mark.asyncio
async def test_duplicate_credentials_do_not_change_or_save_users(
    storage_manager: KeypadManagerStorage,
) -> None:
    """Rejected duplicates must leave the persisted user set intact."""
    storage_manager.store.async_load = AsyncMock(return_value=None)
    first = await storage_manager.user_manager.create(
        "First User", code="2468", tag="5678"
    )
    storage_manager.store.async_save.reset_mock()
    with pytest.raises(UserValidationError):
        await storage_manager.user_manager.create("Second User", code="2468")
    with pytest.raises(UserValidationError):
        await storage_manager.user_manager.create("Second User", tag="5678")
    assert list(storage_manager.data.users) == [first.id]
    storage_manager.store.async_save.assert_not_awaited()
