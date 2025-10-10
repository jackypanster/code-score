"""Unit tests for MetricsCollection and CodeQualityMetrics models."""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.metrics.models.build_validation import BuildValidationResult
from src.metrics.models.metrics_collection import (
    CodeQualityMetrics,
    DocumentationMetrics,
    ExecutionMetadata,
    LintIssue,
    MetricsCollection,
    SecurityIssue,
    TestingMetrics,
)


class TestCodeQualityMetricsExtension:
    """Test CodeQualityMetrics extension with build_details field (T007)."""

    def test_backward_compatibility_deserialize_without_build_details(self) -> None:
        """Test backward compatibility: deserialize old JSON without build_details."""
        # Old JSON format from before build_details was added
        old_json = {
            "lint_results": {"tool_used": "ruff", "issues_count": 0},
            "build_success": None,
            "security_issues": [],
            "dependency_audit": {"vulnerabilities": 0}
        }

        # Should successfully deserialize with build_details defaulting to None
        metrics = CodeQualityMetrics(**old_json)

        assert metrics.lint_results == {"tool_used": "ruff", "issues_count": 0}
        assert metrics.build_success is None
        assert metrics.build_details is None  # Should default to None
        assert metrics.security_issues == []

    def test_backward_compatibility_deserialize_old_json_string(self) -> None:
        """Test backward compatibility: deserialize old JSON string without build_details."""
        # Old JSON string without build_details field
        old_json_str = '{"lint_results": null, "build_success": false, "security_issues": [], "dependency_audit": null}'

        metrics = CodeQualityMetrics.model_validate_json(old_json_str)

        assert metrics.build_success is False
        assert metrics.build_details is None

    def test_forward_compatibility_serialize_with_build_details(self) -> None:
        """Test forward compatibility: serialize with build_details."""
        build_details = BuildValidationResult(
            success=True,
            tool_used="uv",
            execution_time_seconds=3.5,
            error_message=None,
            exit_code=0
        )

        metrics = CodeQualityMetrics(
            lint_results={"tool_used": "ruff", "passed": True},
            build_success=True,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        # Serialize to dict
        metrics_dict = metrics.model_dump()

        assert metrics_dict["build_success"] is True
        assert metrics_dict["build_details"] is not None
        assert metrics_dict["build_details"]["success"] is True
        assert metrics_dict["build_details"]["tool_used"] == "uv"

    def test_forward_compatibility_serialize_to_json_string(self) -> None:
        """Test forward compatibility: serialize to JSON string with build_details."""
        build_details = BuildValidationResult(
            success=False,
            tool_used="npm",
            execution_time_seconds=8.2,
            error_message="Build failed: module not found",
            exit_code=1
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=False,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        # Serialize to JSON string
        json_str = metrics.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["build_success"] is False
        assert "build_details" in parsed
        assert parsed["build_details"]["tool_used"] == "npm"
        assert parsed["build_details"]["error_message"] == "Build failed: module not found"

    def test_build_success_build_details_consistency_both_present(self) -> None:
        """Test consistency: both build_success and build_details are present."""
        build_details = BuildValidationResult(
            success=True,
            tool_used="mvn",
            execution_time_seconds=12.5,
            error_message=None,
            exit_code=0
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=True,  # Should match build_details.success
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        # Values should be consistent
        assert metrics.build_success is True
        assert metrics.build_details.success is True
        assert metrics.build_success == metrics.build_details.success

    def test_build_success_build_details_consistency_failure_case(self) -> None:
        """Test consistency: build_success=False matches build_details.success=False."""
        build_details = BuildValidationResult(
            success=False,
            tool_used="go",
            execution_time_seconds=5.1,
            error_message="Compilation error",
            exit_code=2
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=False,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        assert metrics.build_success is False
        assert metrics.build_details.success is False
        assert metrics.build_success == metrics.build_details.success

    def test_build_success_build_details_consistency_none_case(self) -> None:
        """Test consistency: build_success=None when tool unavailable."""
        build_details = BuildValidationResult(
            success=None,  # Tool unavailable
            tool_used="none",
            execution_time_seconds=0.0,
            error_message="No build configuration found",
            exit_code=None
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=None,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        assert metrics.build_success is None
        assert metrics.build_details.success is None

    def test_field_defaults_both_none(self) -> None:
        """Test that build_success and build_details default to None."""
        # Create CodeQualityMetrics without specifying build fields
        metrics = CodeQualityMetrics(
            lint_results=None,
            security_issues=[],
            dependency_audit=None
        )

        # Both should default to None
        assert metrics.build_success is None
        assert metrics.build_details is None

    def test_field_defaults_only_build_success_set(self) -> None:
        """Test setting only build_success without build_details."""
        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=True,  # Set only build_success
            # build_details not specified
            security_issues=[],
            dependency_audit=None
        )

        assert metrics.build_success is True
        assert metrics.build_details is None  # Should remain None

    def test_field_defaults_only_build_details_set(self) -> None:
        """Test setting only build_details without build_success."""
        build_details = BuildValidationResult(
            success=True,
            tool_used="yarn",
            execution_time_seconds=4.0,
            error_message=None,
            exit_code=0
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            # build_success not specified
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        assert metrics.build_success is None  # Should default to None
        assert metrics.build_details is not None
        assert metrics.build_details.success is True

    def test_round_trip_serialization_with_build_details(self) -> None:
        """Test round-trip serialization: dict -> model -> dict preserves data."""
        original_data = {
            "lint_results": {"tool": "eslint", "issues": 5},
            "build_success": True,
            "build_details": {
                "success": True,
                "tool_used": "gradle",
                "execution_time_seconds": 15.3,
                "error_message": None,
                "exit_code": 0
            },
            "security_issues": [],
            "dependency_audit": {"vulns": 0}
        }

        # Dict -> Model
        metrics = CodeQualityMetrics(**original_data)

        # Model -> Dict
        result_data = metrics.model_dump()

        # Should preserve all data
        assert result_data["build_success"] == original_data["build_success"]
        assert result_data["build_details"]["tool_used"] == original_data["build_details"]["tool_used"]
        assert result_data["build_details"]["execution_time_seconds"] == original_data["build_details"]["execution_time_seconds"]

    def test_nested_build_details_validation(self) -> None:
        """Test that build_details respects BuildValidationResult validators."""
        # Attempt to create with negative execution time (should fail)
        with pytest.raises(ValidationError) as exc_info:
            CodeQualityMetrics(
                lint_results=None,
                build_success=False,
                build_details=BuildValidationResult(
                    success=False,
                    tool_used="npm",
                    execution_time_seconds=-1.0,  # Invalid: negative time
                    error_message="Error",
                    exit_code=1
                ),
                security_issues=[],
                dependency_audit=None
            )

        assert "execution_time_seconds" in str(exc_info.value).lower()

    def test_nested_build_details_error_truncation(self) -> None:
        """Test that build_details error messages are truncated per NFR-002."""
        long_error = "ERROR: " + "x" * 2000

        build_details = BuildValidationResult(
            success=False,
            tool_used="mvn",
            execution_time_seconds=10.0,
            error_message=long_error,
            exit_code=1
        )

        metrics = CodeQualityMetrics(
            lint_results=None,
            build_success=False,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        # Error message should be truncated
        assert len(metrics.build_details.error_message) <= 1000
        assert metrics.build_details.error_message.endswith("...")


class TestMetricsCollectionWithBuildFields:
    """Test MetricsCollection integration with build fields."""

    def test_metrics_collection_includes_build_fields(self) -> None:
        """Test that MetricsCollection properly includes build fields."""
        build_details = BuildValidationResult(
            success=True,
            tool_used="uv",
            execution_time_seconds=3.0,
            error_message=None,
            exit_code=0
        )

        code_quality = CodeQualityMetrics(
            lint_results={"passed": True},
            build_success=True,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        metrics_collection = MetricsCollection(
            repository_id="test-repo",
            code_quality=code_quality,
            testing_metrics=TestingMetrics(),
            documentation_metrics=DocumentationMetrics(),
            execution_metadata=ExecutionMetadata()
        )

        assert metrics_collection.code_quality.build_success is True
        assert metrics_collection.code_quality.build_details is not None
        assert metrics_collection.code_quality.build_details.tool_used == "uv"

    def test_metrics_collection_serialization_with_build_fields(self) -> None:
        """Test MetricsCollection serialization includes build fields."""
        build_details = BuildValidationResult(
            success=False,
            tool_used="npm",
            execution_time_seconds=8.0,
            error_message="Build error",
            exit_code=1
        )

        code_quality = CodeQualityMetrics(
            lint_results=None,
            build_success=False,
            build_details=build_details,
            security_issues=[],
            dependency_audit=None
        )

        metrics_collection = MetricsCollection(
            repository_id="test-repo",
            code_quality=code_quality
        )

        # Serialize to JSON
        json_str = metrics_collection.model_dump_json()
        parsed = json.loads(json_str)

        # Verify build fields are present
        assert "build_success" in parsed["code_quality"]
        assert parsed["code_quality"]["build_success"] is False
        assert "build_details" in parsed["code_quality"]
        assert parsed["code_quality"]["build_details"]["tool_used"] == "npm"

    def test_metrics_collection_backward_compatibility(self) -> None:
        """Test MetricsCollection can deserialize old data without build_details."""
        old_data = {
            "repository_id": "old-repo",
            "collection_timestamp": datetime.utcnow().isoformat(),
            "code_quality": {
                "lint_results": None,
                "build_success": None,  # Old format without build_details
                "security_issues": [],
                "dependency_audit": None
            },
            "testing_metrics": {
                "test_execution": None,
                "coverage_report": None
            },
            "documentation_metrics": {
                "readme_present": False,
                "readme_quality_score": 0.0,
                "api_documentation": False,
                "setup_instructions": False,
                "usage_examples": False
            },
            "execution_metadata": {
                "tools_used": [],
                "errors": [],
                "warnings": [],
                "duration_seconds": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Should deserialize successfully
        metrics = MetricsCollection(**old_data)

        assert metrics.code_quality.build_success is None
        assert metrics.code_quality.build_details is None
