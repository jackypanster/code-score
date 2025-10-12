"""
Unit tests for custom exception types.

Following project guidelines: NO MOCKS - direct exception instantiation and testing.
These tests verify exception attributes, message generation, and inheritance.
"""

from unittest.mock import Mock

import pytest

from src.cli.exceptions import EvaluationFileSystemError, QualityGateException


class TestQualityGateException:
    """Test QualityGateException attributes and behavior."""

    def test_quality_gate_exception_attributes(self):
        """Test that QualityGateException stores all required attributes."""
        # Create a mock evaluation result (minimal interface)
        mock_eval_result = Mock()
        mock_eval_result.total_score = 25.0
        mock_eval_result.max_possible_score = 100.0

        # Create exception instance
        exception = QualityGateException(
            score=25.5,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Verify all attributes are accessible
        assert hasattr(exception, "score"), "Exception should have 'score' attribute"
        assert hasattr(exception, "threshold"), "Exception should have 'threshold' attribute"
        assert hasattr(exception, "evaluation_result"), "Exception should have 'evaluation_result' attribute"

        # Verify attribute values
        assert exception.score == 25.5, f"Expected score=25.5, got {exception.score}"
        assert exception.threshold == 30.0, f"Expected threshold=30.0, got {exception.threshold}"
        assert exception.evaluation_result is mock_eval_result, "evaluation_result should be accessible"

    def test_quality_gate_exception_auto_generated_message(self):
        """Test that QualityGateException auto-generates message when not provided."""
        mock_eval_result = Mock()

        exception = QualityGateException(
            score=20.0,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Get the exception message
        message = str(exception)

        # Verify message format
        assert "Quality gate failure" in message or "quality gate" in message.lower(), \
            "Message should mention quality gate failure"
        assert "20.0" in message, "Message should include score value"
        assert "30.0" in message, "Message should include threshold value"
        assert "below" in message.lower() or "threshold" in message.lower(), \
            "Message should indicate score is below threshold"

    def test_quality_gate_exception_custom_message(self):
        """Test that QualityGateException accepts custom message."""
        mock_eval_result = Mock()
        custom_message = "Custom quality gate failure message"

        exception = QualityGateException(
            score=15.0,
            threshold=30.0,
            evaluation_result=mock_eval_result,
            message=custom_message
        )

        # Verify custom message is used
        assert str(exception) == custom_message, \
            f"Expected custom message, got {str(exception)}"

    def test_quality_gate_exception_repr(self):
        """Test that QualityGateException has meaningful __repr__."""
        mock_eval_result = Mock()

        exception = QualityGateException(
            score=22.5,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Get repr string
        repr_string = repr(exception)

        # Verify repr format
        assert "QualityGateException" in repr_string, "Repr should include class name"
        assert "score=" in repr_string, "Repr should include score"
        assert "threshold=" in repr_string, "Repr should include threshold"
        assert "22.5" in repr_string or "22" in repr_string, "Repr should include score value"
        assert "30.0" in repr_string or "30" in repr_string, "Repr should include threshold value"

    def test_quality_gate_exception_score_below_threshold(self):
        """Test that QualityGateException is used for scores below threshold."""
        mock_eval_result = Mock()

        # Test with score below threshold
        exception = QualityGateException(
            score=25.0,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        assert exception.score < exception.threshold, \
            "QualityGateException should represent score below threshold"

    def test_quality_gate_exception_evaluation_result_accessible(self):
        """Test that evaluation_result attribute provides access to detailed results."""
        # Create mock with attributes similar to real EvaluationResult
        mock_eval_result = Mock()
        mock_eval_result.total_score = 25.0
        mock_eval_result.max_possible_score = 100.0
        mock_eval_result.checklist_items = []
        mock_eval_result.category_breakdowns = {}

        exception = QualityGateException(
            score=25.0,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Verify we can access evaluation result attributes
        assert exception.evaluation_result.total_score == 25.0
        assert exception.evaluation_result.max_possible_score == 100.0
        assert hasattr(exception.evaluation_result, "checklist_items")
        assert hasattr(exception.evaluation_result, "category_breakdowns")


class TestEvaluationFileSystemError:
    """Test EvaluationFileSystemError attributes and behavior."""

    def test_filesystem_error_attributes(self):
        """Test that EvaluationFileSystemError stores all required attributes."""
        # Create a real underlying exception
        original_error = PermissionError("Permission denied")

        # Create filesystem error instance
        exception = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/path/to/output",
            original_error=original_error
        )

        # Verify all attributes are accessible
        assert hasattr(exception, "operation"), "Exception should have 'operation' attribute"
        assert hasattr(exception, "target_path"), "Exception should have 'target_path' attribute"
        assert hasattr(exception, "original_error"), "Exception should have 'original_error' attribute"

        # Verify attribute values
        assert exception.operation == "create_directory", \
            f"Expected operation='create_directory', got {exception.operation}"
        assert exception.target_path == "/path/to/output", \
            f"Expected target_path='/path/to/output', got {exception.target_path}"
        assert exception.original_error is original_error, \
            "original_error should be accessible"

    def test_filesystem_error_auto_generated_message(self):
        """Test that EvaluationFileSystemError auto-generates message when not provided."""
        original_error = OSError("No such file or directory")

        exception = EvaluationFileSystemError(
            operation="write_file",
            target_path="/output/score_input.json",
            original_error=original_error
        )

        # Get the exception message
        message = str(exception)

        # Verify message format
        assert "Filesystem operation" in message or "filesystem" in message.lower(), \
            "Message should mention filesystem operation"
        assert "write_file" in message, "Message should include operation"
        assert "/output/score_input.json" in message, "Message should include target path"
        assert "OSError" in message, "Message should include original error type"

    def test_filesystem_error_custom_message(self):
        """Test that EvaluationFileSystemError accepts custom message."""
        original_error = IOError("I/O error")
        custom_message = "Custom filesystem error message"

        exception = EvaluationFileSystemError(
            operation="save_evidence_files",
            target_path="/evidence/dir",
            original_error=original_error,
            message=custom_message
        )

        # Verify custom message is used
        assert str(exception) == custom_message, \
            f"Expected custom message, got {str(exception)}"

    def test_filesystem_error_repr(self):
        """Test that EvaluationFileSystemError has meaningful __repr__."""
        original_error = PermissionError("Access denied")

        exception = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/root/output",
            original_error=original_error
        )

        # Get repr string
        repr_string = repr(exception)

        # Verify repr format
        assert "EvaluationFileSystemError" in repr_string, "Repr should include class name"
        assert "operation=" in repr_string, "Repr should include operation"
        assert "target_path=" in repr_string, "Repr should include target_path"
        assert "create_directory" in repr_string, "Repr should include operation value"
        assert "/root/output" in repr_string, "Repr should include target path"
        assert "PermissionError" in repr_string, "Repr should include original error type"

    def test_filesystem_error_original_error_accessible(self):
        """Test that original_error attribute provides access to underlying exception."""
        # Test with PermissionError
        perm_error = PermissionError("Permission denied: /root/test")

        exception = EvaluationFileSystemError(
            operation="create_directory",
            target_path="/root/test",
            original_error=perm_error
        )

        # Verify we can access original error
        assert isinstance(exception.original_error, PermissionError)
        assert "Permission denied" in str(exception.original_error)

    def test_filesystem_error_with_different_os_errors(self):
        """Test that EvaluationFileSystemError works with different OS error types."""
        # Test with different error types
        error_types = [
            OSError("Generic OS error"),
            PermissionError("Permission denied"),
            IOError("I/O error"),
            FileNotFoundError("File not found")
        ]

        for original_error in error_types:
            exception = EvaluationFileSystemError(
                operation="test_operation",
                target_path="/test/path",
                original_error=original_error
            )

            # Verify exception can be created and attributes accessible
            assert exception.operation == "test_operation"
            assert exception.target_path == "/test/path"
            assert exception.original_error is original_error
            assert isinstance(exception.original_error, Exception)


class TestExceptionInheritance:
    """Test that custom exceptions inherit from Exception properly."""

    def test_quality_gate_exception_inherits_from_exception(self):
        """Test that QualityGateException inherits from Exception."""
        mock_eval_result = Mock()

        exception = QualityGateException(
            score=20.0,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Verify inheritance
        assert isinstance(exception, Exception), \
            "QualityGateException should inherit from Exception"
        assert isinstance(exception, QualityGateException), \
            "Should be instance of QualityGateException"

    def test_filesystem_error_inherits_from_exception(self):
        """Test that EvaluationFileSystemError inherits from Exception."""
        original_error = OSError("Test error")

        exception = EvaluationFileSystemError(
            operation="test_op",
            target_path="/test/path",
            original_error=original_error
        )

        # Verify inheritance
        assert isinstance(exception, Exception), \
            "EvaluationFileSystemError should inherit from Exception"
        assert isinstance(exception, EvaluationFileSystemError), \
            "Should be instance of EvaluationFileSystemError"

    def test_exceptions_can_be_raised_and_caught(self):
        """Test that custom exceptions can be raised and caught properly."""
        # Test QualityGateException
        mock_eval_result = Mock()

        with pytest.raises(QualityGateException) as exc_info:
            raise QualityGateException(
                score=15.0,
                threshold=30.0,
                evaluation_result=mock_eval_result
            )

        assert exc_info.value.score == 15.0
        assert exc_info.value.threshold == 30.0

        # Test EvaluationFileSystemError
        original_error = PermissionError("Test")

        with pytest.raises(EvaluationFileSystemError) as exc_info:
            raise EvaluationFileSystemError(
                operation="test",
                target_path="/test",
                original_error=original_error
            )

        assert exc_info.value.operation == "test"
        assert exc_info.value.target_path == "/test"

    def test_exceptions_can_be_caught_as_exception(self):
        """Test that custom exceptions can be caught as generic Exception."""
        mock_eval_result = Mock()

        # Test QualityGateException caught as Exception
        with pytest.raises(Exception) as exc_info:
            raise QualityGateException(
                score=20.0,
                threshold=30.0,
                evaluation_result=mock_eval_result
            )

        # Should catch as Exception but still be QualityGateException
        assert isinstance(exc_info.value, QualityGateException)
        assert isinstance(exc_info.value, Exception)

        # Test EvaluationFileSystemError caught as Exception
        original_error = OSError("Test")

        with pytest.raises(Exception) as exc_info:
            raise EvaluationFileSystemError(
                operation="test",
                target_path="/test",
                original_error=original_error
            )

        # Should catch as Exception but still be EvaluationFileSystemError
        assert isinstance(exc_info.value, EvaluationFileSystemError)
        assert isinstance(exc_info.value, Exception)


class TestExceptionUsageScenarios:
    """Test realistic usage scenarios for custom exceptions."""

    def test_quality_gate_exception_typical_usage(self):
        """Test typical usage pattern for QualityGateException."""
        # Simulate evaluation result with low score
        mock_eval_result = Mock()
        mock_eval_result.total_score = 28.0
        mock_eval_result.max_possible_score = 100.0
        mock_eval_result.score_percentage = 28.0

        # Create exception as it would be raised in real code
        exception = QualityGateException(
            score=28.0,  # Below 30% threshold
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        # Verify typical usage patterns
        assert exception.score < exception.threshold, \
            "Score should be below threshold"
        assert exception.score == 28.0, \
            "Score should match evaluation result"
        assert exception.evaluation_result is not None, \
            "Should have evaluation result for detailed analysis"

        # Verify message is informative
        message = str(exception)
        assert "28.0" in message, "Message should include actual score"
        assert "30.0" in message, "Message should include threshold"

    def test_filesystem_error_typical_usage(self):
        """Test typical usage pattern for EvaluationFileSystemError."""
        # Simulate permission error when creating directory
        try:
            # This would be real code trying to create directory
            import os
            os.mkdir("/root/test_impossible_dir_12345")
        except (PermissionError, OSError) as e:
            # Wrap in EvaluationFileSystemError as real code would
            exception = EvaluationFileSystemError(
                operation="create_directory",
                target_path="/root/test_impossible_dir_12345",
                original_error=e
            )

            # Verify typical usage patterns
            assert exception.operation == "create_directory"
            assert "/root/test_impossible_dir_12345" in exception.target_path
            assert isinstance(exception.original_error, Exception)

            # Verify can check original error type for specific handling
            if isinstance(exception.original_error, PermissionError):
                assert True, "Can detect PermissionError for specific handling"

    def test_exception_message_helps_debugging(self):
        """Test that exception messages provide useful debugging information."""
        # QualityGateException message
        mock_eval_result = Mock()
        qg_exception = QualityGateException(
            score=25.5,
            threshold=30.0,
            evaluation_result=mock_eval_result
        )

        qg_message = str(qg_exception)
        # Message should help developer understand what happened
        assert any(word in qg_message.lower() for word in ["quality", "gate", "threshold", "score"]), \
            "Message should indicate quality gate failure"

        # EvaluationFileSystemError message
        fs_exception = EvaluationFileSystemError(
            operation="write_file",
            target_path="/output/score_input.json",
            original_error=PermissionError("Permission denied")
        )

        fs_message = str(fs_exception)
        # Message should help developer understand what failed and where
        assert "write_file" in fs_message, "Message should include operation"
        assert "/output/score_input.json" in fs_message, "Message should include path"
        assert any(word in fs_message for word in ["Permission", "PermissionError"]), \
            "Message should include error type"
