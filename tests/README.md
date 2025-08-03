# Keypad Manager Test Suite

This directory contains comprehensive unit tests for the Keypad Manager integration.

## Test Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py          # Pytest fixtures and configuration
├── test_security.py     # Security module tests
├── test_validation.py   # Validation module tests
├── test_storage.py      # Storage module tests
└── README.md           # This file
```

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install pytest pytest-asyncio
```

### Run All Tests
```bash
# Using the test script
./scripts/test

# Or directly with pytest
python -m pytest tests/ -v
```

### Run Specific Test Files
```bash
# Test only security module
python -m pytest tests/test_security.py -v

# Test only validation module
python -m pytest tests/test_validation.py -v

# Test only storage module
python -m pytest tests/test_storage.py -v
```

### Run Specific Test Classes
```bash
# Test only SecurityManager class
python -m pytest tests/test_security.py::TestSecurityManager -v

# Test only code validation
python -m pytest tests/test_validation.py::TestValidateCode -v
```

### Run Specific Test Methods
```bash
# Test specific method
python -m pytest tests/test_security.py::TestSecurityManager::test_encrypt_code -v
```

## Test Coverage

### Security Module (`test_security.py`)
- ✅ Salt generation and uniqueness
- ✅ Value hashing with PBKDF2
- ✅ Code encryption and verification
- ✅ Secure string comparison
- ✅ Edge cases (None, empty strings)
- ✅ Round-trip encryption/verification
- ✅ Unique encryption for same input

### Validation Module (`test_validation.py`)
- ✅ User name validation (length, format)
- ✅ Code validation (4-8 digits only)
- ✅ Tag validation (0-9999 range)
- ✅ Access method validation
- ✅ Code uniqueness checking
- ✅ Tag uniqueness checking
- ✅ Combined user validation
- ✅ Error message validation

### Storage Module (`test_storage.py`)
- ✅ Storage manager initialization
- ✅ Data loading (empty and populated)
- ✅ Data saving
- ✅ User creation (code only, tag only, both)
- ✅ User retrieval (by ID, code, tag)
- ✅ User updates (name, code, tag, last used)
- ✅ User removal
- ✅ Error handling for missing users

## Test Patterns

### Fixtures
- `mock_hass`: Mock Home Assistant instance
- `mock_config_entry`: Mock configuration entry
- `security_manager`: SecurityManager instance
- `storage_manager`: KeypadManagerStorage instance
- `sample_user`: Sample user for testing
- `sample_users`: Dictionary of sample users

### Async Testing
All async methods are tested using `@pytest.mark.asyncio` decorator.

### Mocking
- External dependencies are mocked using `unittest.mock`
- Validation functions are patched to avoid complex setup
- Security verification is mocked for testing

### Error Testing
- Invalid inputs are tested with `pytest.raises()`
- Error messages are validated for correctness
- Edge cases (None, empty strings) are covered

## Adding New Tests

### For New Modules
1. Create `test_<module_name>.py`
2. Import the module and its classes/functions
3. Create test classes following the naming convention `Test<ClassName>`
4. Add comprehensive test methods

### For New Methods
1. Test happy path (valid inputs)
2. Test error cases (invalid inputs)
3. Test edge cases (None, empty, boundary values)
4. Test async methods with `@pytest.mark.asyncio`

### Example Test Method
```python
def test_method_name(self, fixture_name):
    """Test description."""
    # Arrange
    input_data = "test"

    # Act
    result = method_under_test(input_data)

    # Assert
    assert result == expected_value
```

## Continuous Integration

Tests should be run:
- Before committing changes
- In CI/CD pipelines
- When adding new features
- When fixing bugs

## Test Quality Guidelines

1. **Descriptive Names**: Test methods should clearly describe what they test
2. **Single Responsibility**: Each test should test one specific behavior
3. **Independence**: Tests should not depend on each other
4. **Comprehensive**: Cover happy path, error cases, and edge cases
5. **Fast**: Tests should run quickly (< 1 second each)
6. **Reliable**: Tests should be deterministic and not flaky