"""Contract tests for ToolRequirement dataclass against JSON schema.

This module validates that ToolRequirement instances conform to the
tool_requirement_schema.json contract. Uses real dataclass instances
without mocks.

Test Strategy:
- Create real ToolRequirement instances with various field combinations
- Convert instances to dictionaries for schema validation
- Use jsonschema library for validation against schema file
- Test both valid and invalid scenarios per acceptance criteria
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

# NOTE: This import will FAIL initially - that's expected (TDD)
# The ToolRequirement class doesn't exist yet
try:
    from src.metrics.models.tool_requirement import ToolRequirement
    TOOL_REQUIREMENT_EXISTS = True
except ImportError:
    TOOL_REQUIREMENT_EXISTS = False


# Load schema file
SCHEMA_PATH = Path(__file__).parent / "schemas" / "tool_requirement_schema.json"
with open(SCHEMA_PATH) as f:
    TOOL_REQUIREMENT_SCHEMA = json.load(f)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_valid_python_tool():
    """Test that a valid Python tool (ruff) passes schema validation.

    Acceptance: Valid Python tool passes schema
    """
    # Create real ToolRequirement instance (no mocks)
    tool = ToolRequirement(
        name="ruff",
        language="python",
        category="lint",
        doc_url="https://docs.astral.sh/ruff",
        min_version="0.1.0",
        version_command="--version"
    )

    # Convert to dict for schema validation
    tool_dict = {
        "name": tool.name,
        "language": tool.language,
        "category": tool.category,
        "doc_url": tool.doc_url,
        "min_version": tool.min_version,
        "version_command": tool.version_command
    }

    # Schema validation should pass
    validate(instance=tool_dict, schema=TOOL_REQUIREMENT_SCHEMA)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_valid_global_tool():
    """Test that a valid global tool (git) passes schema validation.

    Acceptance: Valid global tool passes schema
    """
    tool = ToolRequirement(
        name="git",
        language="global",
        category="build",
        doc_url="https://git-scm.com/docs",
        min_version=None,  # No version requirement
        version_command="--version"
    )

    tool_dict = {
        "name": tool.name,
        "language": tool.language,
        "category": tool.category,
        "doc_url": tool.doc_url,
        "min_version": tool.min_version,
        "version_command": tool.version_command
    }

    # Schema validation should pass
    validate(instance=tool_dict, schema=TOOL_REQUIREMENT_SCHEMA)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_missing_name_invalid():
    """Test that schema rejects missing 'name' field.

    Acceptance: Schema rejects missing 'name' field
    """
    # Create dict directly (can't create ToolRequirement with missing required field)
    invalid_tool = {
        "language": "python",
        "category": "lint",
        "doc_url": "https://docs.astral.sh/ruff"
    }

    # Schema validation should fail
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_tool, schema=TOOL_REQUIREMENT_SCHEMA)

    assert "'name' is a required property" in str(exc_info.value)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_invalid_language():
    """Test that schema rejects language not in enum.

    Acceptance: Schema rejects language not in enum
    """
    # Create dict with invalid language (dataclass __post_init__ would reject this)
    invalid_tool = {
        "name": "cobol-lint",
        "language": "cobol",  # Not in enum: ["python", "javascript", "typescript", "java", "go", "global"]
        "category": "lint",
        "doc_url": "https://example.com/cobol"
    }

    # Schema validation should fail
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_tool, schema=TOOL_REQUIREMENT_SCHEMA)

    assert "'cobol' is not one of" in str(exc_info.value)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_invalid_category():
    """Test that schema rejects category not in enum.

    Acceptance: Schema rejects category not in enum
    """
    invalid_tool = {
        "name": "formatter",
        "language": "python",
        "category": "format",  # Not in enum: ["lint", "test", "security", "build"]
        "doc_url": "https://example.com/formatter"
    }

    # Schema validation should fail
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_tool, schema=TOOL_REQUIREMENT_SCHEMA)

    assert "'format' is not one of" in str(exc_info.value)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_invalid_doc_url():
    """Test that schema rejects non-HTTP/HTTPS URL.

    Acceptance: Schema rejects non-HTTP URL
    """
    invalid_tool = {
        "name": "ruff",
        "language": "python",
        "category": "lint",
        "doc_url": "ftp://example.com/docs"  # Not HTTP/HTTPS
    }

    # Schema validation should fail
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_tool, schema=TOOL_REQUIREMENT_SCHEMA)

    # The schema pattern requires ^https?:// (HTTP or HTTPS only)
    assert "does not match" in str(exc_info.value) or "pattern" in str(exc_info.value)


# Additional validation tests for completeness

@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_javascript_tool():
    """Test JavaScript tool with TypeScript language variant."""
    tool = ToolRequirement(
        name="eslint",
        language="javascript",
        category="lint",
        doc_url="https://eslint.org/docs",
        min_version="8.0.0"
    )

    tool_dict = {
        "name": tool.name,
        "language": tool.language,
        "category": tool.category,
        "doc_url": tool.doc_url,
        "min_version": tool.min_version,
        "version_command": tool.version_command
    }

    validate(instance=tool_dict, schema=TOOL_REQUIREMENT_SCHEMA)


@pytest.mark.skipif(not TOOL_REQUIREMENT_EXISTS, reason="ToolRequirement not implemented yet (TDD)")
def test_tool_requirement_security_tool():
    """Test security category tool."""
    tool = ToolRequirement(
        name="pip-audit",
        language="python",
        category="security",
        doc_url="https://pypi.org/project/pip-audit/",
        min_version="2.0.0"
    )

    tool_dict = {
        "name": tool.name,
        "language": tool.language,
        "category": tool.category,
        "doc_url": tool.doc_url,
        "min_version": tool.min_version,
        "version_command": tool.version_command
    }

    validate(instance=tool_dict, schema=TOOL_REQUIREMENT_SCHEMA)
