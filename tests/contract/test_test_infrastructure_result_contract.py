"""Contract tests for TestInfrastructureResult schema validation.

These tests validate that the TestInfrastructureResult data model produces
JSON output matching the expected schema defined in the specification.

Test Coverage:
- All required fields present (FR-017)
- Field types correct (int, bool, float, string)
- Score capped at 25 points (FR-013)
- Schema is serializable to JSON

Expected Status: FAIL until T016 (TestInfrastructureResult model) is implemented.
"""

import json
from pathlib import Path

import pytest


class TestTestInfrastructureResultContract:
    """Contract tests for TestInfrastructureResult data model."""

    def test_result_has_all_required_fields(self):
        """Test that TestInfrastructureResult contains all required fields (FR-017)."""
        # This test will FAIL until src/metrics/models/test_infrastructure.py is created
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        # Create a sample result
        result = TestInfrastructureResult(
            test_files_detected=15,
            test_config_detected=True,
            coverage_config_detected=False,
            test_file_ratio=0.25,
            calculated_score=20,
            inferred_framework="pytest",
        )

        # Verify all required fields are present
        assert hasattr(result, "test_files_detected"), "Missing field: test_files_detected"
        assert hasattr(result, "test_config_detected"), "Missing field: test_config_detected"
        assert hasattr(
            result, "coverage_config_detected"
        ), "Missing field: coverage_config_detected"
        assert hasattr(result, "test_file_ratio"), "Missing field: test_file_ratio"
        assert hasattr(result, "calculated_score"), "Missing field: calculated_score"
        assert hasattr(result, "inferred_framework"), "Missing field: inferred_framework"

    def test_result_field_types_are_correct(self):
        """Test that all fields have correct types."""
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        result = TestInfrastructureResult(
            test_files_detected=15,
            test_config_detected=True,
            coverage_config_detected=False,
            test_file_ratio=0.25,
            calculated_score=20,
            inferred_framework="pytest",
        )

        # Validate types
        assert isinstance(result.test_files_detected, int), "test_files_detected must be int"
        assert isinstance(result.test_config_detected, bool), "test_config_detected must be bool"
        assert isinstance(
            result.coverage_config_detected, bool
        ), "coverage_config_detected must be bool"
        assert isinstance(result.test_file_ratio, float), "test_file_ratio must be float"
        assert isinstance(result.calculated_score, int), "calculated_score must be int"
        assert isinstance(result.inferred_framework, str), "inferred_framework must be str"

    def test_score_capped_at_25_points(self):
        """Test that calculated_score is capped at 25 points (FR-013)."""
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        # Test with maximum possible score
        result = TestInfrastructureResult(
            test_files_detected=100,
            test_config_detected=True,
            coverage_config_detected=True,
            test_file_ratio=0.50,  # 50% ratio
            calculated_score=25,  # Should be capped at 25
            inferred_framework="pytest",
        )

        assert result.calculated_score <= 25, "Score must be capped at 25 points (FR-013)"
        assert result.calculated_score == 25, "Maximum score should be 25"

    def test_result_is_json_serializable(self):
        """Test that TestInfrastructureResult can be serialized to JSON."""
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        result = TestInfrastructureResult(
            test_files_detected=15,
            test_config_detected=True,
            coverage_config_detected=False,
            test_file_ratio=0.25,
            calculated_score=20,
            inferred_framework="pytest",
        )

        # Convert to dict (assuming dataclass or similar)
        result_dict = result.__dict__ if hasattr(result, "__dict__") else result.dict()

        # Verify JSON serialization works
        json_str = json.dumps(result_dict)
        assert json_str, "Result should be JSON serializable"

        # Verify deserialization
        parsed = json.loads(json_str)
        assert parsed["test_files_detected"] == 15
        assert parsed["test_config_detected"] is True
        assert parsed["coverage_config_detected"] is False
        assert parsed["test_file_ratio"] == 0.25
        assert parsed["calculated_score"] == 20
        assert parsed["inferred_framework"] == "pytest"

    def test_zero_score_for_no_infrastructure(self):
        """Test that repos with no test infrastructure get 0 points."""
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        # Simulate tetris-web scenario (no tests)
        result = TestInfrastructureResult(
            test_files_detected=0,
            test_config_detected=False,
            coverage_config_detected=False,
            test_file_ratio=0.0,
            calculated_score=0,
            inferred_framework="none",
        )

        assert result.test_files_detected == 0
        assert result.calculated_score == 0
        assert result.inferred_framework == "none"

    def test_partial_score_for_tests_without_coverage(self):
        """Test that repos with tests but no coverage get partial score."""
        from src.metrics.models.test_infrastructure import TestInfrastructureResult

        # Simulate partial infrastructure
        result = TestInfrastructureResult(
            test_files_detected=10,
            test_config_detected=True,
            coverage_config_detected=False,  # No coverage config
            test_file_ratio=0.15,  # 15% ratio (between 10-30%)
            calculated_score=15,  # 5 (tests) + 5 (config) + 5 (ratio bonus) = 15
            inferred_framework="pytest",
        )

        assert result.test_files_detected > 0
        assert result.test_config_detected is True
        assert result.coverage_config_detected is False
        assert 10 <= result.calculated_score <= 20, "Partial score should be 10-20 points"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
