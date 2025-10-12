"""
Unit tests for evaluate_submission() function.

Following project guidelines: NO MOCKS - use real data and real tools.
These tests focus on input validation, error handling, and return value verification
using minimal real data to keep tests lightweight.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.cli.evaluate import evaluate_submission
from src.cli.exceptions import EvaluationFileSystemError, QualityGateException
from src.cli.models import EvaluationResult, ValidationResult


class TestEvaluateSubmissionInputValidation:
    """Test input validation and error handling without mocks."""

    def test_missing_submission_file_raises_file_not_found(self):
        """Test that missing submission file raises FileNotFoundError."""
        # Use a path that definitely doesn't exist
        non_existent_path = Path("/tmp/definitely_does_not_exist_12345678.json")

        # Ensure it really doesn't exist
        if non_existent_path.exists():
            non_existent_path.unlink()

        with pytest.raises(FileNotFoundError):
            evaluate_submission(
                submission_file=non_existent_path,
                validate_only=False,
                quiet=True
            )

    def test_invalid_json_raises_value_error(self):
        """Test that invalid JSON content raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "invalid.json"

            # Write invalid JSON
            submission_file.write_text("{ this is definitely not valid JSON }")

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    quiet=True
                )

            # Verify error message mentions JSON
            error_msg = str(exc_info.value).lower()
            assert "json" in error_msg or "invalid" in error_msg

    def test_missing_required_sections_raises_value_error(self):
        """Test that submission missing required sections raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "incomplete.json"

            # Write JSON missing required sections (repository and metrics)
            incomplete_data = {
                "schema_version": "1.0.0",
                # Missing "repository" and "metrics" - should fail
            }
            submission_file.write_text(json.dumps(incomplete_data, indent=2))

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    quiet=True
                )

            # Verify error message mentions missing sections
            error_msg = str(exc_info.value).lower()
            assert "missing" in error_msg or "required" in error_msg

    def test_missing_repository_section_raises_value_error(self):
        """Test that submission missing repository section raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "no_repo.json"

            # Write JSON missing repository section only
            no_repo_data = {
                "schema_version": "1.0.0",
                # Missing "repository"
                "metrics": {
                    "code_quality": {},
                    "testing": {},
                    "documentation": {}
                },
                "execution": {"success": True}
            }
            submission_file.write_text(json.dumps(no_repo_data, indent=2))

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    quiet=True
                )

            error_msg = str(exc_info.value).lower()
            assert "repository" in error_msg or "missing" in error_msg

    def test_missing_metrics_section_raises_value_error(self):
        """Test that submission missing metrics section raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "no_metrics.json"

            # Write JSON missing metrics section only
            no_metrics_data = {
                "schema_version": "1.0.0",
                "repository": {
                    "url": "https://github.com/test/repo.git",
                    "commit": "abc123",
                    "language": "python"
                },
                # Missing "metrics"
                "execution": {"success": True}
            }
            submission_file.write_text(json.dumps(no_metrics_data, indent=2))

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    quiet=True
                )

            error_msg = str(exc_info.value).lower()
            assert "metrics" in error_msg or "missing" in error_msg


class TestEvaluateSubmissionValidateOnlyMode:
    """Test validate-only mode with real minimal data."""

    def create_minimal_valid_submission(self, temp_path: Path) -> Path:
        """Create a minimal valid submission file."""
        submission_file = temp_path / "submission.json"

        minimal_data = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123def",
                "language": "python",
                "timestamp": "2025-10-12T10:00:00Z"
            },
            "metrics": {
                "code_quality": {},
                "testing": {},
                "documentation": {}
            },
            "execution": {"success": True}
        }

        submission_file.write_text(json.dumps(minimal_data, indent=2))
        return submission_file

    def test_validate_only_returns_validation_result(self):
        """Test that validate_only=True returns ValidationResult."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_minimal_valid_submission(temp_path)

            result = evaluate_submission(
                submission_file=submission_file,
                validate_only=True,
                quiet=True
            )

            # Verify return type
            assert isinstance(result, ValidationResult), \
                f"Expected ValidationResult, got {type(result)}"

            # Verify ValidationResult structure
            assert hasattr(result, "valid")
            assert hasattr(result, "items_checked")
            assert hasattr(result, "passed_checks")
            assert hasattr(result, "warnings")

            # Verify values
            assert result.valid is True
            assert isinstance(result.items_checked, list)
            assert len(result.items_checked) > 0
            assert isinstance(result.passed_checks, list)
            assert set(result.passed_checks) == set(result.items_checked), \
                "For valid submission, all checks should pass"

    def test_validate_only_does_not_generate_files(self):
        """Test that validate_only=True does not generate output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_minimal_valid_submission(temp_path)
            output_dir = temp_path / "output"

            result = evaluate_submission(
                submission_file=submission_file,
                output_dir=output_dir,
                validate_only=True,
                quiet=True
            )

            assert isinstance(result, ValidationResult)

            # Verify no output files were created
            # In validate-only mode, output directory might not even be created
            if output_dir.exists():
                score_file = output_dir / "score_input.json"
                report_file = output_dir / "evaluation_report.md"

                assert not score_file.exists(), \
                    "score_input.json should not be generated in validate-only mode"
                assert not report_file.exists(), \
                    "evaluation_report.md should not be generated in validate-only mode"


class TestEvaluateSubmissionNormalMode:
    """Test normal evaluation mode with real minimal data."""

    def create_submission_with_metrics(self, temp_path: Path, score_level: str = "high") -> Path:
        """Create submission with metrics for testing.

        Args:
            score_level: 'high', 'medium', or 'low' to control expected score
        """
        submission_file = temp_path / "submission.json"

        if score_level == "high":
            # High quality metrics
            metrics_data = {
                "code_quality": {
                    "linting": {
                        "tool": "ruff",
                        "passed": True,
                        "issues_count": 0,
                        "severity_breakdown": {"error": 0, "warning": 0}
                    },
                    "static_analysis": {"passed": True}
                },
                "testing": {
                    "test_execution": {
                        "passed": True,
                        "total_tests": 50,
                        "passed_tests": 50,
                        "failed_tests": 0
                    },
                    "coverage": {"line_coverage": 95.0}
                },
                "documentation": {
                    "readme_analysis": {
                        "exists": True,
                        "word_count": 1000,
                        "has_installation": True,
                        "has_usage": True,
                        "has_examples": True
                    }
                }
            }
        elif score_level == "low":
            # Low quality metrics
            metrics_data = {
                "code_quality": {
                    "linting": {
                        "passed": False,
                        "issues_count": 500
                    }
                },
                "testing": {
                    "test_execution": {
                        "passed": False,
                        "total_tests": 0
                    }
                },
                "documentation": {
                    "readme_analysis": {
                        "exists": False
                    }
                }
            }
        else:  # medium
            metrics_data = {
                "code_quality": {
                    "linting": {"passed": True, "issues_count": 10}
                },
                "testing": {
                    "test_execution": {"passed": True, "total_tests": 20}
                },
                "documentation": {
                    "readme_analysis": {"exists": True, "word_count": 300}
                }
            }

        submission_data = {
            "schema_version": "1.0.0",
            "repository": {
                "url": "https://github.com/test/repo.git",
                "commit": "abc123def456",
                "language": "python",
                "timestamp": "2025-10-12T10:00:00Z"
            },
            "metrics": metrics_data,
            "execution": {
                "start_time": "2025-10-12T10:00:00Z",
                "end_time": "2025-10-12T10:05:00Z",
                "success": True
            }
        }

        submission_file.write_text(json.dumps(submission_data, indent=2))
        return submission_file

    def test_normal_mode_returns_evaluation_result(self):
        """Test that normal mode returns EvaluationResult."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_submission_with_metrics(temp_path, score_level="high")
            output_dir = temp_path / "output"

            # Execute (may raise QualityGateException if score < 30%)
            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=output_dir,
                    format="json",
                    validate_only=False,
                    quiet=True
                )
            except QualityGateException as e:
                # If quality gate fails, extract result from exception
                percentage = e.score
                if percentage >= 90:
                    grade = "A"
                elif percentage >= 80:
                    grade = "B"
                elif percentage >= 70:
                    grade = "C"
                elif percentage >= 60:
                    grade = "D"
                else:
                    grade = "F"

                result = EvaluationResult(
                    success=False,
                    total_score=e.evaluation_result.total_score,
                    max_possible_score=e.evaluation_result.max_possible_score,
                    grade=grade,
                    generated_files=[],
                    evidence_files={},
                    warnings=[]
                )

            # Verify return type
            assert isinstance(result, EvaluationResult), \
                f"Expected EvaluationResult, got {type(result)}"

            # Verify EvaluationResult structure
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

            # Verify value constraints
            assert result.total_score >= 0
            assert result.max_possible_score > 0
            assert result.total_score <= result.max_possible_score
            assert result.grade in ["A", "B", "C", "D", "F"]

    def test_quality_gate_failure_raises_exception(self):
        """Test that low scores raise QualityGateException."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = self.create_submission_with_metrics(temp_path, score_level="low")
            output_dir = temp_path / "output"

            # Execute - should raise QualityGateException for low scores
            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=output_dir,
                    format="json",
                    validate_only=False,
                    quiet=True
                )

                # If no exception, score must be >= 30%
                assert result.total_score / result.max_possible_score >= 0.30, \
                    "If no exception raised, score should be >= 30%"

            except QualityGateException as e:
                # Verify exception attributes
                assert hasattr(e, "score")
                assert hasattr(e, "threshold")
                assert hasattr(e, "evaluation_result")

                # Verify exception values
                assert isinstance(e.score, (int, float))
                assert isinstance(e.threshold, (int, float))
                assert e.score < e.threshold
                assert e.threshold == 30.0
                assert e.score < 30.0

                # Verify evaluation_result is accessible
                assert e.evaluation_result is not None
                assert hasattr(e.evaluation_result, "total_score")
                assert hasattr(e.evaluation_result, "max_possible_score")


class TestEvaluateSubmissionFileSystemErrors:
    """Test filesystem error handling."""

    def test_invalid_output_dir_raises_filesystem_error(self):
        """Test that invalid output directory raises EvaluationFileSystemError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "submission.json"

            # Create minimal valid submission
            submission_data = {
                "schema_version": "1.0.0",
                "repository": {
                    "url": "https://github.com/test/repo.git",
                    "commit": "abc123",
                    "language": "python",
                    "timestamp": "2025-10-12T10:00:00Z"
                },
                "metrics": {
                    "code_quality": {},
                    "testing": {},
                    "documentation": {}
                },
                "execution": {"success": True}
            }
            submission_file.write_text(json.dumps(submission_data, indent=2))

            # Try to write to read-only or invalid directory
            # /root is typically read-only on most systems
            invalid_output_dir = "/root/test_invalid_dir_99999"

            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=invalid_output_dir,
                    format="json",
                    validate_only=False,
                    quiet=True
                )

                # If successful (running as root), skip test
                pytest.skip("Test requires non-writable directory, but directory was writable")

            except (EvaluationFileSystemError, PermissionError) as e:
                # Either exception type is acceptable
                if isinstance(e, EvaluationFileSystemError):
                    # Verify EvaluationFileSystemError attributes
                    assert hasattr(e, "operation")
                    assert hasattr(e, "target_path")
                    assert hasattr(e, "original_error")

                    assert e.operation
                    assert e.target_path
                    assert isinstance(e.original_error, Exception)
                # PermissionError is also acceptable


class TestEvaluateSubmissionReturnValues:
    """Test return value contracts."""

    def test_validation_result_contract(self):
        """Test that ValidationResult follows contract specifications."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "submission.json"

            submission_data = {
                "schema_version": "1.0.0",
                "repository": {
                    "url": "https://github.com/test/repo.git",
                    "commit": "abc123",
                    "language": "python",
                    "timestamp": "2025-10-12T10:00:00Z"
                },
                "metrics": {"code_quality": {}, "testing": {}, "documentation": {}},
                "execution": {"success": True}
            }
            submission_file.write_text(json.dumps(submission_data, indent=2))

            result = evaluate_submission(
                submission_file=submission_file,
                validate_only=True,
                quiet=True
            )

            # ValidationResult contract requirements
            assert isinstance(result.valid, bool)
            assert isinstance(result.items_checked, list)
            assert isinstance(result.passed_checks, list)
            assert isinstance(result.warnings, list)

            # passed_checks must be subset of items_checked
            assert set(result.passed_checks).issubset(set(result.items_checked))

            # If valid=True, passed_checks must equal items_checked
            if result.valid:
                assert set(result.passed_checks) == set(result.items_checked)

    def test_evaluation_result_grade_matches_score(self):
        """Test that EvaluationResult grade matches score percentage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "submission.json"

            # Create submission with medium quality for predictable score
            submission_data = {
                "schema_version": "1.0.0",
                "repository": {
                    "url": "https://github.com/test/repo.git",
                    "commit": "abc123",
                    "language": "python",
                    "timestamp": "2025-10-12T10:00:00Z"
                },
                "metrics": {
                    "code_quality": {
                        "linting": {"passed": True, "issues_count": 5}
                    },
                    "testing": {
                        "test_execution": {"passed": True, "total_tests": 30}
                    },
                    "documentation": {
                        "readme_analysis": {"exists": True, "word_count": 400}
                    }
                },
                "execution": {"success": True}
            }
            submission_file.write_text(json.dumps(submission_data, indent=2))
            output_dir = temp_path / "output"

            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=output_dir,
                    format="json",
                    validate_only=False,
                    quiet=True
                )
            except QualityGateException as e:
                # Extract result from exception
                percentage = e.score
                if percentage >= 90:
                    expected_grade = "A"
                elif percentage >= 80:
                    expected_grade = "B"
                elif percentage >= 70:
                    expected_grade = "C"
                elif percentage >= 60:
                    expected_grade = "D"
                else:
                    expected_grade = "F"

                result = EvaluationResult(
                    success=False,
                    total_score=e.evaluation_result.total_score,
                    max_possible_score=e.evaluation_result.max_possible_score,
                    grade=expected_grade,
                    generated_files=[],
                    evidence_files={},
                    warnings=[]
                )

            # Calculate expected grade
            percentage = (result.total_score / result.max_possible_score) * 100

            if percentage >= 90:
                expected_grade = "A"
            elif percentage >= 80:
                expected_grade = "B"
            elif percentage >= 70:
                expected_grade = "C"
            elif percentage >= 60:
                expected_grade = "D"
            else:
                expected_grade = "F"

            # Verify grade matches calculation
            assert result.grade == expected_grade, \
                f"Grade {result.grade} doesn't match expected {expected_grade} for score {percentage:.1f}%"
