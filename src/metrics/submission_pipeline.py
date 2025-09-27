"""Pipeline component for loading and validating submission.json files."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from .models.repository import Repository
from .models.metrics_collection import MetricsCollection


class SubmissionValidationError(Exception):
    """Exception raised when submission.json validation fails."""
    pass


class SubmissionLoader:
    """Loads and validates submission.json files for pipeline processing."""

    def __init__(self):
        self.required_sections = ["repository", "metrics", "execution"]
        self.required_repository_fields = ["url", "commit", "language", "timestamp"]
        self.required_metrics_sections = ["code_quality", "testing", "documentation"]

    def load_and_validate(self, submission_path: str) -> Dict[str, Any]:
        """
        Load and validate a submission.json file.

        Args:
            submission_path: Path to the submission.json file

        Returns:
            Validated submission data dictionary

        Raises:
            SubmissionValidationError: If file is invalid or missing required fields
        """
        submission_path = Path(submission_path)

        if not submission_path.exists():
            raise SubmissionValidationError(f"Submission file not found: {submission_path}")

        try:
            with open(submission_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SubmissionValidationError(f"Invalid JSON in submission file: {e}")

        # Validate structure
        validation_errors = self._validate_structure(data)
        if validation_errors:
            error_msg = "Submission validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            raise SubmissionValidationError(error_msg)

        return data

    def _validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validate the structure of submission data."""
        errors = []

        # Check required top-level sections
        for section in self.required_sections:
            if section not in data:
                errors.append(f"Missing required section: {section}")

        # Validate repository section
        if "repository" in data:
            repo_data = data["repository"]
            for field in self.required_repository_fields:
                if field not in repo_data:
                    errors.append(f"Missing repository field: {field}")

        # Validate metrics section
        if "metrics" in data:
            metrics_data = data["metrics"]
            for section in self.required_metrics_sections:
                if section not in metrics_data:
                    errors.append(f"Missing metrics section: {section}")

        # Validate execution section
        if "execution" in data:
            exec_data = data["execution"]
            if "errors" not in exec_data:
                errors.append("Missing execution.errors field")
            if "warnings" not in exec_data:
                errors.append("Missing execution.warnings field")

        return errors

    def extract_repository_info(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract repository information from submission data."""
        repo_data = submission_data.get("repository", {})

        return {
            "url": repo_data.get("url", "unknown"),
            "commit_sha": repo_data.get("commit", "unknown"),
            "primary_language": repo_data.get("language", "unknown"),
            "analysis_timestamp": repo_data.get("timestamp", "unknown"),
            "size_mb": repo_data.get("size_mb", 0),
            "metrics_source": "submission.json"
        }

    def validate_for_checklist_evaluation(self, submission_data: Dict[str, Any]) -> List[str]:
        """
        Validate submission data specifically for checklist evaluation.

        Returns:
            List of validation warnings (not errors, as evaluation can proceed)
        """
        warnings = []

        # Check for common evaluation paths
        metrics = submission_data.get("metrics", {})

        # Code quality checks
        code_quality = metrics.get("code_quality", {})
        if not code_quality.get("lint_results"):
            warnings.append("No lint_results found in code_quality section")
        if code_quality.get("build_success") is None:
            warnings.append("No build_success data found in code_quality section")
        if not code_quality.get("dependency_audit"):
            warnings.append("No dependency_audit found in code_quality section")

        # Testing checks
        testing = metrics.get("testing", {})
        if not testing.get("test_execution"):
            warnings.append("No test_execution found in testing section")
        if not testing.get("coverage_report"):
            warnings.append("No coverage_report found in testing section")

        # Documentation checks
        documentation = metrics.get("documentation", {})
        if documentation.get("readme_present") is None:
            warnings.append("No readme_present data found in documentation section")

        return warnings


class PipelineIntegrator:
    """Integrates checklist evaluation with the existing metrics pipeline."""

    def __init__(self, submission_loader: Optional[SubmissionLoader] = None):
        self.submission_loader = submission_loader or SubmissionLoader()

    def should_run_checklist_evaluation(self, submission_data: Dict[str, Any]) -> bool:
        """
        Determine if checklist evaluation should run based on submission data quality.

        Args:
            submission_data: The loaded submission data

        Returns:
            True if evaluation should proceed, False otherwise
        """
        # Check if we have minimum required data for meaningful evaluation
        metrics = submission_data.get("metrics", {})

        # Require at least one of the main metric categories to have data
        has_code_quality = bool(metrics.get("code_quality"))
        has_testing = bool(metrics.get("testing"))
        has_documentation = bool(metrics.get("documentation"))

        return has_code_quality or has_testing or has_documentation

    def prepare_submission_for_evaluation(self, submission_path: str) -> tuple[Dict[str, Any], List[str]]:
        """
        Load, validate, and prepare submission data for checklist evaluation.

        Args:
            submission_path: Path to submission.json file

        Returns:
            Tuple of (submission_data, warnings)

        Raises:
            SubmissionValidationError: If submission is invalid
        """
        # Load and validate basic structure
        submission_data = self.submission_loader.load_and_validate(submission_path)

        # Get evaluation-specific warnings
        warnings = self.submission_loader.validate_for_checklist_evaluation(submission_data)

        return submission_data, warnings

    def get_pipeline_metadata(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata about the pipeline run from submission data."""
        execution = submission_data.get("execution", {})

        return {
            "tools_used": execution.get("tools_used", []),
            "duration_seconds": execution.get("duration_seconds", 0),
            "errors_count": len(execution.get("errors", [])),
            "warnings_count": len(execution.get("warnings", [])),
            "timestamp": execution.get("timestamp", "unknown")
        }