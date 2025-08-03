"""Tests for security module."""

from custom_components.keypad_manager.security import SecurityManager

# Constants for test values
SALT_LENGTH = 32
HASH_ITERATIONS = 100000
HEX_LENGTH = 64  # 32 bytes = 64 hex chars


class TestSecurityManager:
    """Test SecurityManager class."""

    def test_init(self, security_manager: SecurityManager) -> None:
        """Test SecurityManager initialization."""
        assert security_manager._salt_length == SALT_LENGTH
        assert security_manager._hash_iterations == HASH_ITERATIONS

    def test_generate_salt(self, security_manager: SecurityManager) -> None:
        """Test salt generation."""
        salt1 = security_manager._generate_salt()
        salt2 = security_manager._generate_salt()

        assert len(salt1) == HEX_LENGTH  # 32 bytes = 64 hex chars
        assert len(salt2) == HEX_LENGTH
        assert salt1 != salt2  # Should be unique

    def test_hash_value(self, security_manager: SecurityManager) -> None:
        """Test value hashing."""
        value = "1234"
        salt = security_manager._generate_salt()

        hash1 = security_manager._hash_value(value, salt)
        hash2 = security_manager._hash_value(value, salt)

        assert hash1 == hash2  # Same input should produce same hash
        assert len(hash1) == HEX_LENGTH  # SHA256 = 32 bytes = 64 hex chars

    def test_hash_value_different_salts(
        self, security_manager: SecurityManager
    ) -> None:
        """Test that different salts produce different hashes."""
        value = "1234"
        salt1 = security_manager._generate_salt()
        salt2 = security_manager._generate_salt()

        hash1 = security_manager._hash_value(value, salt1)
        hash2 = security_manager._hash_value(value, salt2)

        assert hash1 != hash2  # Different salts should produce different hashes

    def test_hash_value_empty_string(self, security_manager: SecurityManager) -> None:
        """Test hashing empty string."""
        salt = security_manager._generate_salt()
        result = security_manager._hash_value("", salt)
        assert result == ""

    def test_encrypt_code(self, security_manager: SecurityManager) -> None:
        """Test code encryption."""
        code = "1234"
        hash_result, salt = security_manager.encrypt_code(code)

        assert hash_result is not None
        assert salt is not None
        assert len(salt) == HEX_LENGTH
        assert len(hash_result) == HEX_LENGTH

    def test_encrypt_code_none(self, security_manager: SecurityManager) -> None:
        """Test encrypting None code."""
        hash_result, salt = security_manager.encrypt_code(None)
        assert hash_result is None
        assert salt is None

    def test_verify_code_success(self, security_manager: SecurityManager) -> None:
        """Test successful code verification."""
        code = "1234"
        hash_result, salt = security_manager.encrypt_code(code)

        assert security_manager.verify_code(code, hash_result, salt)

    def test_verify_code_failure(self, security_manager: SecurityManager) -> None:
        """Test failed code verification."""
        code = "1234"
        hash_result, salt = security_manager.encrypt_code(code)

        assert not security_manager.verify_code("5678", hash_result, salt)

    def test_verify_code_empty_inputs(self, security_manager: SecurityManager) -> None:
        """Test verification with empty inputs."""
        assert not security_manager.verify_code("", "hash", "salt")
        assert not security_manager.verify_code("code", "", "salt")
        assert not security_manager.verify_code("code", "hash", "")

    def test_verify_code_none_inputs(self, security_manager: SecurityManager) -> None:
        """Test verification with None inputs."""
        assert not security_manager.verify_code(None, "hash", "salt")
        assert not security_manager.verify_code("code", None, "salt")
        assert not security_manager.verify_code("code", "hash", None)

    def test_secure_compare(self, security_manager: SecurityManager) -> None:
        """Test secure string comparison."""
        assert security_manager.secure_compare("test", "test")
        assert not security_manager.secure_compare("test", "different")
        assert not security_manager.secure_compare("", "test")
        assert security_manager.secure_compare("", "")

    def test_encryption_roundtrip(self, security_manager: SecurityManager) -> None:
        """Test complete encryption and verification cycle."""
        codes = ["1234", "5678", "9999", "0000"]

        for code in codes:
            hash_result, salt = security_manager.encrypt_code(code)
            assert security_manager.verify_code(code, hash_result, salt)
            assert not security_manager.verify_code("wrong", hash_result, salt)

    def test_unique_encryption(self, security_manager: SecurityManager) -> None:
        """Test that same code produces different hashes with different salts."""
        code = "1234"
        hash1, salt1 = security_manager.encrypt_code(code)
        hash2, salt2 = security_manager.encrypt_code(code)

        assert salt1 != salt2  # Salts should be unique
        assert hash1 != hash2  # Hashes should be different
        assert security_manager.verify_code(code, hash1, salt1)
        assert security_manager.verify_code(code, hash2, salt2)
