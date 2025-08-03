"""Security functions for keypad_manager."""

from __future__ import annotations

import hashlib
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class SecurityManager:
    """Manages encryption and security for keypad codes."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize security manager."""
        self.hass = hass
        self._salt_length = 32
        self._hash_iterations = 100000  # PBKDF2 iterations

    def _generate_salt(self) -> str:
        """Generate a random salt."""
        return secrets.token_hex(self._salt_length)

    def _hash_value(self, value: str, salt: str) -> str:
        """Hash a value with salt using PBKDF2."""
        if not value:
            return ""

        # Use PBKDF2 with SHA256 for secure hashing
        key = hashlib.pbkdf2_hmac(
            "sha256", value.encode("utf-8"), salt.encode("utf-8"), self._hash_iterations
        )
        return key.hex()

    def encrypt_code(self, code: str | None) -> tuple[str | None, str | None]:
        """Encrypt a code for storage."""
        if code is None:
            return None, None

        salt = self._generate_salt()
        hashed_code = self._hash_value(code, salt)
        return hashed_code, salt

    def verify_code(self, input_code: str, stored_hash: str, salt: str) -> bool:
        """Verify a code against stored hash."""
        if not input_code or not stored_hash or not salt:
            return False

        input_hash = self._hash_value(input_code, salt)
        return secrets.compare_digest(input_hash, stored_hash)

    def secure_compare(self, a: str, b: str) -> bool:
        """Securely compare two strings to prevent timing attacks."""
        return secrets.compare_digest(a, b)
