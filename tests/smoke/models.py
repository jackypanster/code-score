"""
Data models for smoke test suite.

This module defines the data structures used throughout the smoke test
implementation for tracking execution state and validation results.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SmokeTestExecution:
    """Represents a single execution of the smoke test workflow."""

    repository_url: str
    working_directory: Path
    execution_start_time: datetime
    execution_end_time: datetime | None = None
    pipeline_exit_code: int | None = None
    pipeline_duration: float | None = None

    def __post_init__(self):
        """Validate data integrity after initialization."""
        if not self.repository_url:
            raise ValueError("repository_url must not be empty")

        if not self.working_directory.exists():
            raise ValueError(f"working_directory must exist: {self.working_directory}")

        if self.execution_end_time and self.execution_end_time < self.execution_start_time:
            raise ValueError("execution_end_time must be after execution_start_time")

    @property
    def is_complete(self) -> bool:
        """Check if execution has completed."""
        return self.execution_end_time is not None

    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.is_complete and self.pipeline_exit_code == 0

    def mark_completed(self, exit_code: int) -> None:
        """Mark execution as completed with given exit code."""
        self.execution_end_time = datetime.now()
        self.pipeline_exit_code = exit_code

        if self.execution_start_time and self.execution_end_time:
            duration = self.execution_end_time - self.execution_start_time
            self.pipeline_duration = duration.total_seconds()


@dataclass
class OutputArtifact:
    """Represents expected output files from the pipeline."""

    file_path: Path
    expected_name: str
    file_exists: bool = False
    file_size_bytes: int | None = None
    last_modified: datetime | None = None
    content_valid: bool = False

    def __post_init__(self):
        """Validate and update artifact information."""
        if not self.expected_name:
            raise ValueError("expected_name must not be empty")

        # Check if file exists and update metadata
        self.refresh()

    def refresh(self) -> None:
        """Refresh file metadata from filesystem."""
        self.file_exists = self.file_path.exists()

        if self.file_exists:
            stat = self.file_path.stat()
            self.file_size_bytes = stat.st_size
            self.last_modified = datetime.fromtimestamp(stat.st_mtime)

            # Basic content validation
            self.content_valid = self._validate_content()
        else:
            self.file_size_bytes = None
            self.last_modified = None
            self.content_valid = False

    def _validate_content(self) -> bool:
        """Perform basic content validation based on file type."""
        if not self.file_exists or self.file_size_bytes == 0:
            return False

        try:
            if self.expected_name.endswith('.json'):
                return self._validate_json_content()
            elif self.expected_name.endswith('.md'):
                return self._validate_markdown_content()
            else:
                # For other file types, just check that file is readable
                return self._validate_readable_content()
        except Exception:
            return False

    def _validate_json_content(self) -> bool:
        """Validate JSON file content."""
        try:
            import json
            with open(self.file_path) as f:
                json.load(f)
            return True
        except (OSError, json.JSONDecodeError):
            return False

    def _validate_markdown_content(self) -> bool:
        """Validate Markdown file content."""
        try:
            with open(self.file_path, encoding='utf-8') as f:
                content = f.read()
            # Basic check: file should contain readable text
            # Note: We don't use isprintable() because valid Markdown contains newlines
            return len(content.strip()) > 0
        except (OSError, UnicodeDecodeError):
            return False

    def _validate_readable_content(self) -> bool:
        """Validate that file contains readable content."""
        try:
            with open(self.file_path, encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB
            return len(content.strip()) > 0
        except (OSError, UnicodeDecodeError):
            return False


@dataclass
class ValidationResult:
    """Represents overall smoke test validation outcome."""

    test_passed: bool
    pipeline_successful: bool
    all_files_present: bool
    execution_summary: str
    error_message: str | None = None
    output_files: list[OutputArtifact] | None = None
    pipeline_duration: float | None = None
    pipeline_exit_code: int | None = None

    def __post_init__(self):
        """Validate result consistency."""
        # test_passed should only be True if both pipeline and files are valid
        expected_test_passed = self.pipeline_successful and self.all_files_present

        if self.test_passed != expected_test_passed:
            # Auto-correct inconsistency
            self.test_passed = expected_test_passed

        # Error message should be provided when test fails
        if not self.test_passed and not self.error_message:
            self.error_message = "Test failed: see individual component status"

        # Initialize output_files list if not provided
        if self.output_files is None:
            self.output_files = []

    @classmethod
    def success(
        cls,
        execution_summary: str,
        output_files: list[OutputArtifact],
        pipeline_duration: float,
        pipeline_exit_code: int = 0
    ) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(
            test_passed=True,
            pipeline_successful=True,
            all_files_present=True,
            execution_summary=execution_summary,
            output_files=output_files,
            pipeline_duration=pipeline_duration,
            pipeline_exit_code=pipeline_exit_code
        )

    @classmethod
    def pipeline_failure(
        cls,
        error_message: str,
        pipeline_exit_code: int,
        pipeline_duration: float | None = None
    ) -> 'ValidationResult':
        """Create a pipeline failure result."""
        return cls(
            test_passed=False,
            pipeline_successful=False,
            all_files_present=False,
            execution_summary="Pipeline execution failed",
            error_message=error_message,
            pipeline_exit_code=pipeline_exit_code,
            pipeline_duration=pipeline_duration
        )

    @classmethod
    def file_validation_failure(
        cls,
        error_message: str,
        output_files: list[OutputArtifact],
        pipeline_duration: float,
        pipeline_exit_code: int = 0
    ) -> 'ValidationResult':
        """Create a file validation failure result."""
        return cls(
            test_passed=False,
            pipeline_successful=True,
            all_files_present=False,
            execution_summary="Output file validation failed",
            error_message=error_message,
            output_files=output_files,
            pipeline_duration=pipeline_duration,
            pipeline_exit_code=pipeline_exit_code
        )

    def get_failure_type(self) -> str:
        """Get categorized failure type for error handling."""
        if self.test_passed:
            return "success"

        if not self.pipeline_successful:
            return "pipeline_execution_failed"

        if not self.all_files_present:
            return "output_files_missing"

        return "output_validation_failed"

    def get_missing_files(self) -> list[str]:
        """Get list of missing expected files."""
        if not self.output_files:
            return []

        return [
            artifact.expected_name
            for artifact in self.output_files
            if not artifact.file_exists
        ]
