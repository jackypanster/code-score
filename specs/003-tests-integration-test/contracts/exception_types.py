"""
Contract specification for custom exception types.

This file defines the expected exception class structures and behaviors.
Implementation will be in src/cli/exceptions.py.

Contract tests in tests/contract/test_exception_contracts.py will validate
compliance with this specification.
"""

from typing import Any, Dict


class QualityGateException(Exception):
    """
    Raised when evaluation completes successfully but fails the quality gate threshold.

    This exception signals a business logic failure (low code quality score),
    not a system error. Callers may choose to handle this differently from
    other exceptions (e.g., automated PR checks may expect quality gate failures).

    Attributes:
        score: float
            The actual evaluation score percentage (0.0 - 100.0)
            Example: 25.5 means 25.5% score

        threshold: float
            The quality gate threshold that was not met
            Default: 30.0 (hardcoded in evaluation logic)

        evaluation_result: EvaluationResult
            Complete evaluation result from ChecklistEvaluator
            Contains checklist items, category breakdowns, warnings, etc.
            Type: src.metrics.models.evaluation_result.EvaluationResult

    Example:
        >>> try:
        ...     result = evaluate_submission("low_score_submission.json")
        ... except QualityGateException as e:
        ...     assert e.score < e.threshold
        ...     assert e.score < 30.0
        ...     print(f"Score: {e.score:.1f}%, Threshold: {e.threshold:.1f}%")
        ...     # Access detailed evaluation results
        ...     for item in e.evaluation_result.checklist_items:
        ...         if item.evaluation_status == "unmet":
        ...             print(f"  Unmet: {item.description}")
    """

    def __init__(
        self,
        score: float,
        threshold: float,
        evaluation_result: Any,  # Type: EvaluationResult from ChecklistEvaluator
        message: str | None = None,
    ):
        """
        Initialize QualityGateException.

        Args:
            score: Actual evaluation score percentage
            threshold: Quality gate threshold
            evaluation_result: Complete evaluation result from ChecklistEvaluator
            message: Optional custom error message (auto-generated if None)
        """
        self.score = score
        self.threshold = threshold
        self.evaluation_result = evaluation_result

        if message is None:
            message = (
                f"Quality gate failure: score {score:.1f}% below threshold {threshold:.1f}%"
            )

        super().__init__(message)

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"QualityGateException(score={self.score:.1f}, "
            f"threshold={self.threshold:.1f}, "
            f"evaluation_result=<EvaluationResult>)"
        )


class EvaluationFileSystemError(Exception):
    """
    Raised when filesystem operations fail during evaluation.

    This exception wraps underlying OS errors (OSError, PermissionError, IOError)
    with additional context about the failed operation and target path.

    Attributes:
        operation: str
            Description of the operation that failed
            Examples: "create_directory", "write_file", "create_evidence_dir"

        target_path: str
            Absolute path to the file or directory that failed
            Example: "/absolute/path/to/output/score_input.json"

        original_error: Exception
            The underlying OS exception that was wrapped
            Typically: OSError, PermissionError, IOError

    Example:
        >>> try:
        ...     result = evaluate_submission(
        ...         "submission.json",
        ...         output_dir="/read-only/path"
        ...     )
        ... except EvaluationFileSystemError as e:
        ...     print(f"Operation: {e.operation}")
        ...     print(f"Target: {e.target_path}")
        ...     print(f"Original error: {e.original_error}")
        ...     # Check error type for specific handling
        ...     if isinstance(e.original_error, PermissionError):
        ...         print("Permission denied - check directory permissions")
        ...     elif isinstance(e.original_error, OSError):
        ...         if e.original_error.errno == 28:  # ENOSPC
        ...             print("Disk full - free up space")
    """

    def __init__(
        self,
        operation: str,
        target_path: str,
        original_error: Exception,
        message: str | None = None,
    ):
        """
        Initialize EvaluationFileSystemError.

        Args:
            operation: Description of the failed operation
            target_path: Path that failed (should be absolute)
            original_error: The underlying OS exception
            message: Optional custom error message (auto-generated if None)
        """
        self.operation = operation
        self.target_path = target_path
        self.original_error = original_error

        if message is None:
            message = (
                f"Filesystem operation '{operation}' failed for '{target_path}': "
                f"{type(original_error).__name__}: {original_error}"
            )

        super().__init__(message)

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"EvaluationFileSystemError(operation='{self.operation}', "
            f"target_path='{self.target_path}', "
            f"original_error={type(self.original_error).__name__})"
        )


# Contract validation utilities
def validate_quality_gate_exception_contract(exc: QualityGateException) -> bool:
    """
    Validate that a QualityGateException instance meets the contract.

    Args:
        exc: Exception instance to validate

    Returns:
        True if contract is satisfied, raises AssertionError otherwise

    Contract Requirements:
        - Must inherit from Exception
        - Must have 'score' attribute (float)
        - Must have 'threshold' attribute (float)
        - Must have 'evaluation_result' attribute
        - score must be less than threshold
        - score must be between 0 and 100
    """
    assert isinstance(exc, Exception), "Must inherit from Exception"
    assert hasattr(exc, "score"), "Must have 'score' attribute"
    assert hasattr(exc, "threshold"), "Must have 'threshold' attribute"
    assert hasattr(exc, "evaluation_result"), "Must have 'evaluation_result' attribute"

    assert isinstance(exc.score, (int, float)), "score must be numeric"
    assert isinstance(exc.threshold, (int, float)), "threshold must be numeric"
    assert exc.score < exc.threshold, "score must be below threshold"
    assert 0 <= exc.score <= 100, "score must be percentage (0-100)"

    return True


def validate_filesystem_error_contract(exc: EvaluationFileSystemError) -> bool:
    """
    Validate that an EvaluationFileSystemError instance meets the contract.

    Args:
        exc: Exception instance to validate

    Returns:
        True if contract is satisfied, raises AssertionError otherwise

    Contract Requirements:
        - Must inherit from Exception
        - Must have 'operation' attribute (str)
        - Must have 'target_path' attribute (str)
        - Must have 'original_error' attribute (Exception)
        - operation must be non-empty
        - target_path must be non-empty
        - original_error must be an Exception instance
    """
    assert isinstance(exc, Exception), "Must inherit from Exception"
    assert hasattr(exc, "operation"), "Must have 'operation' attribute"
    assert hasattr(exc, "target_path"), "Must have 'target_path' attribute"
    assert hasattr(exc, "original_error"), "Must have 'original_error' attribute"

    assert isinstance(exc.operation, str), "operation must be string"
    assert isinstance(exc.target_path, str), "target_path must be string"
    assert isinstance(exc.original_error, Exception), "original_error must be Exception"

    assert exc.operation.strip(), "operation must be non-empty"
    assert exc.target_path.strip(), "target_path must be non-empty"

    return True
