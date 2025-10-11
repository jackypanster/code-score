"""Contract tests for ValidationResult dataclass against JSON schema.

This module validates that ValidationResult instances conform to the
validation_result_schema.json contract. Uses real dataclass instances
without mocks.

Test Strategy:
- Create real ValidationResult instances for various scenarios
- Convert instances to dictionaries for schema validation
- Use jsonschema library for validation against schema file
- Test found/missing tools, version checks, permission errors
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

# NOTE: This import will FAIL initially - that's expected (TDD)
try:
    from src.metrics.models.validation_result import ValidationResult
    VALIDATION_RESULT_EXISTS = True
except ImportError:
    VALIDATION_RESULT_EXISTS = False


# Load schema file
SCHEMA_PATH = Path(__file__).parent / "schemas" / "validation_result_schema.json"
with open(SCHEMA_PATH) as f:
    VALIDATION_RESULT_SCHEMA = json.load(f)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_found_with_version():
    """Test that a valid result with found tool and version passes schema.

    Acceptance: Valid result with found tool passes
    """
    # Create real ValidationResult instance (successful validation)
    result = ValidationResult(
        tool_name="ruff",
        found=True,
        path="/usr/local/bin/ruff",
        version="0.1.8",
        version_ok=True,
        permissions=None,
        error_category=None,
        error_details=None
    )

    # Convert to dict for schema validation
    result_dict = {
        "tool_name": result.tool_name,
        "found": result.found,
        "path": result.path,
        "version": result.version,
        "version_ok": result.version_ok,
        "permissions": result.permissions,
        "error_category": result.error_category,
        "error_details": result.error_details
    }

    # Schema validation should pass
    validate(instance=result_dict, schema=VALIDATION_RESULT_SCHEMA)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_missing_tool():
    """Test that a valid result with found=False passes schema.

    Acceptance: Valid result with found=False passes
    """
    # Create real ValidationResult for missing tool
    result = ValidationResult(
        tool_name="pytest",
        found=False,
        path=None,
        version=None,
        version_ok=False,
        permissions=None,
        error_category="missing",
        error_details="Tool not found in PATH"
    )

    result_dict = {
        "tool_name": result.tool_name,
        "found": result.found,
        "path": result.path,
        "version": result.version,
        "version_ok": result.version_ok,
        "permissions": result.permissions,
        "error_category": result.error_category,
        "error_details": result.error_details
    }

    # Schema validation should pass
    validate(instance=result_dict, schema=VALIDATION_RESULT_SCHEMA)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_permission_error():
    """Test that a valid result with permissions field passes schema.

    Acceptance: Valid result with permissions field passes
    """
    # Create real ValidationResult for permission error
    result = ValidationResult(
        tool_name="ruff",
        found=True,
        path="/usr/bin/ruff",
        version=None,
        version_ok=False,
        permissions="-rw-r--r--",
        error_category="permission",
        error_details="Tool exists but is not executable"
    )

    result_dict = {
        "tool_name": result.tool_name,
        "found": result.found,
        "path": result.path,
        "version": result.version,
        "version_ok": result.version_ok,
        "permissions": result.permissions,
        "error_category": result.error_category,
        "error_details": result.error_details
    }

    # Schema validation should pass
    validate(instance=result_dict, schema=VALIDATION_RESULT_SCHEMA)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_invalid_error_category():
    """Test that schema rejects invalid error_category.

    Acceptance: Schema rejects invalid error_category
    """
    # Create dict with invalid error_category
    invalid_result = {
        "tool_name": "ruff",
        "found": False,
        "path": None,
        "version": None,
        "version_ok": False,
        "permissions": None,
        "error_category": "invalid_category",  # Not in enum: ["missing", "outdated", "permission", "other"]
        "error_details": "Some error"
    }

    # Schema validation should fail
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_result, schema=VALIDATION_RESULT_SCHEMA)

    assert "'invalid_category' is not one of" in str(exc_info.value) or "enum" in str(exc_info.value)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_missing_required_fields():
    """Test that schema rejects missing tool_name or found.

    Acceptance: Schema rejects missing required fields
    """
    # Missing 'tool_name' field
    invalid_result_1 = {
        "found": True,
        "path": "/usr/bin/ruff"
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_result_1, schema=VALIDATION_RESULT_SCHEMA)

    assert "'tool_name' is a required property" in str(exc_info.value)

    # Missing 'found' field
    invalid_result_2 = {
        "tool_name": "ruff",
        "path": "/usr/bin/ruff"
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_result_2, schema=VALIDATION_RESULT_SCHEMA)

    assert "'found' is a required property" in str(exc_info.value)


# Additional validation tests for completeness

@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_outdated_version():
    """Test outdated version scenario."""
    result = ValidationResult(
        tool_name="npm",
        found=True,
        path="/usr/local/bin/npm",
        version="7.5.0",
        version_ok=False,
        permissions=None,
        error_category="outdated",
        error_details="Current: 7.5.0, Minimum: 8.0.0"
    )

    result_dict = {
        "tool_name": result.tool_name,
        "found": result.found,
        "path": result.path,
        "version": result.version,
        "version_ok": result.version_ok,
        "permissions": result.permissions,
        "error_category": result.error_category,
        "error_details": result.error_details
    }

    validate(instance=result_dict, schema=VALIDATION_RESULT_SCHEMA)


@pytest.mark.skipif(not VALIDATION_RESULT_EXISTS, reason="ValidationResult not implemented yet (TDD)")
def test_validation_result_is_valid_method():
    """Test that is_valid() method works correctly.

    This tests the business logic in ValidationResult.is_valid()
    """
    # Valid tool
    valid_result = ValidationResult(
        tool_name="ruff",
        found=True,
        path="/usr/bin/ruff",
        version="0.1.8",
        version_ok=True
    )
    assert valid_result.is_valid() is True

    # Invalid tool (missing)
    invalid_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing"
    )
    assert invalid_result.is_valid() is False

    # Invalid tool (version problem)
    version_issue_result = ValidationResult(
        tool_name="npm",
        found=True,
        version_ok=False,
        error_category="outdated"
    )
    assert version_issue_result.is_valid() is False
