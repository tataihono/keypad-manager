"""User validation for keypad_manager."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .const import (
    LOGGER,
    MAX_CODE_LENGTH,
    MAX_TAG_VALUE,
    MAX_USER_NAME_LENGTH,
    MIN_CODE_LENGTH,
    MIN_TAG_VALUE,
    MIN_USER_NAME_LENGTH,
)

if TYPE_CHECKING:
    from .data import User
    from .security import SecurityManager


class UserValidationError(Exception):
    """Raised when user validation fails."""


class UserValidator:
    """Validates user data for Keypad Manager."""

    def __init__(self, security_manager: SecurityManager) -> None:
        """Initialize user validator."""
        self.security = security_manager

    def _validate_name(self, name: str) -> None:
        """Validate user name."""
        if not name or not name.strip():
            message = "User name cannot be empty"
            raise UserValidationError(message)

        if len(name.strip()) < MIN_USER_NAME_LENGTH:
            message = f"User name must be at least {MIN_USER_NAME_LENGTH} characters"
            raise UserValidationError(message)

        if len(name.strip()) > MAX_USER_NAME_LENGTH:
            message = f"User name must be less than {MAX_USER_NAME_LENGTH} characters"
            raise UserValidationError(message)

    def _validate_code(
        self,
        code: str | None,
        users: dict[str, User],
        exclude_user_id: str | None = None,
    ) -> None:
        """Validate keypad code format."""
        if code is None:
            return

        if not code.strip():
            message = "Code cannot be empty if provided"
            raise UserValidationError(message)

        if not re.match(
            f"^[0-9]{{{MIN_CODE_LENGTH},{MAX_CODE_LENGTH}}}$", code.strip()
        ):
            message = f"Code must be {MIN_CODE_LENGTH}-{MAX_CODE_LENGTH} digits"
            raise UserValidationError(message)

        for user_id, user in users.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            if user.active and (
                user.code_hash
                and user.code_salt
                and self.security.verify_code(code, user.code_hash, user.code_salt)
            ):
                message = f"Code '{code}' is already assigned"
                raise UserValidationError(message)

    def _validate_tag(
        self,
        tag: str | None,
        users: dict[str, User],
        exclude_user_id: str | None = None,
    ) -> None:
        """Validate RFID tag format."""
        if tag is None:
            return

        if not tag.strip():
            message = "Tag cannot be empty if provided"
            raise UserValidationError(message)

        if not re.match(r"^[0-9]+$", tag.strip()):
            message = "Tag must be a number"
            raise UserValidationError(message)

        try:
            tag_value = int(tag.strip())
            if tag_value < MIN_TAG_VALUE or tag_value > MAX_TAG_VALUE:
                message = (
                    f"Tag must be a number from {MIN_TAG_VALUE} to {MAX_TAG_VALUE}"
                )
                raise UserValidationError(message)
        except ValueError as err:
            message = "Tag must be a number"
            raise UserValidationError(message) from err

        for user_id, user in users.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            if user.active and user.tag == tag.strip():
                message = f"Tag '{tag}' is already assigned"
                raise UserValidationError(message)

    def _validate_has_access_method(self, user: User) -> None:
        """Validate that user has at least one access method."""
        if not user.code_hash and not user.tag:
            message = "User must have either a code or tag"
            raise UserValidationError(message)

    def validate(
        self,
        *,
        user: User,
        users: dict[str, User],
        code: str | None = None,
        tag: str | None = None,
    ) -> None:
        """Validate complete user data."""
        try:
            self._validate_name(user.name)
            self._validate_has_access_method(user)
            if code:
                self._validate_code(code, users, user.id)
            if tag:
                self._validate_tag(tag, users, user.id)
        except UserValidationError as err:
            LOGGER.error("User validation failed: %s", err)
            raise
