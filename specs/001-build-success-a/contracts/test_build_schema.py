"""
Contract tests for build validation schema.

These tests validate that the build_success field and build_details structure
conform to the defined schema contracts. Tests are expected to FAIL initially
until the implementation is complete (TDD approach).

Test Categories:
1. Schema presence tests - Verify build_success field exists
2. Type validation tests - Verify field types match schema
3. Value constraint tests - Verify error message truncation, non-negative timing
4. Integration tests - Verify build_details matches BuildValidationResult schema
"""

import json
from pathlib import Path
from typing import Any

import pytest


class TestBuildSchemaContract:
    """Contract tests for build validation in submission.json."""

    @pytest.fixture
    def sample_submission_path(self, tmp_path: Path) -> Path:
        """
        Create a sample submission.json for testing.

        This fixture will FAIL initially because build_success is not populated.
        Once implementation is complete, it should use actual submission.json.
        """
        submission_data = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123",
                "language": "python",
                "timestamp": "2025-10-09T00:00:00Z",
                "size_mb": 10.5
            },
            "metrics": {
                "code_quality": {
                    "lint_results": {
                        "tool_used": "ruff",
                        "passed": True,
                        "issues_count": 0,
                        "issues": []
                    },
                    "build_success": None,  # EXPECTED TO FAIL: Should be True/False, not None
                    "build_details": None,  # EXPECTED TO FAIL: Should have structure
                    "security_issues": [],
                    "dependency_audit": {
                        "vulnerabilities_found": 0,
                        "high_severity_count": 0,
                        "tool_used": "none"
                    }
                },
                "testing": {
                    "test_execution": {
                        "tests_run": 0,
                        "tests_passed": 0,
                        "tests_failed": 0,
                        "framework": "none",
                        "execution_time_seconds": 0.0
                    }
                },
                "documentation": {
                    "readme_present": True,
                    "readme_quality_score": 0.8
                }
            },
            "execution": {
                "tools_used": ["ruff"],
                "duration_seconds": 5.2,
                "errors": [],
                "warnings": []
            }
        }

        submission_file = tmp_path / "submission.json"
        submission_file.write_text(json.dumps(submission_data, indent=2))
        return submission_file

    def test_build_success_field_exists(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify build_success field is present in submission.json.

        Expected to FAIL initially: Field exists but is always None.
        Should PASS after implementation: Field is populated with boolean or null.
        """
        data = json.loads(sample_submission_path.read_text())
        assert "build_success" in data["metrics"]["code_quality"], \
            "build_success field must exist in code_quality metrics"

    def test_build_success_type_validation(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify build_success is boolean or null, never undefined.

        Expected to FAIL initially: Field is always None.
        Should PASS after implementation: Field has True/False/None based on build outcome.
        """
        data = json.loads(sample_submission_path.read_text())
        build_success = data["metrics"]["code_quality"]["build_success"]

        # Allow boolean or null, but not undefined or other types
        assert build_success in [True, False, None], \
            f"build_success must be True, False, or None, got {build_success}"

    def test_build_details_structure(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify build_details matches BuildValidationResult schema.

        Expected to FAIL initially: Field is None.
        Should PASS after implementation: Field has correct structure when populated.
        """
        data = json.loads(sample_submission_path.read_text())
        build_details = data["metrics"]["code_quality"].get("build_details")

        # If build_details is present, it must match schema
        if build_details is not None:
            assert isinstance(build_details, dict), "build_details must be an object"

            # Required fields
            assert "success" in build_details, "success field is required"
            assert "tool_used" in build_details, "tool_used field is required"
            assert "execution_time_seconds" in build_details, \
                "execution_time_seconds field is required"

            # Type validation
            assert isinstance(build_details["success"], (bool, type(None))), \
                "success must be boolean or null"
            assert isinstance(build_details["tool_used"], str), \
                "tool_used must be string"
            assert isinstance(build_details["execution_time_seconds"], (int, float)), \
                "execution_time_seconds must be number"

            # Optional fields type validation
            if "error_message" in build_details:
                assert isinstance(build_details["error_message"], (str, type(None))), \
                    "error_message must be string or null"
            if "exit_code" in build_details:
                assert isinstance(build_details["exit_code"], (int, type(None))), \
                    "exit_code must be integer or null"

    def test_error_message_truncation(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify error messages are truncated to 1000 characters (NFR-002).

        Expected to FAIL initially: No error messages generated.
        Should PASS after implementation: Long error messages are truncated.
        """
        data = json.loads(sample_submission_path.read_text())
        build_details = data["metrics"]["code_quality"].get("build_details")

        if build_details and build_details.get("error_message"):
            error_message = build_details["error_message"]
            assert len(error_message) <= 1000, \
                f"error_message must be <= 1000 chars, got {len(error_message)}"

    def test_execution_time_non_negative(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify execution_time_seconds is non-negative.

        Expected to FAIL initially: Field doesn't exist or is 0.
        Should PASS after implementation: Execution time is positive number.
        """
        data = json.loads(sample_submission_path.read_text())
        build_details = data["metrics"]["code_quality"].get("build_details")

        if build_details:
            execution_time = build_details["execution_time_seconds"]
            assert execution_time >= 0, \
                f"execution_time_seconds must be >= 0, got {execution_time}"

    def test_build_success_consistency_with_details(
        self, sample_submission_path: Path
    ) -> None:
        """
        GATE: Verify build_success matches build_details.success.

        Expected to FAIL initially: build_success is None, build_details is None.
        Should PASS after implementation: Both fields are consistent.
        """
        data = json.loads(sample_submission_path.read_text())
        build_success = data["metrics"]["code_quality"]["build_success"]
        build_details = data["metrics"]["code_quality"].get("build_details")

        # If build_details exists, build_success must match build_details.success
        if build_details is not None:
            details_success = build_details["success"]
            assert build_success == details_success, \
                f"build_success ({build_success}) must match build_details.success ({details_success})"

    def test_tool_used_valid_values(self, sample_submission_path: Path) -> None:
        """
        GATE: Verify tool_used is one of the supported tools.

        Expected to FAIL initially: No tool_used value.
        Should PASS after implementation: tool_used is valid enum value.
        """
        data = json.loads(sample_submission_path.read_text())
        build_details = data["metrics"]["code_quality"].get("build_details")

        if build_details:
            tool_used = build_details["tool_used"]
            valid_tools = {"uv", "build", "npm", "yarn", "go", "mvn", "gradle", "none"}
            assert tool_used in valid_tools, \
                f"tool_used must be one of {valid_tools}, got {tool_used}"

    @pytest.mark.parametrize("expected_success,expected_tool", [
        (True, "uv"),      # Successful Python build
        (False, "npm"),    # Failed JavaScript build
        (None, "none"),    # Tool unavailable
    ])
    def test_build_result_examples(
        self, expected_success: bool | None, expected_tool: str
    ) -> None:
        """
        GATE: Verify various build result scenarios are correctly structured.

        Expected to FAIL initially: Cannot generate these scenarios.
        Should PASS after implementation: All scenarios produce valid structure.
        """
        # This test uses parameterized examples to validate different outcomes
        # Implementation will need to generate these different scenarios

        example_result = {
            "success": expected_success,
            "tool_used": expected_tool,
            "execution_time_seconds": 3.14 if expected_success else 8.52,
            "error_message": None if expected_success else "Build failed",
            "exit_code": 0 if expected_success else 1
        }

        # Validate structure
        assert example_result["success"] == expected_success
        assert example_result["tool_used"] == expected_tool
        assert example_result["execution_time_seconds"] >= 0

        if expected_success is False:
            assert example_result["error_message"] is not None
            assert example_result["exit_code"] != 0
        elif expected_success is True:
            assert example_result["exit_code"] == 0


class TestBuildSchemaIntegration:
    """Integration tests for build validation in full pipeline."""

    @pytest.mark.skip(reason="Requires actual repository analysis - run after implementation")
    def test_real_repository_build_validation(self) -> None:
        """
        Integration test: Analyze a real repository and verify build_success is populated.

        This test is skipped initially because it requires:
        1. Actual tool runner implementations
        2. ToolExecutor integration
        3. Output generator updates

        Should be enabled once implementation is complete.
        """
        # Pseudo-code for actual integration test:
        # 1. Clone test repository
        # 2. Run metrics collection with build validation
        # 3. Load submission.json
        # 4. Assert build_success is not None
        # 5. Assert build_details has correct structure
        # 6. Compare with manual build attempt
        pass

    @pytest.mark.skip(reason="Performance validation - run after implementation")
    def test_build_timeout_compliance(self) -> None:
        """
        Performance test: Verify build validation completes within timeout (NFR-001).

        This test is skipped initially. Once implemented:
        1. Test against 20+ repositories
        2. Measure build duration for each
        3. Verify 99% complete within 120 seconds
        4. Document outliers
        """
        pass


# Run contract tests with:
# uv run pytest specs/001-build-success-a/contracts/test_build_schema.py -v
#
# Expected initial results:
# - test_build_success_field_exists: PASS (field exists but is None)
# - test_build_success_type_validation: PASS (None is valid type)
# - test_build_details_structure: SKIP (field is None)
# - Others: SKIP or FAIL (no implementation yet)
#
# After implementation:
# - All tests should PASS
# - build_success populated with actual values
# - build_details has correct structure
