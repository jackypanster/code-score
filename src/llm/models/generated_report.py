"""
Generated report output model.

This module defines the GeneratedReport Pydantic model for final report
output with metadata and generation tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class TruncationInfo(BaseModel):
    """Information about content truncation during generation."""

    evidence_truncated: bool = Field(
        default=False,
        description="Whether evidence items were truncated"
    )

    items_removed: int = Field(
        default=0,
        description="Number of evidence items removed due to length limits",
        ge=0
    )

    original_length: int = Field(
        default=0,
        description="Original content length before truncation",
        ge=0
    )

    final_length: int = Field(
        default=0,
        description="Final content length after truncation",
        ge=0
    )

    truncation_reason: Optional[str] = Field(
        None,
        description="Reason for truncation (context_limit, max_tokens, etc.)"
    )


class ProviderMetadata(BaseModel):
    """Metadata about the LLM provider used for generation."""

    provider_name: str = Field(
        ...,
        description="Name of the LLM provider"
    )

    model_name: Optional[str] = Field(
        None,
        description="Specific model used for generation"
    )

    temperature: Optional[float] = Field(
        None,
        description="Temperature setting used",
        ge=0.0,
        le=2.0
    )

    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens setting",
        gt=0
    )

    response_time_seconds: Optional[float] = Field(
        None,
        description="Time taken for LLM response",
        ge=0.0
    )

    token_usage: Optional[Dict[str, int]] = Field(
        None,
        description="Token usage statistics (prompt_tokens, completion_tokens, total_tokens)"
    )


class TemplateMetadata(BaseModel):
    """Metadata about the template used for generation."""

    file_path: str = Field(
        ...,
        description="Path to the template file used"
    )

    template_name: str = Field(
        ...,
        description="Template identifier"
    )

    template_type: str = Field(
        default="general",
        description="Template category"
    )

    required_fields_used: List[str] = Field(
        default_factory=list,
        description="List of template fields that were populated"
    )


class InputMetadata(BaseModel):
    """Metadata about the input data used for generation."""

    repository_url: str = Field(
        ...,
        description="Repository URL from score input"
    )

    commit_sha: str = Field(
        ...,
        description="Commit SHA analyzed"
    )

    primary_language: str = Field(
        ...,
        description="Primary programming language"
    )

    total_score: float = Field(
        ...,
        description="Total evaluation score",
        ge=0.0,
        le=100.0
    )

    max_possible_score: float = Field(
        ...,
        description="Maximum possible score",
        ge=0.0,
        le=100.0
    )

    checklist_items_count: int = Field(
        ...,
        description="Number of checklist items evaluated",
        ge=0
    )

    evidence_items_count: int = Field(
        ...,
        description="Number of evidence items available",
        ge=0
    )


class GeneratedReport(BaseModel):
    """
    Final report output with metadata and generation tracking.

    This model represents the complete generated report including content,
    generation metadata, and information about the generation process.
    """

    content: str = Field(
        ...,
        description="Generated markdown report content",
        min_length=1
    )

    generation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the report was generated (UTC)"
    )

    template_used: TemplateMetadata = Field(
        ...,
        description="Information about the template used"
    )

    provider_used: ProviderMetadata = Field(
        ...,
        description="Information about the LLM provider used"
    )

    input_metadata: InputMetadata = Field(
        ...,
        description="Metadata about the input evaluation data"
    )

    truncation_applied: TruncationInfo = Field(
        default_factory=TruncationInfo,
        description="Information about any content truncation"
    )

    generation_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings or issues during generation process"
    )

    validation_status: str = Field(
        default="valid",
        description="Validation status of generated content"
    )

    word_count: int = Field(
        default=0,
        description="Word count of generated content",
        ge=0
    )

    estimated_reading_time_minutes: float = Field(
        default=0.0,
        description="Estimated reading time in minutes",
        ge=0.0
    )

    @classmethod
    @field_validator('content')
    def validate_content_format(cls, v):
        """Validate that content is proper markdown format."""
        if not v.strip():
            raise ValueError("Report content cannot be empty")

        # Basic markdown validation - should have at least one header
        if not any(line.strip().startswith('#') for line in v.split('\n')):
            raise ValueError("Report content should contain at least one markdown header")

        return v

    @classmethod
    @field_validator('validation_status')
    def validate_status(cls, v):
        """Validate validation status values."""
        allowed_statuses = ['valid', 'warnings', 'errors', 'incomplete']
        if v not in allowed_statuses:
            raise ValueError(f"Validation status must be one of: {', '.join(allowed_statuses)}")

        return v

    def calculate_derived_fields(self) -> None:
        """Calculate word count and reading time from content."""
        import re

        # Calculate word count (simple whitespace-based counting)
        words = re.findall(r'\b\w+\b', self.content)
        self.word_count = len(words)

        # Estimate reading time (average 200 words per minute)
        self.estimated_reading_time_minutes = max(1.0, self.word_count / 200.0)

    def add_warning(self, warning: str) -> None:
        """Add a generation warning."""
        if warning not in self.generation_warnings:
            self.generation_warnings.append(warning)

    def get_content_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the generated content."""
        lines = self.content.split('\n')

        # Count different markdown elements
        headers = [line for line in lines if line.strip().startswith('#')]
        code_blocks = self.content.count('```')
        lists = [line for line in lines if line.strip().startswith(('- ', '* ', '1.'))]

        return {
            'total_lines': len(lines),
            'headers_count': len(headers),
            'code_blocks_count': code_blocks // 2,  # Paired opening/closing
            'list_items_count': len(lists),
            'word_count': self.word_count,
            'character_count': len(self.content),
            'estimated_reading_time': self.estimated_reading_time_minutes
        }

    def validate_markdown_structure(self) -> List[str]:
        """
        Validate markdown structure and return list of issues.

        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []
        lines = self.content.split('\n')

        # Check for basic structure
        has_title = any(line.strip().startswith('# ') for line in lines)
        if not has_title:
            issues.append("No main title (H1) found")

        # Check for unmatched code blocks
        code_block_count = self.content.count('```')
        if code_block_count % 2 != 0:
            issues.append("Unmatched code block markers")

        # Check for empty headers
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#') and not line.strip()[line.strip().find(' '):].strip():
                issues.append(f"Empty header on line {i}")

        return issues

    def to_file_content(self) -> str:
        """
        Generate file content with metadata header.

        Returns:
            Complete file content including metadata and report
        """
        metadata_header = f"""<!--
Generated Report Metadata:
- Generated: {self.generation_timestamp.isoformat()}
- Template: {self.template_used.template_name} ({self.template_used.template_type})
- Provider: {self.provider_used.provider_name}
- Repository: {self.input_metadata.repository_url}
- Score: {self.input_metadata.total_score}/{self.input_metadata.max_possible_score}
- Word Count: {self.word_count}
- Reading Time: {self.estimated_reading_time_minutes:.1f} minutes
-->

"""
        return metadata_header + self.content

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

        json_schema_extra = {
            "example": {
                "content": "# Code Review Report\n\n## Overview\nThis repository shows...",
                "generation_timestamp": "2025-09-27T15:30:00Z",
                "template_used": {
                    "file_path": "specs/prompts/llm_report.md",
                    "template_name": "Default LLM Report",
                    "template_type": "general",
                    "required_fields_used": ["repository.url", "total.score", "met_items"]
                },
                "provider_used": {
                    "provider_name": "gemini",
                    "model_name": "gemini-1.5-pro",
                    "temperature": 0.1,
                    "response_time_seconds": 12.5
                },
                "input_metadata": {
                    "repository_url": "https://github.com/user/repo.git",
                    "commit_sha": "abc123456",
                    "primary_language": "python",
                    "total_score": 67.5,
                    "max_possible_score": 100.0,
                    "checklist_items_count": 11,
                    "evidence_items_count": 25
                },
                "word_count": 342,
                "estimated_reading_time_minutes": 1.7,
                "validation_status": "valid"
            }
        }