"""Tests for validation module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.keypad_manager.data import User
from custom_components.keypad_manager.security import SecurityManager
from custom_components.keypad_manager.validation import (
    ValidationError,
    validate_code,
    validate_tag,
    validate_user_has_access_method,
    validate_user_name,
    validate_user_name_and_access_method,
)


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error(self) -> None:
        """Test ValidationError creation."""
        error = ValidationError("Test error")
        assert str(error) == "Test error"


class TestValidateUserName:
    """Test user name validation."""

    def test_valid_name(self) -> None:
        """Test valid user name."""
        validate_user_name("John Doe")
        validate_user_name("AB")  # Minimum length
        validate_user_name("A" * 50)  # Maximum length

    def test_empty_name(self) -> None:
        """Test empty name validation."""
        with pytest.raises(ValidationError, match="User name cannot be empty"):
            validate_user_name("")
        with pytest.raises(ValidationError, match="User name cannot be empty"):
            validate_user_name("   ")

    def test_none_name(self) -> None:
        """Test None name validation."""
        with pytest.raises(ValidationError, match="User name cannot be empty"):
            validate_user_name(None)

    def test_too_short_name(self) -> None:
        """Test name too short."""
        with pytest.raises(ValidationError, match="User name must be at least"):
            validate_user_name("A")

    def test_too_long_name(self) -> None:
        """Test name too long."""
        long_name = "A" * 51
        with pytest.raises(ValidationError, match="User name must be less than"):
            validate_user_name(long_name)


class TestValidateCode:
    """Test code validation."""

    def test_valid_codes(self, security_manager: SecurityManager) -> None:
        """Test valid codes."""
        valid_codes = ["1234", "56789", "12345678"]
        for code in valid_codes:
            validate_code(code, {}, security_manager)

    def test_none_code(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test None code."""
        validate_code(None, sample_users, security_manager)  # Should not raise

    def test_empty_code(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test empty code."""
        with pytest.raises(ValidationError, match="Code cannot be empty if provided"):
            validate_code("", sample_users, security_manager)
        with pytest.raises(ValidationError, match="Code cannot be empty if provided"):
            validate_code("   ", sample_users, security_manager)

    def test_too_short_code(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test code too short."""
        with pytest.raises(ValidationError, match="Code must be"):
            validate_code("123", sample_users, security_manager)

    def test_too_long_code(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test code too long."""
        with pytest.raises(ValidationError, match="Code must be"):
            validate_code("123456789", sample_users, security_manager)

    def test_non_digit_code(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test code with non-digits."""
        with pytest.raises(ValidationError, match="Code must be"):
            validate_code("123a", sample_users, security_manager)
        with pytest.raises(ValidationError, match="Code must be"):
            validate_code("abcd", sample_users, security_manager)

    def test_code_uniqueness(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test code uniqueness checking."""
        # Mock the security manager to return True for verification
        security_manager.verify_code = MagicMock(return_value=True)

        with pytest.raises(ValidationError, match="Code '1234' is already assigned"):
            validate_code("1234", sample_users, security_manager)

    def test_code_uniqueness_exclude_user(
        self, sample_users: dict[str, User], security_manager: SecurityManager
    ) -> None:
        """Test code uniqueness with user exclusion."""
        # Mock the security manager to return False for verification (no conflict)
        security_manager.verify_code = MagicMock(return_value=False)

        # Should not raise when excluding the user that has the code
        validate_code("1234", sample_users, security_manager, exclude_user_id="user1")


class TestValidateTag:
    """Test tag validation."""

    def test_valid_tags(self) -> None:
        """Test valid tags."""
        valid_tags = ["0", "123", "9999", "1"]
        for tag in valid_tags:
            validate_tag(tag, {})

    def test_none_tag(self, sample_users: dict[str, User]) -> None:
        """Test None tag."""
        validate_tag(None, sample_users)  # Should not raise

    def test_empty_tag(self, sample_users: dict[str, User]) -> None:
        """Test empty tag."""
        with pytest.raises(ValidationError, match="Tag cannot be empty if provided"):
            validate_tag("", sample_users)
        with pytest.raises(ValidationError, match="Tag cannot be empty if provided"):
            validate_tag("   ", sample_users)

    def test_too_high_tag(self, sample_users: dict[str, User]) -> None:
        """Test tag too high."""
        with pytest.raises(ValidationError, match="Tag must be a number from"):
            validate_tag("10000", sample_users)

    def test_negative_tag(self, sample_users: dict[str, User]) -> None:
        """Test negative tag."""
        with pytest.raises(ValidationError, match="Tag must be a number"):
            validate_tag("-1", sample_users)

    def test_non_numeric_tag(self, sample_users: dict[str, User]) -> None:
        """Test non-numeric tag."""
        with pytest.raises(ValidationError, match="Tag must be a number"):
            validate_tag("abc", sample_users)
        with pytest.raises(ValidationError, match="Tag must be a number"):
            validate_tag("12ab", sample_users)

    def test_tag_uniqueness(self, sample_users: dict[str, User]) -> None:
        """Test tag uniqueness checking."""
        with pytest.raises(ValidationError, match="Tag '1234' is already assigned"):
            validate_tag("1234", sample_users)

    def test_tag_uniqueness_exclude_user(self, sample_users: dict[str, User]) -> None:
        """Test tag uniqueness with user exclusion."""
        # Should not raise when excluding the user that has the tag
        validate_tag("1234", sample_users, exclude_user_id="user1")

    def test_tag_uniqueness_inactive_user(self, sample_users: dict[str, User]) -> None:
        """Test that inactive users are ignored."""
        # Make user inactive
        sample_users["user1"].active = False

        # Should not raise since the user is inactive
        validate_tag("1234", sample_users)


class TestValidateUserHasAccessMethod:
    """Test access method validation."""

    def test_user_with_code(self) -> None:
        """Test user with code hash."""
        user = User(
            id="test",
            name="Test",
            code_hash="hash",
            code_salt="salt",
            tag=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        validate_user_has_access_method(user)

    def test_user_with_tag(self) -> None:
        """Test user with tag."""
        user = User(
            id="test",
            name="Test",
            code_hash=None,
            code_salt=None,
            tag="1234",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        validate_user_has_access_method(user)

    def test_user_with_both(self) -> None:
        """Test user with both code and tag."""
        user = User(
            id="test",
            name="Test",
            code_hash="hash",
            code_salt="salt",
            tag="1234",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        validate_user_has_access_method(user)

    def test_user_with_neither(self) -> None:
        """Test user with neither code nor tag."""
        user = User(
            id="test",
            name="Test",
            code_hash=None,
            code_salt=None,
            tag=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with pytest.raises(
            ValidationError, match="User must have either a code or tag"
        ):
            validate_user_has_access_method(user)


class TestValidateUserNameAndAccessMethod:
    """Test combined user validation."""

    def test_valid_user(self, sample_user: User) -> None:
        """Test valid user."""
        validate_user_name_and_access_method(sample_user)

    def test_invalid_name(self) -> None:
        """Test user with invalid name."""
        user = User(
            id="test",
            name="",  # Invalid name
            code_hash="hash",
            code_salt="salt",
            tag=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError, match="User name cannot be empty"):
            validate_user_name_and_access_method(user)

    def test_no_access_method(self) -> None:
        """Test user with no access method."""
        user = User(
            id="test",
            name="Test",
            code_hash=None,
            code_salt=None,
            tag=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with pytest.raises(
            ValidationError, match="User must have either a code or tag"
        ):
            validate_user_name_and_access_method(user)
