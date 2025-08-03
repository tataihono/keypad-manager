"""Validation functions for keypad_manager."""

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


class ValidationError(Exception):
    """Raised when validation fails."""


def validate_user_name(name: str) -> None:
    """Validate user name."""
    if not name or not name.strip():
        message = "User name cannot be empty"
        raise ValidationError(message)

    if len(name.strip()) < MIN_USER_NAME_LENGTH:
        message = f"User name must be at least {MIN_USER_NAME_LENGTH} characters"
        raise ValidationError(message)

    if len(name.strip()) > MAX_USER_NAME_LENGTH:
        message = f"User name must be less than {MAX_USER_NAME_LENGTH} characters"
        raise ValidationError(message)


def validate_code(
    code: str | None,
    users: dict[str, User],
    security_manager: SecurityManager,
    exclude_user_id: str | None = None,
) -> None:
    """Validate keypad code format."""
    if code is None:
        return

    if not code.strip():
        message = "Code cannot be empty if provided"
        raise ValidationError(message)

    if not re.match(f"^[0-9]{{{MIN_CODE_LENGTH},{MAX_CODE_LENGTH}}}$", code.strip()):
        message = f"Code must be {MIN_CODE_LENGTH}-{MAX_CODE_LENGTH} digits"
        raise ValidationError(message)

    for user_id, user in users.items():
        if exclude_user_id and user_id == exclude_user_id:
            continue
        if user.active and (
            user.code_hash
            and user.code_salt
            and security_manager.verify_code(code, user.code_hash, user.code_salt)
        ):
            message = f"Code '{code}' is already assigned"
            raise ValidationError(message)


def validate_tag(
    tag: str | None,
    users: dict[str, User],
    exclude_user_id: str | None = None,
) -> None:
    """Validate RFID tag format."""
    if tag is None:
        return

    if not tag.strip():
        message = "Tag cannot be empty if provided"
        raise ValidationError(message)

    if not re.match(r"^[0-9]+$", tag.strip()):
        message = "Tag must be a number"
        raise ValidationError(message)

    try:
        tag_value = int(tag.strip())
        if tag_value < MIN_TAG_VALUE or tag_value > MAX_TAG_VALUE:
            message = f"Tag must be a number from {MIN_TAG_VALUE} to {MAX_TAG_VALUE}"
            raise ValidationError(message)
    except ValueError as err:
        message = "Tag must be a number"
        raise ValidationError(message) from err

    for user_id, user in users.items():
        if exclude_user_id and user_id == exclude_user_id:
            continue
        if user.active and user.tag == tag.strip():
            message = f"Tag '{tag}' is already assigned"
            raise ValidationError(message)


def validate_user_has_access_method(user: User) -> None:
    """Validate that user has at least one access method."""
    if not user.code_hash and not user.tag:
        message = "User must have either a code or tag"
        raise ValidationError(message)


def validate_user_name_and_access_method(user: User) -> None:
    """Validate complete user data."""
    try:
        validate_user_name(user.name)
        validate_user_has_access_method(user)
    except ValidationError as err:
        LOGGER.error("User validation failed: %s", err)
        raise
