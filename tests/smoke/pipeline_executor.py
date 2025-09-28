"""
Pipeline executor utility for smoke test suite.

This module handles the execution of the code analysis pipeline script
and provides utilities for managing subprocess execution.
"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from .models import SmokeTestExecution

# Configure logging
logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails."""
    pass


class PipelineTimeoutError(PipelineExecutionError):
    """Raised when pipeline execution times out."""
    pass


def execute_pipeline(
    repository_url: str,
    working_directory: Path,
    timeout_seconds: int = 300,
    enable_checklist: bool = True,
    generate_llm_report: bool = False
) -> SmokeTestExecution:
    """
    Execute the code analysis pipeline script.

    Args:
        repository_url: Git repository URL to analyze
        working_directory: Project root directory
        timeout_seconds: Maximum execution time in seconds
        enable_checklist: Whether to enable checklist evaluation
        generate_llm_report: Whether to generate LLM reports

    Returns:
        SmokeTestExecution object with execution details

    Raises:
        PipelineExecutionError: If pipeline execution fails
        PipelineTimeoutError: If execution times out
    """
    # Create execution tracking object
    execution = SmokeTestExecution(
        repository_url=repository_url,
        working_directory=working_directory,
        execution_start_time=datetime.now()
    )

    # Build command arguments
    script_path = working_directory / "scripts" / "run_metrics.sh"
    if not script_path.exists():
        raise PipelineExecutionError(f"Pipeline script not found: {script_path}")

    args = _build_command_args(
        script_path=script_path,
        repository_url=repository_url,
        enable_checklist=enable_checklist,
        generate_llm_report=generate_llm_report
    )

    logger.info(f"Executing pipeline: {' '.join(str(arg) for arg in args)}")

    try:
        # Execute the pipeline script
        result = subprocess.run(
            args,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        # Mark execution as completed
        execution.mark_completed(result.returncode)

        logger.info(f"Pipeline completed with exit code: {result.returncode}")
        logger.debug(f"Pipeline stdout: {result.stdout}")

        if result.returncode != 0:
            error_msg = f"Pipeline failed with exit code {result.returncode}"
            if result.stderr:
                error_msg += f": {result.stderr}"
            logger.error(error_msg)
            raise PipelineExecutionError(error_msg)

        return execution

    except subprocess.TimeoutExpired as e:
        execution.mark_completed(-1)  # Timeout exit code
        error_msg = f"Pipeline execution timed out after {timeout_seconds} seconds"
        logger.error(error_msg)
        raise PipelineTimeoutError(error_msg) from e

    except subprocess.SubprocessError as e:
        execution.mark_completed(-1)
        error_msg = f"Pipeline execution failed: {e}"
        logger.error(error_msg)
        raise PipelineExecutionError(error_msg) from e


def _build_command_args(
    script_path: Path,
    repository_url: str,
    enable_checklist: bool,
    generate_llm_report: bool
) -> List[str]:
    """Build command line arguments for pipeline script."""
    args = [str(script_path), repository_url]

    # Always explicitly set checklist behavior since script defaults to enabled
    if enable_checklist:
        args.append("--enable-checklist")
    else:
        args.append("--disable-checklist")

    # Only include the flag when we want to generate LLM reports
    # Omit the flag entirely when false (default behavior)
    if generate_llm_report:
        args.append("--generate-llm-report")

    return args


def validate_pipeline_environment(working_directory: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that the pipeline execution environment is ready.

    Args:
        working_directory: Project root directory

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check that working directory exists
    if not working_directory.exists():
        return False, f"Working directory does not exist: {working_directory}"

    if not working_directory.is_dir():
        return False, f"Working directory is not a directory: {working_directory}"

    # Check that pipeline script exists
    script_path = working_directory / "scripts" / "run_metrics.sh"
    if not script_path.exists():
        return False, f"Pipeline script not found: {script_path}"

    # Check that script is executable (on Unix systems)
    if not script_path.is_file():
        return False, f"Pipeline script is not a file: {script_path}"

    # Check that output directory can be created
    output_dir = working_directory / "output"
    try:
        output_dir.mkdir(exist_ok=True)
    except (OSError, PermissionError) as e:
        return False, f"Cannot create output directory: {e}"

    return True, None


def cleanup_pipeline_outputs(working_directory: Path) -> None:
    """
    Clean up pipeline output files from previous runs.

    Args:
        working_directory: Project root directory
    """
    output_dir = working_directory / "output"
    if not output_dir.exists():
        return

    # List of files to clean up
    cleanup_files = [
        "submission.json",
        "score_input.json",
        "evaluation_report.md"
    ]

    for filename in cleanup_files:
        file_path = output_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"Cleaned up output file: {filename}")
            except OSError as e:
                logger.warning(f"Failed to clean up {filename}: {e}")


def check_pipeline_script_availability() -> bool:
    """
    Check if the pipeline script is available and executable.

    Returns:
        True if script is available, False otherwise
    """
    try:
        # Try to get help from the script to verify it's working
        result = subprocess.run(
            ["./scripts/run_metrics.sh", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_pipeline_version_info(working_directory: Path) -> Optional[str]:
    """
    Get version information from the pipeline script.

    Args:
        working_directory: Project root directory

    Returns:
        Version string if available, None otherwise
    """
    script_path = working_directory / "scripts" / "run_metrics.sh"
    if not script_path.exists():
        return None

    try:
        result = subprocess.run(
            [str(script_path), "--version"],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass

    return None