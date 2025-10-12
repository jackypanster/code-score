"""
Contract tests for programmatic API return objects.

Validates that Pydantic models in src/cli/models.py comply with the
contract specification defined in specs/003-tests-integration-test/contracts/return_objects.py.

These tests verify:
- Pydantic model structure and fields
- Field validators and constraints
- Contract validation utilities
- Property calculations
"""

import pytest
from pydantic import ValidationError

from src.cli.models import EvaluationResult, ValidationResult


class TestValidationResultContract:
    """Contract tests for ValidationResult Pydantic model."""

    def test_validation_result_structure(self):
        """Verify ValidationResult has required fields."""
        result = ValidationResult(
            valid=True,
            items_checked=["submission_structure", "checklist_config"],
            passed_checks=["submission_structure", "checklist_config"],
            warnings=[],
        )

        # Verify fields exist
        assert hasattr(result, "valid")
        assert hasattr(result, "items_checked")
        assert hasattr(result, "passed_checks")
        assert hasattr(result, "warnings")

        # Verify field types
        assert isinstance(result.valid, bool)
        assert isinstance(result.items_checked, list)
        assert isinstance(result.passed_checks, list)
        assert isinstance(result.warnings, list)

        # Verify field values
        assert result.valid is True
        assert result.items_checked == ["submission_structure", "checklist_config"]
        assert result.passed_checks == ["submission_structure", "checklist_config"]
        assert result.warnings == []

    def test_validation_result_passed_checks_subset_validator(self):
        """Verify passed_checks must be subset of items_checked."""
        # Valid: passed_checks is subset
        result = ValidationResult(
            valid=False,
            items_checked=["item1", "item2", "item3"],
            passed_checks=["item1", "item2"],  # Subset
            warnings=[],
        )
        assert set(result.passed_checks).issubset(set(result.items_checked))

        # Invalid: passed_checks contains items not in items_checked
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                valid=True,
                items_checked=["item1", "item2"],
                passed_checks=["item1", "item3"],  # item3 not in items_checked
                warnings=[],
            )

        error = exc_info.value
        assert "passed_checks contains items not in items_checked" in str(error)

    def test_validation_result_valid_consistency_validator(self):
        """Verify if valid=True, passed_checks must equal items_checked."""
        # Valid: valid=True and passed_checks == items_checked
        result = ValidationResult(
            valid=True,
            items_checked=["item1", "item2"],
            passed_checks=["item1", "item2"],
            warnings=[],
        )
        assert set(result.passed_checks) == set(result.items_checked)

        # Invalid: valid=True but passed_checks != items_checked
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                valid=True,
                items_checked=["item1", "item2", "item3"],
                passed_checks=["item1", "item2"],  # Missing item3
                warnings=[],
            )

        error = exc_info.value
        assert "passed_checks must equal items_checked" in str(error)

    def test_validation_result_warnings_default(self):
        """Verify warnings field defaults to empty list."""
        result = ValidationResult(
            valid=True,
            items_checked=["item1"],
            passed_checks=["item1"],
            # warnings not provided
        )

        assert result.warnings == []
        assert isinstance(result.warnings, list)

    def test_validation_result_contract_validation(self):
        """Verify result passes contract validation utility."""
        import sys
        from pathlib import Path

        # Add specs directory to path for contract imports
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "003-tests-integration-test"
        sys.path.insert(0, str(specs_dir))

        from contracts.return_objects import (
            validate_validation_result_contract,
        )

        result = ValidationResult(
            valid=True,
            items_checked=["submission_structure", "checklist_config"],
            passed_checks=["submission_structure", "checklist_config"],
            warnings=["Non-critical warning"],
        )

        # Should pass validation without raising AssertionError
        assert validate_validation_result_contract(result) is True


class TestEvaluationResultContract:
    """Contract tests for EvaluationResult Pydantic model."""

    def test_evaluation_result_structure(self):
        """Verify EvaluationResult has required fields."""
        result = EvaluationResult(
            success=True,
            total_score=85.5,
            max_possible_score=100.0,
            grade="B",
            generated_files=["/output/score_input.json"],
            evidence_files={"code_quality": "/output/evidence/code_quality.json"},
            warnings=[],
        )

        # Verify fields exist
        assert hasattr(result, "success")
        assert hasattr(result, "total_score")
        assert hasattr(result, "max_possible_score")
        assert hasattr(result, "grade")
        assert hasattr(result, "generated_files")
        assert hasattr(result, "evidence_files")
        assert hasattr(result, "warnings")

        # Verify field types
        assert isinstance(result.success, bool)
        assert isinstance(result.total_score, (int, float))
        assert isinstance(result.max_possible_score, (int, float))
        assert isinstance(result.grade, str)
        assert isinstance(result.generated_files, list)
        assert isinstance(result.evidence_files, dict)
        assert isinstance(result.warnings, list)

        # Verify field values
        assert result.success is True
        assert result.total_score == 85.5
        assert result.max_possible_score == 100.0
        assert result.grade == "B"

    def test_evaluation_result_total_score_validator(self):
        """Verify total_score validation constraints."""
        # Valid: total_score within bounds
        result = EvaluationResult(
            success=True,
            total_score=75.0,
            max_possible_score=100.0,
            grade="C",
            generated_files=[],
        )
        assert result.total_score == 75.0

        # Invalid: negative total_score
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=-10.0,
                max_possible_score=100.0,
                grade="F",
                generated_files=[],
            )
        assert "total_score must be non-negative" in str(exc_info.value)

        # Invalid: total_score exceeds max_possible_score
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=150.0,
                max_possible_score=100.0,
                grade="A",
                generated_files=[],
            )
        assert "cannot exceed max_possible_score" in str(exc_info.value)

    def test_evaluation_result_max_possible_score_validator(self):
        """Verify max_possible_score must be positive."""
        # Valid: positive max_possible_score
        result = EvaluationResult(
            success=True,
            total_score=80.0,
            max_possible_score=100.0,
            grade="B",
            generated_files=[],
        )
        assert result.max_possible_score == 100.0

        # Invalid: zero max_possible_score
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=0.0,
                max_possible_score=0.0,
                grade="F",
                generated_files=[],
            )
        assert "max_possible_score must be positive" in str(exc_info.value)

        # Invalid: negative max_possible_score
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=50.0,
                max_possible_score=-100.0,
                grade="F",
                generated_files=[],
            )
        assert "max_possible_score must be positive" in str(exc_info.value)

    def test_evaluation_result_grade_validation(self):
        """Verify grade matches score percentage."""
        # Valid: A grade (≥90%)
        result = EvaluationResult(
            success=True,
            total_score=95.0,
            max_possible_score=100.0,
            grade="A",
            generated_files=[],
        )
        assert result.grade == "A"

        # Valid: B grade (≥80%, <90%)
        result = EvaluationResult(
            success=True,
            total_score=85.0,
            max_possible_score=100.0,
            grade="B",
            generated_files=[],
        )
        assert result.grade == "B"

        # Valid: F grade (<60%)
        result = EvaluationResult(
            success=True,
            total_score=50.0,
            max_possible_score=100.0,
            grade="F",
            generated_files=[],
        )
        assert result.grade == "F"

        # Invalid: grade doesn't match score
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=95.0,  # 95% should be A
                max_possible_score=100.0,
                grade="B",  # Wrong grade
                generated_files=[],
            )
        assert "grade 'B' doesn't match score" in str(exc_info.value)
        assert "expected 'A'" in str(exc_info.value)

        # Invalid: invalid grade letter
        with pytest.raises(ValidationError) as exc_info:
            EvaluationResult(
                success=True,
                total_score=85.0,
                max_possible_score=100.0,
                grade="X",  # Invalid grade
                generated_files=[],
            )
        assert "grade must be one of" in str(exc_info.value)

    def test_evaluation_result_score_percentage_property(self):
        """Verify score_percentage property calculation."""
        result = EvaluationResult(
            success=True,
            total_score=85.5,
            max_possible_score=100.0,
            grade="B",
            generated_files=[],
        )

        # Verify property returns correct percentage
        assert result.score_percentage == 85.5
        assert isinstance(result.score_percentage, float)

        # Test edge cases
        result_low = EvaluationResult(
            success=True,
            total_score=0.0,
            max_possible_score=100.0,
            grade="F",
            generated_files=[],
        )
        assert result_low.score_percentage == 0.0

        result_high = EvaluationResult(
            success=True,
            total_score=100.0,
            max_possible_score=100.0,
            grade="A",
            generated_files=[],
        )
        assert result_high.score_percentage == 100.0

    def test_evaluation_result_defaults(self):
        """Verify optional fields have correct defaults."""
        result = EvaluationResult(
            success=True,
            total_score=80.0,
            max_possible_score=100.0,
            grade="B",
            generated_files=[],
            # evidence_files and warnings not provided
        )

        assert result.evidence_files == {}
        assert result.warnings == []
        assert isinstance(result.evidence_files, dict)
        assert isinstance(result.warnings, list)

    def test_evaluation_result_contract_validation(self):
        """Verify result passes contract validation utility."""
        import sys
        from pathlib import Path

        # Add specs directory to path for contract imports
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "003-tests-integration-test"
        sys.path.insert(0, str(specs_dir))

        from contracts.return_objects import (
            validate_evaluation_result_contract,
        )

        result = EvaluationResult(
            success=True,
            total_score=85.5,
            max_possible_score=100.0,
            grade="B",
            generated_files=["/output/score_input.json"],
            evidence_files={"code_quality": "/output/evidence/code_quality.json"},
            warnings=["Non-critical warning"],
        )

        # Should pass validation without raising AssertionError
        assert validate_evaluation_result_contract(result) is True


class TestGradeCalculation:
    """Contract tests for grade calculation helper."""

    def test_calculate_grade_function(self):
        """Verify _calculate_grade helper function."""
        from src.cli.models import _calculate_grade

        # Test all grade boundaries
        assert _calculate_grade(100.0) == "A"
        assert _calculate_grade(95.0) == "A"
        assert _calculate_grade(90.0) == "A"

        assert _calculate_grade(89.9) == "B"
        assert _calculate_grade(85.0) == "B"
        assert _calculate_grade(80.0) == "B"

        assert _calculate_grade(79.9) == "C"
        assert _calculate_grade(75.0) == "C"
        assert _calculate_grade(70.0) == "C"

        assert _calculate_grade(69.9) == "D"
        assert _calculate_grade(65.0) == "D"
        assert _calculate_grade(60.0) == "D"

        assert _calculate_grade(59.9) == "F"
        assert _calculate_grade(50.0) == "F"
        assert _calculate_grade(0.0) == "F"
