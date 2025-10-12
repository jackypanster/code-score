"""CLI evaluate command for running checklist evaluation on submission.json files."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import click

from ..metrics.checklist_evaluator import ChecklistEvaluator
from ..metrics.checklist_loader import ChecklistLoader
from ..metrics.evidence_tracker import EvidenceTracker
from ..metrics.models.evaluation_result import RepositoryInfo
from ..metrics.scoring_mapper import ScoringMapper
from .exceptions import EvaluationFileSystemError, QualityGateException
from .models import EvaluationResult, ValidationResult

logger = logging.getLogger(__name__)


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
    # Configure logging level (quiet takes precedence over verbose)
    if quiet:
        logger.setLevel(logging.WARNING)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Convert paths to Path objects
    submission_file = Path(submission_file)
    output_dir = Path(output_dir)
    if checklist_config:
        checklist_config = Path(checklist_config)
    evidence_dir_path = Path(evidence_dir)

    start_time = datetime.now()

    try:
        # Initialize components
        logger.debug("🔍 Initializing checklist evaluation...")

        # Load checklist configuration
        if checklist_config:
            loader = ChecklistLoader(str(checklist_config))
        else:
            loader = ChecklistLoader()

        logger.debug("📋 Loaded checklist configuration")

        # Validate checklist configuration
        validation = loader.validate_checklist_config()
        if not validation["valid"]:
            errors = "\n".join(f"   • {error}" for error in validation["errors"])
            raise ValueError(
                f"Checklist configuration validation failed:\n{errors}"
            )

        stats = validation["statistics"]
        logger.debug(f"   ✅ {stats['total_checklist_items']} items, {stats['total_max_points']} total points")

        # Load and validate submission file
        logger.debug(f"📄 Loading submission file: {submission_file}")

        try:
            with open(submission_file, encoding='utf-8') as f:
                submission_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in submission file: {e}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Submission file not found: {submission_file}")
        except Exception as e:
            raise ValueError(f"Error reading submission file: {e}")

        # Basic submission structure validation
        required_sections = ["repository", "metrics"]
        missing_sections = [section for section in required_sections if section not in submission_data]
        if missing_sections:
            raise ValueError(
                f"Missing required sections in submission: {', '.join(missing_sections)}"
            )

        if validate_only:
            logger.info("✅ Submission file validation passed")
            # Include checklist validation warnings if any
            validation_warnings = validation.get("warnings", [])
            return ValidationResult(
                valid=True,
                items_checked=["submission_structure", "checklist_config", "required_sections"],
                passed_checks=["submission_structure", "checklist_config", "required_sections"],
                warnings=validation_warnings
            )

        # Initialize evaluator and evidence tracker
        evaluator = ChecklistEvaluator(str(checklist_config) if checklist_config else None)
        evidence_tracker = EvidenceTracker(str(output_dir / evidence_dir_path))

        logger.debug("⚙️  Running evaluation...")

        # Run evaluation
        evaluation_result = evaluator.evaluate_from_dict(submission_data, str(submission_file))

        # Track evidence
        evidence_tracker.track_evaluation_evidence(evaluation_result)

        # Create repository info
        repo_data = submission_data.get("repository", {})
        repository_info = RepositoryInfo(
            url=repo_data.get("url", "unknown"),
            commit_sha=repo_data.get("commit", "unknown"),
            primary_language=repo_data.get("language", "unknown"),
            analysis_timestamp=datetime.fromisoformat(
                repo_data.get("timestamp", datetime.now().isoformat()).replace('Z', '+00:00')
            ),
            metrics_source=str(submission_file)
        )

        # Generate score input
        mapper = ScoringMapper(str(output_dir))
        score_input = mapper.map_to_score_input(
            evaluation_result=evaluation_result,
            repository_info=repository_info,
            submission_path=str(submission_file),
            evidence_base_path=str(evidence_dir_path)
        )

        # Create output directory
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError, IOError) as e:
            raise EvaluationFileSystemError(
                operation="create_directory",
                target_path=str(output_dir.absolute()),
                original_error=e
            )

        generated_files = []

        # Save evidence files first
        logger.debug("📁 Saving evidence files...")

        try:
            evidence_files = evidence_tracker.save_evidence_files()
        except (OSError, PermissionError, IOError) as e:
            raise EvaluationFileSystemError(
                operation="save_evidence_files",
                target_path=str(output_dir / evidence_dir_path),
                original_error=e
            )

        # Update evidence paths in score input before generating outputs
        mapper.update_evidence_paths_with_generated_files(score_input, evidence_files)

        # Generate outputs based on format selection (after evidence paths are updated)
        if format in ['json', 'both']:
            logger.debug("📝 Generating score_input.json...")

            json_output_path = output_dir / "score_input.json"
            try:
                mapper.generate_score_input_json(score_input, str(json_output_path))
                generated_files.append(str(json_output_path.absolute()))
            except (OSError, PermissionError, IOError) as e:
                raise EvaluationFileSystemError(
                    operation="write_file",
                    target_path=str(json_output_path.absolute()),
                    original_error=e
                )

        if format in ['markdown', 'both']:
            logger.debug("📝 Generating evaluation report...")

            markdown_output_path = output_dir / "evaluation_report.md"
            try:
                mapper.generate_markdown_report(score_input, str(markdown_output_path))
                generated_files.append(str(markdown_output_path.absolute()))
            except (OSError, PermissionError, IOError) as e:
                raise EvaluationFileSystemError(
                    operation="write_file",
                    target_path=str(markdown_output_path.absolute()),
                    original_error=e
                )

        # Generate final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n🎉 Evaluation completed successfully!")
        logger.info(f"📊 Score: {evaluation_result.total_score:.1f}/{evaluation_result.max_possible_score} ({evaluation_result.score_percentage:.1f}%)")

        # Show category breakdown
        logger.info("\n📈 Category Breakdown:")
        for dimension, breakdown in evaluation_result.category_breakdowns.items():
            percentage = breakdown.percentage
            grade = get_letter_grade(percentage)
            logger.info(f"   {dimension.replace('_', ' ').title()}: {breakdown.actual_points:.1f}/{breakdown.max_points} ({percentage:.1f}%, Grade: {grade})")

        # Show status distribution
        met_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "met")
        partial_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "partial")
        unmet_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "unmet")

        logger.info(f"\n📋 Items: {met_count} met, {partial_count} partial, {unmet_count} unmet")

        if evaluation_result.evaluation_metadata.warnings:
            logger.warning(f"\n⚠️  Warnings ({len(evaluation_result.evaluation_metadata.warnings)}):")
            for warning in evaluation_result.evaluation_metadata.warnings:
                logger.warning(f"   • {warning}")

        logger.info("\n📁 Generated Files:")
        for file_path in generated_files:
            logger.info(f"   • {file_path}")

        logger.info(f"📁 Evidence Files: {len(evidence_files)} files in {output_dir / evidence_dir_path}")
        logger.info(f"⏱️  Processing Time: {duration:.2f} seconds")

        # Quality gate check - raise exception if score below threshold
        if evaluation_result.score_percentage < 30:
            raise QualityGateException(
                score=evaluation_result.score_percentage,
                threshold=30.0,
                evaluation_result=evaluation_result
            )

        # Calculate letter grade for return object
        score_percentage = evaluation_result.score_percentage
        if score_percentage >= 90:
            letter_grade = "A"
        elif score_percentage >= 80:
            letter_grade = "B"
        elif score_percentage >= 70:
            letter_grade = "C"
        elif score_percentage >= 60:
            letter_grade = "D"
        else:
            letter_grade = "F"

        # Convert evidence_files dict to format expected by EvaluationResult
        evidence_files_dict = {k: str(Path(v).absolute()) for k, v in evidence_files.items()}

        return EvaluationResult(
            success=True,
            total_score=evaluation_result.total_score,
            max_possible_score=evaluation_result.max_possible_score,
            grade=letter_grade,
            generated_files=generated_files,
            evidence_files=evidence_files_dict,
            warnings=list(evaluation_result.evaluation_metadata.warnings)
        )

    except QualityGateException:
        # Re-raise quality gate exceptions (don't catch and suppress)
        raise
    except EvaluationFileSystemError:
        # Re-raise filesystem errors (don't catch and suppress)
        raise
    except FileNotFoundError:
        # Re-raise file not found errors (don't catch and suppress)
        raise
    except ValueError:
        # Re-raise validation errors (don't catch and suppress)
        raise
    except Exception as e:
        # Wrap unexpected errors in ValueError for consistency
        raise ValueError(f"Unexpected error during evaluation: {e}")


class ClickHandler(logging.Handler):
    """Logging handler that outputs via click.echo() for consistent CLI formatting."""

    def emit(self, record):
        """Emit a log record via click.echo()."""
        try:
            msg = self.format(record)
            # Send WARNING and above to stderr, INFO and DEBUG to stdout
            click.echo(msg, err=(record.levelno >= logging.WARNING))
        except Exception:
            self.handleError(record)


@click.command()
@click.argument('submission_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    default='output',
    help='Output directory for generated files (default: output)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'markdown', 'both']),
    default='both',
    help='Output format: json, markdown, or both (default: both)'
)
@click.option(
    '--checklist-config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to checklist configuration YAML file'
)
@click.option(
    '--evidence-dir', '-e',
    type=click.Path(path_type=Path),
    default='evidence',
    help='Directory for evidence files (default: evidence)'
)
@click.option(
    '--validate-only', '-v',
    is_flag=True,
    help='Only validate input without generating outputs'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress output except errors'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Show detailed evaluation progress'
)
def evaluate(
    submission_file: Path,
    output_dir: Path,
    format: str,
    checklist_config: Path | None,
    evidence_dir: Path,
    validate_only: bool,
    quiet: bool,
    verbose: bool
):
    """
    Evaluate a repository submission against the quality checklist.

    SUBMISSION_FILE: Path to the submission.json file to evaluate.

    This command processes a repository metrics submission and evaluates it against
    the 11-item quality checklist, generating structured output for downstream
    processing or human review.

    Examples:
        # Basic evaluation
        code-score evaluate submission.json

        # Custom output directory and format
        code-score evaluate submission.json -o results -f json

        # Validation only
        code-score evaluate submission.json -v

        # Verbose evaluation with custom checklist
        code-score evaluate submission.json -c custom_checklist.yaml --verbose
    """
    # Configure logging to output via click.echo() for CLI
    cli_logger = logging.getLogger("src.cli.evaluate")

    # Remove any existing handlers to avoid duplicates
    cli_logger.handlers.clear()

    # Add ClickHandler for CLI output
    handler = ClickHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    cli_logger.addHandler(handler)

    # Prevent propagation to avoid duplicate output
    cli_logger.propagate = False

    # Delegate to programmatic API with exception translation for CLI
    try:
        result = evaluate_submission(
            submission_file=submission_file,
            output_dir=output_dir,
            format=format,
            checklist_config=checklist_config,
            evidence_dir=evidence_dir,
            validate_only=validate_only,
            verbose=verbose,
            quiet=quiet
        )

        # Generate CLI output from return object
        # Note: Logging messages were already output during evaluation via ClickHandler
        # This section adds final summary output only

    except QualityGateException as e:
        click.echo(f"⚠️  Quality gate: Score {e.score:.1f}% below {e.threshold:.1f}% threshold", err=True)
        sys.exit(2)
    except EvaluationFileSystemError as e:
        click.echo(f"❌ Filesystem error: {e.operation} failed for {e.target_path}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"❌ Validation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


def get_letter_grade(percentage: float) -> str:
    """Get letter grade for percentage."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


# Allow running as standalone script for testing
def main():
    """Main entry point for standalone execution."""
    evaluate()


if __name__ == '__main__':
    main()
