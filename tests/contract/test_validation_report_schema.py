"""Contract tests for ValidationReport dataclass against JSON schema.

This module validates that ValidationReport instances conform to the
validation_report_schema.json contract. Uses real dataclass instances
without mocks.

Test Strategy:
- Create real ValidationReport instances with various error scenarios
- Convert instances to dictionaries for schema validation
- Use jsonschema library for validation against schema file
- Test both passed and failed reports with categorized errors
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate, RefResolver, Draft7Validator, FormatChecker

# NOTE: These imports will FAIL initially - that's expected (TDD)
try:
    from src.metrics.models.validation_report import ValidationReport
    from src.metrics.models.validation_result import ValidationResult
    VALIDATION_REPORT_EXISTS = True
except ImportError:
    VALIDATION_REPORT_EXISTS = False


# Load schema files
SCHEMA_DIR = Path(__file__).parent / "schemas"
SCHEMA_PATH = SCHEMA_DIR / "validation_report_schema.json"
with open(SCHEMA_PATH) as f:
    VALIDATION_REPORT_SCHEMA = json.load(f)

# Load validation_result_schema for the RefResolver
VALIDATION_RESULT_SCHEMA_PATH = SCHEMA_DIR / "validation_result_schema.json"
with open(VALIDATION_RESULT_SCHEMA_PATH) as f:
    VALIDATION_RESULT_SCHEMA = json.load(f)

# Create a RefResolver to handle $ref in schemas
# This allows validation_report_schema to reference validation_result_schema
schema_store = {
    "validation_result_schema.json": VALIDATION_RESULT_SCHEMA
}
resolver = RefResolver.from_schema(VALIDATION_REPORT_SCHEMA, store=schema_store)


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_passed():
    """Test that a valid report with passed=True validates.

    Acceptance: Valid report with passed=True
    """
    # Create real ValidationReport for successful validation
    report = ValidationReport(
        passed=True,
        language="python",
        checked_tools=["ruff", "pytest", "pip-audit"],
        errors_by_category={},
        timestamp=datetime.utcnow()
    )

    # Convert to dict for schema validation
    report_dict = {
        "passed": report.passed,
        "language": report.language,
        "checked_tools": report.checked_tools,
        "errors_by_category": report.errors_by_category,
        "timestamp": report.timestamp.isoformat()
    }

    # Schema validation should pass
    validate(instance=report_dict, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_with_errors():
    """Test that a valid report with errors_by_category populated validates.

    Acceptance: Valid report with errors_by_category populated
    """
    # Create real ValidationResult for missing tool
    missing_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing",
        error_details="Tool not found in PATH"
    )

    # Create real ValidationReport with errors
    report = ValidationReport(
        passed=False,
        language="python",
        checked_tools=["ruff", "pytest", "pip-audit"],
        errors_by_category={
            "missing": [missing_result]
        },
        timestamp=datetime.utcnow()
    )

    # Convert ValidationResult to dict for schema validation
    missing_result_dict = {
        "tool_name": missing_result.tool_name,
        "found": missing_result.found,
        "path": missing_result.path,
        "version": missing_result.version,
        "version_ok": missing_result.version_ok,
        "permissions": missing_result.permissions,
        "error_category": missing_result.error_category,
        "error_details": missing_result.error_details
    }

    report_dict = {
        "passed": report.passed,
        "language": report.language,
        "checked_tools": report.checked_tools,
        "errors_by_category": {
            "missing": [missing_result_dict]
        },
        "timestamp": report.timestamp.isoformat()
    }

    # Schema validation should pass
    validate(instance=report_dict, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_multiple_error_types():
    """Test report with all 3 error categories (missing, outdated, permission).

    Acceptance: Report with all 3 error categories
    """
    # Create real ValidationResults for each error type
    missing_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing",
        error_details="Tool not found"
    )

    outdated_result = ValidationResult(
        tool_name="npm",
        found=True,
        path="/usr/bin/npm",
        version="7.5.0",
        version_ok=False,
        error_category="outdated",
        error_details="Current: 7.5.0, Minimum: 8.0.0"
    )

    permission_result = ValidationResult(
        tool_name="ruff",
        found=True,
        path="/usr/bin/ruff",
        permissions="-rw-r--r--",
        version_ok=False,
        error_category="permission",
        error_details="Tool not executable"
    )

    # Create report with all error types
    report = ValidationReport(
        passed=False,
        language="python",
        checked_tools=["ruff", "pytest", "npm"],
        errors_by_category={
            "missing": [missing_result],
            "outdated": [outdated_result],
            "permission": [permission_result]
        },
        timestamp=datetime.utcnow()
    )

    # Convert to dicts for schema validation
    report_dict = {
        "passed": report.passed,
        "language": report.language,
        "checked_tools": report.checked_tools,
        "errors_by_category": {
            "missing": [{
                "tool_name": missing_result.tool_name,
                "found": missing_result.found,
                "path": missing_result.path,
                "version": missing_result.version,
                "version_ok": missing_result.version_ok,
                "permissions": missing_result.permissions,
                "error_category": missing_result.error_category,
                "error_details": missing_result.error_details
            }],
            "outdated": [{
                "tool_name": outdated_result.tool_name,
                "found": outdated_result.found,
                "path": outdated_result.path,
                "version": outdated_result.version,
                "version_ok": outdated_result.version_ok,
                "permissions": outdated_result.permissions,
                "error_category": outdated_result.error_category,
                "error_details": outdated_result.error_details
            }],
            "permission": [{
                "tool_name": permission_result.tool_name,
                "found": permission_result.found,
                "path": permission_result.path,
                "version": permission_result.version,
                "version_ok": permission_result.version_ok,
                "permissions": permission_result.permissions,
                "error_category": permission_result.error_category,
                "error_details": permission_result.error_details
            }]
        },
        "timestamp": report.timestamp.isoformat()
    }

    # Schema validation should pass
    validate(instance=report_dict, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_invalid_timestamp():
    """Test that schema rejects invalid timestamp type (must be string).

    Acceptance: Schema rejects non-string timestamp

    Note: Format validation (date-time) is optional in JSON Schema and requires
    additional dependencies. This test verifies the type constraint instead.
    """
    invalid_report = {
        "passed": True,
        "language": "python",
        "checked_tools": ["ruff"],
        "errors_by_category": {},
        "timestamp": 1234567890  # Invalid: integer instead of string
    }

    # Schema validation should fail (wrong type)
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_report, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)

    # Check error mentions type
    assert "type" in str(exc_info.value).lower() or "integer" in str(exc_info.value).lower()


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_missing_required_fields():
    """Test that schema rejects missing required fields.

    Acceptance: Schema rejects missing fields
    """
    # Missing 'passed' field
    invalid_report_1 = {
        "language": "python",
        "checked_tools": ["ruff"],
        "errors_by_category": {},
        "timestamp": datetime.utcnow().isoformat()
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_report_1, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)

    assert "'passed' is a required property" in str(exc_info.value)

    # Missing 'language' field
    invalid_report_2 = {
        "passed": True,
        "checked_tools": ["ruff"],
        "errors_by_category": {},
        "timestamp": datetime.utcnow().isoformat()
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_report_2, schema=VALIDATION_REPORT_SCHEMA, resolver=resolver)

    assert "'language' is a required property" in str(exc_info.value)


# Additional validation tests for completeness

@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_format_error_message():
    """Test that format_error_message() generates correct Chinese message.

    This tests the business logic in ValidationReport.format_error_message()
    """
    # Report with passed=True
    passed_report = ValidationReport(
        passed=True,
        language="python",
        checked_tools=["ruff", "pytest"],
        errors_by_category={},
        timestamp=datetime.utcnow()
    )
    message = passed_report.format_error_message()
    assert "工具链验证通过" in message
    assert "python" in message
    assert "2个" in message

    # Report with errors
    missing_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing",
        error_details="缺少工具 pytest。请在评分主机安装后重试（参考 https://docs.pytest.org）"
    )

    failed_report = ValidationReport(
        passed=False,
        language="python",
        checked_tools=["pytest"],
        errors_by_category={"missing": [missing_result]},
        timestamp=datetime.utcnow()
    )
    message = failed_report.format_error_message()
    assert "工具链验证失败" in message
    assert "【缺少工具】" in message
    assert "pytest" in message


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_get_failed_tools():
    """Test get_failed_tools() method."""
    missing_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing"
    )

    outdated_result = ValidationResult(
        tool_name="npm",
        found=True,
        version_ok=False,
        error_category="outdated"
    )

    report = ValidationReport(
        passed=False,
        language="python",
        checked_tools=["pytest", "npm"],
        errors_by_category={
            "missing": [missing_result],
            "outdated": [outdated_result]
        },
        timestamp=datetime.utcnow()
    )

    failed_tools = report.get_failed_tools()
    assert "pytest" in failed_tools
    assert "npm" in failed_tools
    assert len(failed_tools) == 2


@pytest.mark.skipif(not VALIDATION_REPORT_EXISTS, reason="ValidationReport not implemented yet (TDD)")
def test_validation_report_get_error_count():
    """Test get_error_count() method."""
    missing_result = ValidationResult(
        tool_name="pytest",
        found=False,
        error_category="missing"
    )

    outdated_result = ValidationResult(
        tool_name="npm",
        found=True,
        version_ok=False,
        error_category="outdated"
    )

    report = ValidationReport(
        passed=False,
        language="python",
        checked_tools=["pytest", "npm"],
        errors_by_category={
            "missing": [missing_result],
            "outdated": [outdated_result]
        },
        timestamp=datetime.utcnow()
    )

    assert report.get_error_count() == 2
