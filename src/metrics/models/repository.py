"""Repository entity model for metrics collection."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Repository(BaseModel):
    """Represents a Git repository being analyzed."""

    url: str = Field(default="", description="Git repository URL")
    commit_sha: Optional[str] = Field(None, description="Specific commit to analyze")
    local_path: Optional[str] = Field(None, description="Temporary local clone path")
    detected_language: Optional[str] = Field(None, description="Primary programming language detected")
    clone_timestamp: Optional[datetime] = Field(None, description="When repository was cloned")
    size_mb: Optional[float] = Field(None, description="Repository size in megabytes")

    @field_validator('commit_sha')
    @classmethod
    def validate_commit_sha(cls, v: Optional[str]) -> Optional[str]:
        """Validate commit SHA format."""
        if v is not None and len(v) != 40:
            raise ValueError("Commit SHA must be 40 characters long")
        if v is not None and not all(c in '0123456789abcdef' for c in v.lower()):
            raise ValueError("Commit SHA must contain only hexadecimal characters")
        return v

    @field_validator('detected_language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate detected language is supported."""
        if v is not None:
            supported_languages = {"python", "javascript", "typescript", "java", "go", "unknown"}
            if v not in supported_languages:
                raise ValueError(f"Language must be one of {supported_languages}")
        return v

    @field_validator('size_mb')
    @classmethod
    def validate_size(cls, v: Optional[float]) -> Optional[float]:
        """Validate repository size is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Repository size must be non-negative")
        return v