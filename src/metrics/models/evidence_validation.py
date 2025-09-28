"""
Evidence validation models for ensuring evidence paths reliability.

This module provides validation models for evidence paths to ensure
all referenced files actually exist and follow expected patterns.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator


class EvidencePathsMapping(BaseModel):
    """Validated mapping of evidence categories to verified file system paths.

    This model ensures that all evidence paths point to existing files
    and follow the expected naming conventions.
    """

    evidence_key: str
    file_path: str
    dimension: str
    source_type: str

    @field_validator("file_path")
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        """Validate that file_path points to an existing file."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Evidence file does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Evidence path is not a file: {v}")
        return v

    @field_validator("evidence_key")
    @classmethod
    def validate_evidence_key_pattern(cls, v: str) -> str:
        """Validate evidence_key follows expected pattern: {item_id}_{source_type}."""
        if "_" not in v:
            raise ValueError(f"Evidence key must contain underscore separator: {v}")
        return v

    @field_validator("dimension")
    @classmethod
    def validate_dimension(cls, v: str) -> str:
        """Validate dimension is one of expected values."""
        valid_dimensions = {"code_quality", "testing", "documentation", "system"}
        if v not in valid_dimensions:
            raise ValueError(f"Dimension must be one of {valid_dimensions}, got: {v}")
        return v


class EvidencePathsCollection(BaseModel):
    """Collection of validated evidence paths with metadata.

    This model represents the complete set of evidence paths
    for a repository evaluation with validation guarantees.
    """

    evidence_paths: Dict[str, str]
    evidence_base_path: str
    total_evidence_files: int
    validation_summary: Optional[Dict[str, int]] = None

    @field_validator("evidence_paths")
    @classmethod
    def validate_all_paths_exist(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate that all paths in evidence_paths point to existing files."""
        for evidence_key, file_path in v.items():
            path = Path(file_path)
            if not path.exists():
                raise ValueError(f"Evidence file does not exist: {file_path} for key: {evidence_key}")
            if not path.is_file():
                raise ValueError(f"Evidence path is not a file: {file_path} for key: {evidence_key}")
        return v

    @field_validator("total_evidence_files")
    @classmethod
    def validate_count_matches_evidence(cls, v: int, info) -> int:
        """Validate that total_evidence_files matches actual evidence_paths count."""
        if hasattr(info, 'data') and 'evidence_paths' in info.data:
            actual_count = len(info.data['evidence_paths'])
            if v != actual_count:
                raise ValueError(f"Total evidence files count ({v}) doesn't match actual evidence paths ({actual_count})")
        return v


class EvidenceFileMetadata(BaseModel):
    """Metadata for individual evidence files with validation.

    Provides detailed information about evidence files including
    file system properties and validation status.
    """

    file_path: str
    evidence_key: str
    file_size: int
    created_at: Optional[str] = None
    content_type: str
    is_valid: bool = True

    @field_validator("file_path")
    @classmethod
    def validate_file_exists_and_readable(cls, v: str) -> str:
        """Validate file exists and is readable."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Evidence file does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Evidence path is not a file: {v}")
        try:
            # Test readability
            path.read_bytes()
        except (OSError, PermissionError) as e:
            raise ValueError(f"Evidence file not readable: {v}, error: {e}")
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size_positive(cls, v: int) -> int:
        """Validate file size is positive (non-empty files)."""
        if v <= 0:
            raise ValueError(f"Evidence file must be non-empty, got size: {v}")
        return v

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type is one of expected types."""
        valid_types = {"checklist_item", "summary", "manifest"}
        if v not in valid_types:
            raise ValueError(f"Content type must be one of {valid_types}, got: {v}")
        return v


class ValidationResult(BaseModel):
    """Result of evidence paths validation with detailed feedback.

    Provides comprehensive validation results including
    success status, error details, and recommendations.
    """

    is_valid: bool
    total_paths_checked: int
    valid_paths_count: int
    invalid_paths: List[str] = []
    validation_errors: List[str] = []
    phantom_paths_removed: List[str] = []
    recommendations: List[str] = []

    @property
    def validation_summary(self) -> Dict[str, int]:
        """Get summary of validation results."""
        return {
            "total_checked": self.total_paths_checked,
            "valid": self.valid_paths_count,
            "invalid": len(self.invalid_paths),
            "phantom_removed": len(self.phantom_paths_removed)
        }


def validate_evidence_paths(evidence_paths: Dict[str, str]) -> ValidationResult:
    """Validate evidence paths dictionary for file existence and accessibility.

    Args:
        evidence_paths: Dictionary mapping evidence keys to file paths

    Returns:
        ValidationResult with detailed validation information
    """
    total_paths = len(evidence_paths)
    valid_paths = 0
    invalid_paths = []
    validation_errors = []
    phantom_paths_removed = []
    recommendations = []

    # Check for known phantom paths
    known_phantoms = ["evaluation_summary", "category_breakdowns", "warnings_log"]
    for phantom in known_phantoms:
        if phantom in evidence_paths:
            phantom_paths_removed.append(phantom)
            validation_errors.append(f"Phantom path detected: {phantom}")

    # Validate each evidence path
    for evidence_key, file_path in evidence_paths.items():
        if evidence_key in known_phantoms:
            continue  # Skip phantom paths

        try:
            path = Path(file_path)
            if not path.exists():
                invalid_paths.append(evidence_key)
                validation_errors.append(f"File does not exist: {file_path}")
                continue

            if not path.is_file():
                invalid_paths.append(evidence_key)
                validation_errors.append(f"Path is not a file: {file_path}")
                continue

            if path.stat().st_size == 0:
                invalid_paths.append(evidence_key)
                validation_errors.append(f"File is empty: {file_path}")
                continue

            valid_paths += 1

        except Exception as e:
            invalid_paths.append(evidence_key)
            validation_errors.append(f"Validation error for {evidence_key}: {e}")

    # Generate recommendations
    if phantom_paths_removed:
        recommendations.append("Remove phantom path generation from evidence mapping")
    if invalid_paths:
        recommendations.append("Ensure evidence files are created before path mapping")
    if valid_paths == 0 and total_paths > 0:
        recommendations.append("Check evidence generation workflow for file creation issues")

    is_valid = len(invalid_paths) == 0 and len(phantom_paths_removed) == 0

    return ValidationResult(
        is_valid=is_valid,
        total_paths_checked=total_paths,
        valid_paths_count=valid_paths,
        invalid_paths=invalid_paths,
        validation_errors=validation_errors,
        phantom_paths_removed=phantom_paths_removed,
        recommendations=recommendations
    )


def clean_evidence_paths(evidence_paths: Dict[str, str]) -> Dict[str, str]:
    """Clean evidence paths by removing phantom entries and invalid files.

    Args:
        evidence_paths: Original evidence paths dictionary

    Returns:
        Cleaned evidence paths with only valid, existing files
    """
    cleaned_paths = {}
    known_phantoms = ["evaluation_summary", "category_breakdowns", "warnings_log"]

    for evidence_key, file_path in evidence_paths.items():
        # Skip known phantom paths
        if evidence_key in known_phantoms:
            continue

        # Only include paths that point to existing files
        path = Path(file_path)
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            cleaned_paths[evidence_key] = file_path

    return cleaned_paths