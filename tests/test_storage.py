"""Tests for storage module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.keypad_manager.data import User
from custom_components.keypad_manager.storage import KeypadManagerStorage

# Constants for test values
EXPECTED_USER_COUNT = 2


class TestKeypadManagerStorage:
    """Test KeypadManagerStorage class."""

    def test_init(self, storage_manager: KeypadManagerStorage) -> None:
        """Test storage manager initialization."""
        assert storage_manager.hass is not None
        assert storage_manager.config_entry is not None
        assert storage_manager.store is not None
        assert storage_manager.security is not None
        assert storage_manager.data is None

    @pytest.mark.asyncio
    async def test_async_load_empty_data(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test loading empty data."""
        storage_manager.store.async_load = AsyncMock(return_value=None)

        result = await storage_manager.async_load()

        assert result.users == {}
        assert result.schedules == []
        assert storage_manager.data == result

    @pytest.mark.asyncio
    async def test_async_load_with_data(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test loading data with existing users."""
        stored_data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "name": "John Doe",
                    "code_hash": "hash1",
                    "code_salt": "salt1",
                    "tag": "1234",
                    "active": True,
                    "created": "2024-01-01T00:00:00+00:00",
                    "last_used": "2024-01-02T00:00:00+00:00",
                }
            },
            "schedules": [],
        }
        storage_manager.store.async_load = AsyncMock(return_value=stored_data)

        result = await storage_manager.async_load()

        assert len(result.users) == 1
        assert "user1" in result.users
        user = result.users["user1"]
        assert user.name == "John Doe"
        assert user.code_hash == "hash1"
        assert user.tag == "1234"
        assert user.active is True

    @pytest.mark.asyncio
    async def test_async_save(self, storage_manager: KeypadManagerStorage) -> None:
        """Test saving data."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {
            "user1": User(
                id="user1",
                name="John Doe",
                code_hash="hash1",
                code_salt="salt1",
                tag="1234",
                active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                last_used_at=datetime.now(UTC),
            )
        }
        storage_manager.data.schedules = []
        storage_manager.store.async_save = AsyncMock()

        await storage_manager.async_save()

        storage_manager.store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_create_user(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test creating a user."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {}

        # Mock the validation functions
        with (
            patch("custom_components.keypad_manager.storage.validate_code"),
            patch("custom_components.keypad_manager.storage.validate_tag"),
            patch(
                "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
            ),
        ):
            user = await storage_manager.async_create_user(
                "John Doe", code="1234", tag="5678"
            )

            assert user.name == "John Doe"
            assert user.code_hash is not None
            assert user.code_salt is not None
            assert user.tag == "5678"
            assert user.active is True
            assert user.created_at is not None
            assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_async_create_user_code_only(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test creating a user with code only."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {}

        with (
            patch("custom_components.keypad_manager.storage.validate_code"),
            patch(
                "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
            ),
        ):
            user = await storage_manager.async_create_user("John Doe", code="1234")

            assert user.name == "John Doe"
            assert user.code_hash is not None
            assert user.code_salt is not None
            assert user.tag is None

    @pytest.mark.asyncio
    async def test_async_create_user_tag_only(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test creating a user with tag only."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {}

        with (
            patch("custom_components.keypad_manager.storage.validate_tag"),
            patch(
                "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
            ),
        ):
            user = await storage_manager.async_create_user("John Doe", tag="5678")

            assert user.name == "John Doe"
            assert user.code_hash is None
            assert user.code_salt is None
            assert user.tag == "5678"

    @pytest.mark.asyncio
    async def test_async_get_user_by_id_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by ID when found."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        result = await storage_manager.async_get_user_by_id("user1")

        assert result == user

    @pytest.mark.asyncio
    async def test_async_get_user_by_id_not_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by ID when not found."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {}

        with pytest.raises(ValueError, match="User with ID 'nonexistent' not found"):
            await storage_manager.async_get_user_by_id("nonexistent")

    @pytest.mark.asyncio
    async def test_async_get_user_by_code_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by code when found."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}
        storage_manager.security.verify_code = MagicMock(return_value=True)

        result = await storage_manager.async_get_user_by_code("1234")

        assert result == user

    @pytest.mark.asyncio
    async def test_async_get_user_by_code_not_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by code when not found."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}
        storage_manager.security.verify_code = MagicMock(return_value=False)

        result = await storage_manager.async_get_user_by_code("5678")

        assert result is None

    @pytest.mark.asyncio
    async def test_async_get_user_by_tag_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by tag when found."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        result = await storage_manager.async_get_user_by_tag("1234")

        assert result == user

    @pytest.mark.asyncio
    async def test_async_get_user_by_tag_not_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting user by tag when not found."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        result = await storage_manager.async_get_user_by_tag("5678")

        assert result is None

    @pytest.mark.asyncio
    async def test_async_get_all_users(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test getting all users."""
        user1 = User(
            id="user1",
            name="John",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        user2 = User(
            id="user2",
            name="Jane",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user1, "user2": user2}

        result = await storage_manager.async_get_all_users()

        assert len(result) == EXPECTED_USER_COUNT
        assert "user1" in result
        assert "user2" in result

    @pytest.mark.asyncio
    async def test_async_update_user_name(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test updating user name."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        with patch(
            "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
        ):
            result = await storage_manager.async_update_user_name("user1", "Jane Doe")

            assert result.name == "Jane Doe"
            assert result.id == "user1"
            assert result.code_hash == "hash1"
            assert result.tag == "1234"

    @pytest.mark.asyncio
    async def test_async_update_user_code(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test updating user code."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="old_hash",
            code_salt="old_salt",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}
        storage_manager.security.encrypt_code = MagicMock(
            return_value=("new_hash", "new_salt")
        )

        with (
            patch("custom_components.keypad_manager.storage.validate_code"),
            patch(
                "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
            ),
        ):
            result = await storage_manager.async_update_user_code("user1", "5678")

            assert result.code_hash == "new_hash"
            assert result.code_salt == "new_salt"
            assert result.name == "John Doe"
            assert result.tag == "1234"

    @pytest.mark.asyncio
    async def test_async_update_user_tag(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test updating user tag."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        with (
            patch("custom_components.keypad_manager.storage.validate_tag"),
            patch(
                "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
            ),
        ):
            result = await storage_manager.async_update_user_tag("user1", "5678")

            assert result.tag == "5678"
            assert result.name == "John Doe"
            assert result.code_hash == "hash1"

    @pytest.mark.asyncio
    async def test_async_update_user_last_used_at(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test updating user last used timestamp."""
        user = User(
            id="user1",
            name="John Doe",
            code_hash="hash1",
            code_salt="salt1",
            tag="1234",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}

        with patch(
            "custom_components.keypad_manager.storage.validate_user_name_and_access_method"
        ):
            result = await storage_manager.async_update_user_last_used_at("user1")

            assert result.last_used_at is not None
            assert result.name == "John Doe"
            assert result.code_hash == "hash1"

    @pytest.mark.asyncio
    async def test_async_remove_user(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test removing a user."""
        user = User(
            id="user1",
            name="John Doe",
            active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        storage_manager.data = MagicMock()
        storage_manager.data.users = {"user1": user}
        storage_manager.store.async_save = AsyncMock()

        await storage_manager.async_remove_user("user1")

        assert "user1" not in storage_manager.data.users
        storage_manager.store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_remove_user_not_found(
        self, storage_manager: KeypadManagerStorage
    ) -> None:
        """Test removing a user that doesn't exist."""
        storage_manager.data = MagicMock()
        storage_manager.data.users = {}
        storage_manager.store.async_save = AsyncMock()

        await storage_manager.async_remove_user("nonexistent")

        # Should not raise an error, just do nothing
        storage_manager.store.async_save.assert_not_called()
