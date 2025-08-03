"""Pytest configuration and fixtures for keypad_manager tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.keypad_manager.data import User
from custom_components.keypad_manager.security import SecurityManager
from custom_components.keypad_manager.storage import KeypadManagerStorage


@pytest.fixture
def mock_hass() -> MagicMock:
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.domain = "keypad_manager"
    return entry


@pytest.fixture
def security_manager(mock_hass: MagicMock) -> SecurityManager:
    """Security manager instance."""
    return SecurityManager(mock_hass)


@pytest.fixture
def storage_manager(
    mock_hass: MagicMock, mock_config_entry: MagicMock
) -> KeypadManagerStorage:
    """Storage manager instance."""
    return KeypadManagerStorage(mock_hass, mock_config_entry)


@pytest.fixture
def sample_user() -> User:
    """Sample user for testing."""
    return User(
        id="test_user_1",
        name="Test User",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        code_hash="test_hash",
        code_salt="test_salt",
        tag="1234",
        active=True,
        last_used_at=None,
    )


@pytest.fixture
def sample_users() -> dict[str, User]:
    """Sample users dictionary for testing."""
    return {
        "user1": User(
            id="user1",
            name="John Doe",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            last_used_at=None,
        ),
        "user2": User(
            id="user2",
            name="Jane Smith",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            code_hash="hash2",
            code_salt="salt2",
            tag="5678",
            active=True,
            last_used_at=None,
        ),
    }
