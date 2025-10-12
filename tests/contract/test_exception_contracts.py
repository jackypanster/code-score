"""
Contract tests for custom exception types.

Validates that exception classes in src/cli/exceptions.py comply with the
contract specification defined in specs/003-tests-integration-test/contracts/exception_types.py.

These tests verify:
- Exception class structure and inheritance
- Required attributes and their types
- Auto-generated message formatting
- __repr__ implementation
- Contract validation utilities
"""

import pytest

from src.cli.exceptions import EvaluationFileSystemError, QualityGateException


class TestQualityGateExceptionContract:
    """Contract tests for QualityGateException."""

    def test_quality_gate_exception_structure(self):
        """Verify QualityGateException has required attributes."""
        # Create mock evaluation result
        mock_eval_result = {"total_score": 25.5, "items": []}

        # Create exception instance
        exc = QualityGateException(
            score=25.5, threshold=30.0, evaluation_result=mock_eval_result
        )

        # Verify required attributes exist
        assert hasattr(exc, "score"), "Must have 'score' attribute"
        assert hasattr(exc, "threshold"), "Must have 'threshold' attribute"
        assert hasattr(
            exc, "evaluation_result"
        ), "Must have 'evaluation_result' attribute"

        # Verify attribute types
        assert isinstance(exc.score, (int, float)), "score must be numeric"
        assert isinstance(exc.threshold, (int, float)), "threshold must be numeric"

        # Verify attribute values
        assert exc.score == 25.5
        assert exc.threshold == 30.0
        assert exc.evaluation_result == mock_eval_result

    def test_quality_gate_exception_inheritance(self):
        """Verify QualityGateException inherits from Exception."""
        mock_eval_result = {}
        exc = QualityGateException(
            score=20.0, threshold=30.0, evaluation_result=mock_eval_result
        )

        # Verify inheritance chain
        assert isinstance(exc, Exception), "Must inherit from Exception"
        assert isinstance(
            exc, QualityGateException
        ), "Must be QualityGateException instance"

        # Verify can be raised and caught as Exception
        with pytest.raises(Exception):
            raise exc

        # Verify can be raised and caught as QualityGateException
        with pytest.raises(QualityGateException):
            raise exc

    def test_quality_gate_exception_auto_message(self):
        """Verify auto-generated error message format."""
        mock_eval_result = {}
        exc = QualityGateException(
            score=25.5, threshold=30.0, evaluation_result=mock_eval_result
        )

        # Verify auto-generated message format
        expected_message = "Quality gate failure: score 25.5% below threshold 30.0%"
        assert str(exc) == expected_message

    def test_quality_gate_exception_custom_message(self):
        """Verify custom error message can be provided."""
        mock_eval_result = {}
        custom_message = "Custom quality gate failure message"

        exc = QualityGateException(
            score=20.0,
            threshold=30.0,
            evaluation_result=mock_eval_result,
            message=custom_message,
        )

        assert str(exc) == custom_message

    def test_quality_gate_exception_repr(self):
        """Verify __repr__ includes score and threshold."""
        mock_eval_result = {}
        exc = QualityGateException(
            score=25.5, threshold=30.0, evaluation_result=mock_eval_result
        )

        repr_str = repr(exc)

        # Verify repr includes key information
        assert "QualityGateException" in repr_str
        assert "25.5" in repr_str
        assert "30.0" in repr_str
        assert "score=" in repr_str
        assert "threshold=" in repr_str

    def test_quality_gate_exception_contract_validation(self):
        """Verify exception passes contract validation utility."""
        import sys
        from pathlib import Path

        # Add specs directory to path for contract imports
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "003-tests-integration-test"
        sys.path.insert(0, str(specs_dir))

        from contracts.exception_types import (
            validate_quality_gate_exception_contract,
        )

        mock_eval_result = {}
        exc = QualityGateException(
            score=25.5, threshold=30.0, evaluation_result=mock_eval_result
        )

        # Should pass validation without raising AssertionError
        assert validate_quality_gate_exception_contract(exc) is True


class TestEvaluationFileSystemErrorContract:
    """Contract tests for EvaluationFileSystemError."""

    def test_filesystem_error_structure(self):
        """Verify EvaluationFileSystemError has required attributes."""
        # Create mock original error
        original_error = OSError("Permission denied")

        # Create exception instance
        exc = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/output/evidence",
            original_error=original_error,
        )

        # Verify required attributes exist
        assert hasattr(exc, "operation"), "Must have 'operation' attribute"
        assert hasattr(exc, "target_path"), "Must have 'target_path' attribute"
        assert hasattr(exc, "original_error"), "Must have 'original_error' attribute"

        # Verify attribute types
        assert isinstance(exc.operation, str), "operation must be string"
        assert isinstance(exc.target_path, str), "target_path must be string"
        assert isinstance(
            exc.original_error, Exception
        ), "original_error must be Exception"

        # Verify attribute values
        assert exc.operation == "create_directory"
        assert exc.target_path == "/output/evidence"
        assert exc.original_error == original_error

    def test_filesystem_error_inheritance(self):
        """Verify EvaluationFileSystemError inherits from Exception."""
        original_error = PermissionError("No access")
        exc = EvaluationFileSystemError(
            operation="write_file",
            target_path="/output/score_input.json",
            original_error=original_error,
        )

        # Verify inheritance chain
        assert isinstance(exc, Exception), "Must inherit from Exception"
        assert isinstance(
            exc, EvaluationFileSystemError
        ), "Must be EvaluationFileSystemError instance"

        # Verify can be raised and caught as Exception
        with pytest.raises(Exception):
            raise exc

        # Verify can be raised and caught as EvaluationFileSystemError
        with pytest.raises(EvaluationFileSystemError):
            raise exc

    def test_filesystem_error_auto_message(self):
        """Verify auto-generated error message format."""
        original_error = PermissionError("Permission denied")
        exc = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/read-only/path",
            original_error=original_error,
        )

        # Verify auto-generated message format includes all details
        message = str(exc)
        assert "create_directory" in message
        assert "/read-only/path" in message
        assert "PermissionError" in message
        assert "Permission denied" in message

    def test_filesystem_error_custom_message(self):
        """Verify custom error message can be provided."""
        original_error = OSError("Disk full")
        custom_message = "Custom filesystem error message"

        exc = EvaluationFileSystemError(
            operation="write_file",
            target_path="/output/report.md",
            original_error=original_error,
            message=custom_message,
        )

        assert str(exc) == custom_message

    def test_filesystem_error_repr(self):
        """Verify __repr__ includes operation and target_path."""
        original_error = PermissionError("Permission denied")
        exc = EvaluationFileSystemError(
            operation="write_file",
            target_path="/output/score_input.json",
            original_error=original_error,
        )

        repr_str = repr(exc)

        # Verify repr includes key information
        assert "EvaluationFileSystemError" in repr_str
        assert "operation='write_file'" in repr_str
        assert "target_path='/output/score_input.json'" in repr_str
        assert "original_error=PermissionError" in repr_str

    def test_filesystem_error_contract_validation(self):
        """Verify exception passes contract validation utility."""
        import sys
        from pathlib import Path

        # Add specs directory to path for contract imports
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "003-tests-integration-test"
        sys.path.insert(0, str(specs_dir))

        from contracts.exception_types import (
            validate_filesystem_error_contract,
        )

        original_error = OSError("Test error")
        exc = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/output/evidence",
            original_error=original_error,
        )

        # Should pass validation without raising AssertionError
        assert validate_filesystem_error_contract(exc) is True

    def test_filesystem_error_wraps_various_os_errors(self):
        """Verify EvaluationFileSystemError can wrap different OS error types."""
        os_errors = [
            OSError("Generic OS error"),
            PermissionError("No permission"),
            IOError("I/O error"),
            FileNotFoundError("File not found"),
        ]

        for original_error in os_errors:
            exc = EvaluationFileSystemError(
                operation="test_operation",
                target_path="/test/path",
                original_error=original_error,
            )

            assert exc.original_error == original_error
            assert isinstance(exc, Exception)
            assert type(original_error).__name__ in str(exc)
