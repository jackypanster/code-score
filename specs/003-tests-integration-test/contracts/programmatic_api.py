"""
Contract specification for the programmatic evaluation API.

This file defines the expected function signature and behavior contract.
Implementation will be in src/cli/evaluate.py.

Contract tests in tests/contract/test_programmatic_api_contract.py will validate
compliance with this specification.
"""

from pathlib import Path
from typing import Literal

from src.cli.models import EvaluationResult, ValidationResult


def evaluate_submission(
    submission_file: str | Path,
    output_dir: str | Path = "output",
    format: Literal["json", "markdown", "both"] = "both",
    checklist_config: str | Path | None = None,
    evidence_dir: str | Path = "evidence",
    validate_only: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> ValidationResult | EvaluationResult:
    """
    Programmatically evaluate a repository submission against the quality checklist.

    This function provides a Python API for the evaluation workflow, enabling
    integration tests and internal tooling to trigger evaluations without spawning
    CLI processes or parsing terminal output.

    Args:
        submission_file: Path to the submission.json file to evaluate (required)
        output_dir: Directory for generated output files (default: "output")
        format: Output format - "json", "markdown", or "both" (default: "both")
        checklist_config: Optional path to custom checklist YAML configuration
        evidence_dir: Directory name for evidence files, relative to output_dir (default: "evidence")
        validate_only: If True, only validate input without generating outputs (default: False)
        verbose: Enable DEBUG-level logging (default: False)
        quiet: Suppress all logs except WARNING and above (default: False)

    Returns:
        ValidationResult: If validate_only=True, returns validation details
            - valid: bool (overall validation status)
            - items_checked: List[str] (validation items performed)
            - passed_checks: List[str] (checks that passed)
            - warnings: List[str] (non-fatal warnings)

        EvaluationResult: If validate_only=False, returns evaluation outcome
            - success: bool (evaluation completed successfully)
            - total_score: float (actual score achieved)
            - max_possible_score: float (maximum possible score)
            - grade: str (letter grade A-F)
            - generated_files: List[str] (absolute paths to output files)
            - evidence_files: Dict[str, str] (evidence key → file path mapping)
            - warnings: List[str] (evaluation warnings)

    Raises:
        FileNotFoundError:
            - If submission_file does not exist
            - If checklist_config is provided but does not exist

        ValueError:
            - If submission_file contains invalid JSON
            - If submission structure is missing required sections (repository, metrics)
            - If checklist configuration validation fails

        EvaluationFileSystemError:
            - If output_dir cannot be created (wrapped OSError/PermissionError)
            - If evidence_dir cannot be created
            - If output files cannot be written
            Attributes:
                - operation: str (e.g., "create_directory", "write_file")
                - target_path: str (absolute path that failed)
                - original_error: Exception (underlying OS error)

        QualityGateException:
            - If evaluation completes but score < 30% threshold
            Attributes:
                - score: float (actual evaluation score percentage)
                - threshold: float (quality gate threshold, 30.0)
                - evaluation_result: EvaluationResult (full evaluation details)

    Behavior Notes:
        - Logging: Uses Python logging module, respects verbose/quiet flags
            - verbose=True: Sets log level to DEBUG
            - normal: Sets log level to INFO
            - quiet=True: Sets log level to WARNING
        - Path Handling: All returned file paths are absolute
        - Side Effects: Creates directories, writes files (unless validate_only=True)
        - Backward Compatibility: Behavior MUST match CLI command output when called
          with equivalent parameters

    Examples:
        # Validate submission without generating outputs
        >>> result = evaluate_submission("output/submission.json", validate_only=True)
        >>> assert result.valid
        >>> print(result.items_checked)
        ['submission_structure', 'checklist_config', 'required_sections']

        # Full evaluation with custom output directory
        >>> result = evaluate_submission(
        ...     "output/submission.json",
        ...     output_dir="results",
        ...     format="json",
        ...     verbose=True
        ... )
        >>> assert result.success
        >>> assert result.grade in ["A", "B", "C", "D", "F"]
        >>> assert "results/score_input.json" in result.generated_files

        # Handle quality gate failure
        >>> from src.cli.exceptions import QualityGateException
        >>> try:
        ...     result = evaluate_submission("low_score_submission.json")
        ... except QualityGateException as e:
        ...     print(f"Quality gate failed: {e.score:.1f}% < {e.threshold:.1f}%")
        ...     # Can still access full evaluation details
        ...     for item in e.evaluation_result.checklist_items:
        ...         if item.evaluation_status == "unmet":
        ...             print(f"  Unmet: {item.description}")

        # Handle filesystem errors
        >>> from src.cli.exceptions import EvaluationFileSystemError
        >>> try:
        ...     result = evaluate_submission(
        ...         "submission.json",
        ...         output_dir="/read-only/path"
        ...     )
        ... except EvaluationFileSystemError as e:
        ...     print(f"Failed to {e.operation} at {e.target_path}")
        ...     if isinstance(e.original_error, PermissionError):
        ...         print("Check directory permissions")
    """
    raise NotImplementedError(
        "This is a contract specification. "
        "Implementation will be in src/cli/evaluate.py::evaluate_submission()"
    )
