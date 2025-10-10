"""Unit tests for BuildValidationResult model."""

import pytest
from pydantic import ValidationError

from src.metrics.models.build_validation import BuildValidationResult


class TestBuildValidationResult:
    """Test BuildValidationResult Pydantic model."""

    def test_valid_instance_creation_success(self) -> None:
        """Test creating a valid BuildValidationResult instance with success=True."""
        result = BuildValidationResult(
            success=True,
            tool_used="uv",
            execution_time_seconds=3.14,
            error_message=None,
            exit_code=0
        )

        assert result.success is True
        assert result.tool_used == "uv"
        assert result.execution_time_seconds == 3.14
        assert result.error_message is None
        assert result.exit_code == 0

    def test_valid_instance_creation_failure(self) -> None:
        """Test creating a valid BuildValidationResult instance with success=False."""
        result = BuildValidationResult(
            success=False,
            tool_used="npm",
            execution_time_seconds=8.52,
            error_message="Build failed: Module not found",
            exit_code=1
        )

        assert result.success is False
        assert result.tool_used == "npm"
        assert result.execution_time_seconds == 8.52
        assert result.error_message == "Build failed: Module not found"
        assert result.exit_code == 1

    def test_valid_instance_creation_unavailable(self) -> None:
        """Test creating a valid BuildValidationResult instance with success=None."""
        result = BuildValidationResult(
            success=None,
            tool_used="none",
            execution_time_seconds=0.0,
            error_message="Maven not available in PATH",
            exit_code=None
        )

        assert result.success is None
        assert result.tool_used == "none"
        assert result.execution_time_seconds == 0.0
        assert result.error_message == "Maven not available in PATH"
        assert result.exit_code is None

    def test_error_message_truncation_exactly_1000_chars(self) -> None:
        """Test error message is NOT truncated when exactly 1000 characters."""
        long_error = "x" * 1000
        result = BuildValidationResult(
            success=False,
            tool_used="gradle",
            execution_time_seconds=10.0,
            error_message=long_error,
            exit_code=1
        )

        # Should not be truncated at exactly 1000 chars
        assert len(result.error_message) == 1000
        assert result.error_message == long_error

    def test_error_message_truncation_over_1000_chars(self) -> None:
        """Test error message is truncated to 997 chars + '...' when over 1000 chars."""
        long_error = "a" * 1001
        result = BuildValidationResult(
            success=False,
            tool_used="mvn",
            execution_time_seconds=15.0,
            error_message=long_error,
            exit_code=1
        )

        # Should be truncated to 997 + "..." = 1000 chars total
        assert len(result.error_message) == 1000
        assert result.error_message.endswith("...")
        assert result.error_message == ("a" * 997 + "...")

    def test_error_message_truncation_significantly_over_limit(self) -> None:
        """Test error message truncation with very long messages."""
        long_error = "Error: " + "x" * 5000 + " end"
        result = BuildValidationResult(
            success=False,
            tool_used="npm",
            execution_time_seconds=20.0,
            error_message=long_error,
            exit_code=1
        )

        assert len(result.error_message) == 1000
        assert result.error_message.startswith("Error: ")
        assert result.error_message.endswith("...")

    def test_negative_execution_time_rejection(self) -> None:
        """Test that negative execution time raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BuildValidationResult(
                success=False,
                tool_used="go",
                execution_time_seconds=-1.0,
                error_message="Negative time test",
                exit_code=1
            )

        # Verify the error message mentions execution time
        assert "execution_time_seconds" in str(exc_info.value).lower()

    def test_zero_execution_time_allowed(self) -> None:
        """Test that zero execution time is valid (tool unavailable case)."""
        result = BuildValidationResult(
            success=None,
            tool_used="none",
            execution_time_seconds=0.0,
            error_message="Tool not found",
            exit_code=None
        )

        assert result.execution_time_seconds == 0.0

    def test_serialization_to_dict(self) -> None:
        """Test serialization of BuildValidationResult to dictionary."""
        result = BuildValidationResult(
            success=True,
            tool_used="yarn",
            execution_time_seconds=5.5,
            error_message=None,
            exit_code=0
        )

        result_dict = result.model_dump()

        assert result_dict["success"] is True
        assert result_dict["tool_used"] == "yarn"
        assert result_dict["execution_time_seconds"] == 5.5
        assert result_dict["error_message"] is None
        assert result_dict["exit_code"] == 0

    def test_deserialization_from_dict(self) -> None:
        """Test deserialization of BuildValidationResult from dictionary."""
        data = {
            "success": False,
            "tool_used": "gradle",
            "execution_time_seconds": 12.3,
            "error_message": "Compilation error",
            "exit_code": 1
        }

        result = BuildValidationResult(**data)

        assert result.success is False
        assert result.tool_used == "gradle"
        assert result.execution_time_seconds == 12.3
        assert result.error_message == "Compilation error"
        assert result.exit_code == 1

    def test_json_serialization(self) -> None:
        """Test JSON serialization of BuildValidationResult."""
        result = BuildValidationResult(
            success=True,
            tool_used="uv",
            execution_time_seconds=2.5,
            error_message=None,
            exit_code=0
        )

        json_str = result.model_dump_json()

        assert '"success":true' in json_str
        assert '"tool_used":"uv"' in json_str
        assert '"execution_time_seconds":2.5' in json_str

    def test_json_deserialization(self) -> None:
        """Test JSON deserialization of BuildValidationResult."""
        json_str = '{"success":false,"tool_used":"npm","execution_time_seconds":10.0,"error_message":"Build failed","exit_code":1}'

        result = BuildValidationResult.model_validate_json(json_str)

        assert result.success is False
        assert result.tool_used == "npm"
        assert result.execution_time_seconds == 10.0
        assert result.error_message == "Build failed"
        assert result.exit_code == 1

    def test_validator_behavior_with_known_tools(self) -> None:
        """Test that known tool names are accepted."""
        known_tools = ["uv", "build", "npm", "yarn", "go", "mvn", "gradle", "none"]

        for tool in known_tools:
            result = BuildValidationResult(
                success=True,
                tool_used=tool,
                execution_time_seconds=1.0,
                error_message=None,
                exit_code=0
            )
            assert result.tool_used == tool

    def test_validator_behavior_with_unknown_tool(self) -> None:
        """Test that unknown tool names are allowed (for extensibility)."""
        # Unknown tool should be allowed without raising error
        result = BuildValidationResult(
            success=True,
            tool_used="future_build_tool",
            execution_time_seconds=1.0,
            error_message=None,
            exit_code=0
        )

        assert result.tool_used == "future_build_tool"

    def test_optional_fields_defaults(self) -> None:
        """Test that optional fields have correct defaults."""
        result = BuildValidationResult(
            success=None,
            tool_used="none",
            execution_time_seconds=0.0
        )

        # Optional fields should default to None
        assert result.error_message is None
        assert result.exit_code is None

    def test_all_field_combinations_success_true(self) -> None:
        """Test typical successful build field combination."""
        result = BuildValidationResult(
            success=True,
            tool_used="go",
            execution_time_seconds=4.2,
            error_message=None,  # Should be None for success
            exit_code=0
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.error_message is None

    def test_all_field_combinations_success_false(self) -> None:
        """Test typical failed build field combination."""
        result = BuildValidationResult(
            success=False,
            tool_used="mvn",
            execution_time_seconds=7.8,
            error_message="Compilation errors detected",
            exit_code=1
        )

        assert result.success is False
        assert result.exit_code == 1
        assert result.error_message is not None

    def test_all_field_combinations_success_none(self) -> None:
        """Test typical unavailable tool field combination."""
        result = BuildValidationResult(
            success=None,
            tool_used="none",
            execution_time_seconds=0.0,
            error_message="Tool not available",
            exit_code=None
        )

        assert result.success is None
        assert result.tool_used == "none"
        assert result.exit_code is None
