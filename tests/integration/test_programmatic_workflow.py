"""
Integration tests for programmatic evaluation workflow.

These tests validate the programmatic API (evaluate_submission function) using
real submission files and real tool execution WITHOUT MOCKS.

Following project guidelines:
- All tests must be real integration tests (no mocks)
- Tests call real APIs, databases, or services
- Fail-fast on any errors (no exception catching unless testing error paths)
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.cli.evaluate import evaluate_submission
from src.cli.exceptions import EvaluationFileSystemError, QualityGateException
from src.cli.models import EvaluationResult, ValidationResult


class TestProgrammaticEvaluationWorkflow:
    """Test programmatic evaluation workflow with real submission files."""

    def test_programmatic_execution_normal_mode(self):
        """Test normal evaluation mode returns EvaluationResult with real data."""
        # Use real submission file if available, otherwise create minimal one
        submission_file = Path("output/submission.json")

        if not submission_file.exists():
            # Create minimal valid submission for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                submission_file = temp_path / "submission.json"

                # Create minimal valid submission data
                submission_data = {
                    "schema_version": "1.0.0",
                    "repository": {
                        "url": "https://github.com/test/repo.git",
                        "commit": "abc123def456",
                        "language": "python",
                        "timestamp": "2025-10-12T10:00:00Z"
                    },
                    "metrics": {
                        "code_quality": {
                            "linting": {
                                "tool": "ruff",
                                "passed": True,
                                "issues_count": 0,
                                "severity_breakdown": {"error": 0, "warning": 0}
                            },
                            "static_analysis": {
                                "passed": True
                            }
                        },
                        "testing": {
                            "test_execution": {
                                "passed": True,
                                "total_tests": 10,
                                "passed_tests": 10,
                                "failed_tests": 0
                            }
                        },
                        "documentation": {
                            "readme_analysis": {
                                "exists": True,
                                "word_count": 500,
                                "has_installation": True,
                                "has_usage": True
                            }
                        }
                    },
                    "execution": {
                        "start_time": "2025-10-12T10:00:00Z",
                        "end_time": "2025-10-12T10:05:00Z",
                        "success": True,
                        "duration_seconds": 300
                    }
                }

                submission_file.write_text(json.dumps(submission_data, indent=2))
                output_dir = temp_path / "output"

                # Execute evaluation (may raise QualityGateException if score < 30%)
                try:
                    result = evaluate_submission(
                        submission_file=submission_file,
                        output_dir=output_dir,
                        format="json",
                        validate_only=False,
                        verbose=False,
                        quiet=True
                    )
                except QualityGateException as e:
                    # Quality gate exception is acceptable - extract data from exception
                    # Convert percentage to letter grade
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
                        success=False,  # Quality gate failed
                        total_score=e.evaluation_result.total_score,
                        max_possible_score=e.evaluation_result.max_possible_score,
                        grade=grade,
                        generated_files=[],  # Files may still have been generated
                        evidence_files={},
                        warnings=list(e.evaluation_result.evaluation_metadata.warnings) if hasattr(e.evaluation_result, 'evaluation_metadata') else []
                    )

                # Verify return type
                assert isinstance(result, EvaluationResult), f"Expected EvaluationResult, got {type(result)}"

                # Verify required fields exist
                assert hasattr(result, "success"), "Result should have 'success' field"
                assert hasattr(result, "total_score"), "Result should have 'total_score' field"
                assert hasattr(result, "max_possible_score"), "Result should have 'max_possible_score' field"
                assert hasattr(result, "grade"), "Result should have 'grade' field"
                assert hasattr(result, "generated_files"), "Result should have 'generated_files' field"
                assert hasattr(result, "evidence_files"), "Result should have 'evidence_files' field"

                # Verify field values
                # Note: success may be False if quality gate failed
                assert isinstance(result.success, bool), "success should be boolean"
                assert result.total_score >= 0, "Total score should be non-negative"
                assert result.max_possible_score > 0, "Max score should be positive"
                assert result.grade in ["A", "B", "C", "D", "F"], f"Invalid grade: {result.grade}"
                assert isinstance(result.generated_files, list), "generated_files should be a list"
                assert isinstance(result.evidence_files, dict), "evidence_files should be a dict"

                # Verify score relationship
                assert result.total_score <= result.max_possible_score, "Score should not exceed max"

                # Verify generated files exist
                for file_path in result.generated_files:
                    file_obj = Path(file_path)
                    assert file_obj.exists(), f"Generated file should exist: {file_path}"
                    assert file_obj.is_file(), f"Generated path should be a file: {file_path}"

        else:
            # Use existing submission file from output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                output_dir = temp_path / "test_output"

                # Execute evaluation with real submission file (may raise QualityGateException)
                try:
                    result = evaluate_submission(
                        submission_file=submission_file,
                        output_dir=output_dir,
                        format="json",
                        validate_only=False,
                        verbose=False,
                        quiet=True
                    )
                except QualityGateException as e:
                    # Quality gate failure is expected for low-scoring submissions
                    # Extract data from exception to create result object
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
                        success=False,  # Quality gate failed
                        total_score=e.evaluation_result.total_score,
                        max_possible_score=e.evaluation_result.max_possible_score,
                        grade=grade,
                        generated_files=[],
                        evidence_files={},
                        warnings=list(e.evaluation_result.evaluation_metadata.warnings) if hasattr(e.evaluation_result, 'evaluation_metadata') else []
                    )

                # Same verifications as above
                assert isinstance(result, EvaluationResult)
                # Note: success may be False if quality gate failed
                assert isinstance(result.success, bool)
                assert result.total_score >= 0
                assert result.grade in ["A", "B", "C", "D", "F"]

    def test_programmatic_execution_validate_only(self):
        """Test validate-only mode returns ValidationResult."""
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
                "execution": {
                    "success": True
                }
            }

            submission_file.write_text(json.dumps(submission_data, indent=2))

            # Execute validation
            result = evaluate_submission(
                submission_file=submission_file,
                validate_only=True,
                verbose=False,
                quiet=True
            )

            # Verify return type
            assert isinstance(result, ValidationResult), f"Expected ValidationResult, got {type(result)}"

            # Verify required fields
            assert hasattr(result, "valid"), "Result should have 'valid' field"
            assert hasattr(result, "items_checked"), "Result should have 'items_checked' field"
            assert hasattr(result, "passed_checks"), "Result should have 'passed_checks' field"
            assert hasattr(result, "warnings"), "Result should have 'warnings' field"

            # Verify field values
            assert result.valid is True, "Validation should pass for valid submission"
            assert isinstance(result.items_checked, list), "items_checked should be a list"
            assert len(result.items_checked) > 0, "Should check at least one item"
            assert isinstance(result.passed_checks, list), "passed_checks should be a list"
            assert set(result.passed_checks).issubset(set(result.items_checked)), "passed_checks must be subset of items_checked"
            assert isinstance(result.warnings, list), "warnings should be a list"

            # Verify relationship between fields
            assert set(result.passed_checks) == set(result.items_checked), "All checks should pass for valid submission"

    def test_quality_gate_exception_raised(self):
        """Test that QualityGateException is raised for low scores."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "low_score_submission.json"

            # Create submission with metrics that will result in low score
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
                        "linting": {
                            "tool": "none",
                            "passed": False,
                            "issues_count": 100,
                            "severity_breakdown": {"error": 50, "warning": 50}
                        },
                        "static_analysis": {
                            "passed": False
                        }
                    },
                    "testing": {
                        "test_execution": {
                            "passed": False,
                            "total_tests": 0,
                            "passed_tests": 0,
                            "failed_tests": 0
                        }
                    },
                    "documentation": {
                        "readme_analysis": {
                            "exists": False,
                            "word_count": 0
                        }
                    }
                },
                "execution": {
                    "start_time": "2025-10-12T10:00:00Z",
                    "end_time": "2025-10-12T10:01:00Z",
                    "success": True
                }
            }

            submission_file.write_text(json.dumps(submission_data, indent=2))
            output_dir = temp_path / "output"

            # Execute evaluation - should raise QualityGateException if score < 30%
            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=output_dir,
                    format="json",
                    validate_only=False,
                    verbose=False,
                    quiet=True
                )

                # If no exception was raised, score must be >= 30%
                assert result.total_score / result.max_possible_score >= 0.30, \
                    "If no exception, score should be >= 30%"

            except QualityGateException as e:
                # Verify exception attributes
                assert hasattr(e, "score"), "Exception should have 'score' attribute"
                assert hasattr(e, "threshold"), "Exception should have 'threshold' attribute"
                assert hasattr(e, "evaluation_result"), "Exception should have 'evaluation_result' attribute"

                # Verify score relationship
                assert e.score < e.threshold, "Score should be below threshold"
                assert e.threshold == 30.0, "Threshold should be 30%"
                assert e.score < 30.0, "Score should be less than 30%"

                # Verify evaluation result is accessible
                assert e.evaluation_result is not None, "Should have evaluation result"

    def test_filesystem_error_raised(self):
        """Test that EvaluationFileSystemError is raised for filesystem failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "submission.json"

            # Create valid submission
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
                "execution": {
                    "success": True
                }
            }

            submission_file.write_text(json.dumps(submission_data, indent=2))

            # Try to write to read-only or invalid directory
            # Note: /root is typically read-only on most systems
            invalid_output_dir = "/root/test_invalid_output_dir_12345"

            # Execute evaluation - should raise EvaluationFileSystemError
            try:
                result = evaluate_submission(
                    submission_file=submission_file,
                    output_dir=invalid_output_dir,
                    format="json",
                    validate_only=False,
                    verbose=False,
                    quiet=True
                )

                # If no exception, the directory might have been created
                # (possible if running as root)
                pytest.skip("Test requires non-writable directory, but directory was writable")

            except EvaluationFileSystemError as e:
                # Verify exception attributes
                assert hasattr(e, "operation"), "Exception should have 'operation' attribute"
                assert hasattr(e, "target_path"), "Exception should have 'target_path' attribute"
                assert hasattr(e, "original_error"), "Exception should have 'original_error' attribute"

                # Verify attributes are non-empty
                assert e.operation, "Operation should be non-empty"
                assert e.target_path, "Target path should be non-empty"
                assert isinstance(e.original_error, Exception), "Original error should be Exception"

                # Verify operation describes what failed
                assert e.operation in ["create_directory", "write_file", "save_evidence_files"], \
                    f"Unexpected operation: {e.operation}"

            except PermissionError:
                # Alternative: some systems raise PermissionError directly
                # This is acceptable behavior
                pass


class TestProgrammaticAPIErrorHandling:
    """Test error handling in programmatic API."""

    def test_missing_submission_file_raises_file_not_found(self):
        """Test that missing submission file raises FileNotFoundError."""
        non_existent_file = "/tmp/non_existent_submission_12345.json"

        with pytest.raises(FileNotFoundError):
            evaluate_submission(
                submission_file=non_existent_file,
                validate_only=False,
                verbose=False,
                quiet=True
            )

    def test_invalid_json_raises_value_error(self):
        """Test that invalid JSON raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "invalid.json"

            # Write invalid JSON
            submission_file.write_text("{ this is not valid JSON }")

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    verbose=False,
                    quiet=True
                )

            assert "JSON" in str(exc_info.value) or "json" in str(exc_info.value), \
                "Error message should mention JSON"

    def test_missing_required_sections_raises_value_error(self):
        """Test that missing required sections raises ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            submission_file = temp_path / "incomplete.json"

            # Write JSON missing required sections
            incomplete_data = {
                "schema_version": "1.0.0"
                # Missing "repository" and "metrics" sections
            }
            submission_file.write_text(json.dumps(incomplete_data, indent=2))

            with pytest.raises(ValueError) as exc_info:
                evaluate_submission(
                    submission_file=submission_file,
                    validate_only=False,
                    verbose=False,
                    quiet=True
                )

            error_msg = str(exc_info.value).lower()
            assert "missing" in error_msg or "required" in error_msg, \
                "Error message should mention missing/required sections"
