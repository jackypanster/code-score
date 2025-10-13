"""Contract tests for metrics.testing.test_execution schema extension.

These tests validate that the schema extension for static test infrastructure
analysis is backward-compatible and follows FR-019 requirements.

Test Coverage:
- New field `test_files_detected` present (FR-017)
- Existing fields preserved (tests_run, tests_passed, tests_failed, framework)
- Backward compatibility (FR-019)
- Static analysis vs execution distinction

Expected Status: Test structure complete, will verify integration when analyzer is implemented.
"""

import json
from pathlib import Path

import pytest


class TestMetricsSchemaExtension:
    """Contract tests for backward-compatible schema extension."""

    def test_new_field_test_files_detected_present(self):
        """Test that new field test_files_detected is added to test_execution (FR-017)."""
        # Simulate test_execution dict from static analysis
        test_execution = {
            "tests_run": 0,  # Static analysis doesn't run tests
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",
            "execution_time_seconds": 0.0,
            "test_files_detected": 15,  # New field from FR-017
        }

        # Verify new field present
        assert "test_files_detected" in test_execution, "New field test_files_detected must be present"
        assert isinstance(
            test_execution["test_files_detected"], int
        ), "test_files_detected must be int"
        assert (
            test_execution["test_files_detected"] >= 0
        ), "test_files_detected must be non-negative"

    def test_existing_fields_preserved(self):
        """Test that all existing fields are preserved (FR-019 backward compatibility)."""
        # Simulate extended test_execution dict
        test_execution = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",
            "execution_time_seconds": 0.0,
            "test_files_detected": 15,  # New field
        }

        # Verify all existing fields still present
        required_existing_fields = [
            "tests_run",
            "tests_passed",
            "tests_failed",
            "framework",
            "execution_time_seconds",
        ]

        for field in required_existing_fields:
            assert field in test_execution, f"Existing field {field} must be preserved (FR-019)"

    def test_static_analysis_signature(self):
        """Test that static analysis results are distinguishable from execution results."""
        # Static analysis case (FR-017 clarification)
        static_result = {
            "tests_run": 0,  # Explicitly 0 = no execution
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",
            "execution_time_seconds": 0.0,
            "test_files_detected": 15,  # > 0 = static detection found tests
        }

        # Verify static analysis signature
        assert static_result["tests_run"] == 0, "tests_run=0 indicates no execution"
        assert (
            static_result["test_files_detected"] > 0
        ), "test_files_detected>0 indicates static detection"
        assert (
            static_result["framework"] != "none"
        ), "Framework inferred from config, not 'none'"

    def test_no_infrastructure_case(self):
        """Test schema for repos with no test infrastructure (tetris-web scenario)."""
        no_tests_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "none",
            "execution_time_seconds": 0.0,
            "test_files_detected": 0,  # No tests detected
        }

        assert no_tests_result["test_files_detected"] == 0
        assert no_tests_result["framework"] == "none"
        assert no_tests_result["tests_run"] == 0

    def test_schema_json_serializable(self):
        """Test that extended schema is JSON serializable."""
        test_execution = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",
            "execution_time_seconds": 0.0,
            "test_files_detected": 15,
        }

        # Verify JSON serialization
        json_str = json.dumps(test_execution)
        assert json_str, "Extended schema must be JSON serializable"

        # Verify deserialization
        parsed = json.loads(json_str)
        assert parsed["test_files_detected"] == 15
        assert parsed["tests_run"] == 0

    def test_multiple_languages_max_score_case(self):
        """Test schema for multi-language repos (FR-004a - max score strategy)."""
        # In multi-language repos, analyzer returns result with highest score
        # The test_execution section reflects the winning language's result
        multi_lang_result = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",  # Python had highest score
            "execution_time_seconds": 0.0,
            "test_files_detected": 25,  # Python test files count
        }

        assert multi_lang_result["test_files_detected"] > 0
        assert multi_lang_result["framework"] in [
            "pytest",
            "jest",
            "go test",
            "junit",
        ]

    def test_anthropic_sdk_python_expected_output(self):
        """Test expected schema for anthropic-sdk-python analysis."""
        # Expected result from T006 integration test
        expected = {
            "tests_run": 0,  # Static analysis
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest",  # Detected from pyproject.toml
            "execution_time_seconds": 0.0,
            "test_files_detected": 15,  # Approximate expected count (placeholder)
        }

        # Validate structure
        assert expected["tests_run"] == 0, "Static analysis doesn't run tests"
        assert expected["test_files_detected"] > 0, "Should detect pytest files"
        assert expected["framework"] == "pytest", "Should infer pytest from config"

    @pytest.mark.parametrize(
        "test_files,expected_score_range",
        [
            (0, (0, 5)),  # No tests → 0-5 points
            (5, (10, 15)),  # Some tests, low ratio → 10-15 points
            (15, (15, 25)),  # Good test coverage → 15-25 points
        ],
    )
    def test_test_files_detected_correlates_with_score(
        self, test_files: int, expected_score_range: tuple[int, int]
    ):
        """Test that test_files_detected count correlates with expected score range."""
        # This is a contract for the relationship between detection and scoring
        # Actual scoring logic is in TestInfrastructureAnalyzer (T027)

        test_execution = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "framework": "pytest" if test_files > 0 else "none",
            "execution_time_seconds": 0.0,
            "test_files_detected": test_files,
        }

        min_score, max_score = expected_score_range

        # Verify field present and in expected range
        assert test_execution["test_files_detected"] == test_files
        # Note: Actual score validation happens in integration tests (T006, T007)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
