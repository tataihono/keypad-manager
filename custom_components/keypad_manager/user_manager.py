"""User management for keypad_manager."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .data import User
from .user_validator import UserValidator

if TYPE_CHECKING:
    from .security import SecurityManager
    from .storage import KeypadManagerStorage


class UserManager:
    """Manages user operations for Keypad Manager."""

    def __init__(
        self, storage: KeypadManagerStorage, security: SecurityManager
    ) -> None:
        """Initialize user manager."""
        self.storage = storage
        self.security = security
        self.validator = UserValidator(security)

    async def create(
        self, name: str, code: str | None = None, tag: str | None = None
    ) -> User:
        """Create a user with optional encrypted code and/or plain text tag."""
        await self.storage.async_load()

        code_hash, code_salt = None, None
        if code:
            code_hash, code_salt = self.security.encrypt_code(code)

        user = User(
            id=secrets.token_hex(16),
            name=name,
            code_hash=code_hash,
            code_salt=code_salt,
            tag=tag,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.validator.validate(
            user=user, code=code, tag=tag, users=self.storage.data.users
        )
        self.storage.data.users[user.id] = user
        await self.storage.async_save()
        return user

    async def update_name(self, user_id: str, name: str) -> User:
        """Update a user's name."""
        user = await self.get_by_id(user_id)

        updated_user = User(
            id=user.id,
            name=name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        self.validator.validate(user=updated_user, users=self.storage.data.users)
        self.storage.data.users[user_id] = updated_user
        await self.storage.async_save()
        return updated_user

    async def update_code(self, user_id: str, code: str | None = None) -> User:
        """Update user credentials with validation and encryption."""
        user = await self.get_by_id(user_id)

        code_hash, code_salt = user.code_hash, user.code_salt

        if code and code.strip() != "":
            code_hash, code_salt = self.security.encrypt_code(code)
        else:
            code_hash, code_salt = None, None

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=code_hash,
            code_salt=code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        self.validator.validate(
            user=updated_user, code=code, users=self.storage.data.users
        )
        self.storage.data.users[user_id] = updated_user
        await self.storage.async_save()
        return updated_user

    async def update_tag(self, user_id: str, tag: str | None = None) -> User:
        """Update user tag."""
        user = await self.get_by_id(user_id)

        if tag and tag.strip() == "":
            tag = None

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=user.last_used_at,
        )
        self.validator.validate(
            user=updated_user, tag=tag, users=self.storage.data.users
        )
        self.storage.data.users[user_id] = updated_user
        await self.storage.async_save()
        return updated_user

    async def update_last_used_at(self, user_id: str) -> User:
        """Update user's last used timestamp."""
        user = await self.get_by_id(user_id)

        updated_user = User(
            id=user.id,
            name=user.name,
            code_hash=user.code_hash,
            code_salt=user.code_salt,
            tag=user.tag,
            active=user.active,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
            last_used_at=datetime.now(UTC),
        )
        self.storage.data.users[user_id] = updated_user
        await self.storage.async_save()
        return updated_user

    async def remove(self, user_id: str) -> None:
        """Remove a user from storage."""
        await self.storage.async_load()

        if self.storage.data.users and user_id in self.storage.data.users:
            del self.storage.data.users[user_id]
            await self.storage.async_save()

    async def get_by_code(self, code: str) -> User | None:
        """Get user by code using secure verification."""
        await self.storage.async_load()

        if self.storage.data.users:
            for user in self.storage.data.users.values():
                if not user.active:
                    continue

                if (
                    user.code_hash
                    and user.code_salt
                    and self.security.verify_code(code, user.code_hash, user.code_salt)
                ):
                    return user
        return None

    async def get_by_tag(self, tag: str) -> User | None:
        """Get user by tag using plain text comparison."""
        await self.storage.async_load()

        if self.storage.data.users:
            for user in self.storage.data.users.values():
                if not user.active:
                    continue

                if user.tag == tag:
                    return user
        return None

    async def get_all(self) -> dict[str, User]:
        """Get all users."""
        await self.storage.async_load()
        return self.storage.data.users or {}

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        await self.storage.async_load()

        if self.storage.data.users and user_id in self.storage.data.users:
            return self.storage.data.users[user_id]

        message = f"User with ID '{user_id}' not found"
        raise ValueError(message)
