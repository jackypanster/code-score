"""
Report template configuration model.

This module defines the ReportTemplate Pydantic model for template configuration
and metadata used in LLM report generation.
"""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ReportTemplate(BaseModel):
    """
    Configuration and metadata for report generation templates.

    This model handles template file paths, validation, and content limits
    for use with Jinja2 template rendering and LLM prompt generation.
    """

    name: str = Field(
        ...,
        description="Human-readable template identifier",
        min_length=1,
        max_length=100
    )

    file_path: str = Field(
        ...,
        description="Path to the template file (absolute or relative to project root)",
        min_length=1
    )

    description: str = Field(
        ...,
        description="Human-readable description of template purpose",
        min_length=1,
        max_length=500
    )

    required_fields: list[str] = Field(
        default_factory=list,
        description="List of required template placeholders (Jinja2 variables)"
    )

    content_limits: dict[str, int] = Field(
        default_factory=lambda: {
            "max_evidence_items": 3,
            "max_checklist_items": 20,
            "max_description_length": 200
        },
        description="Content truncation limits for LLM context management"
    )

    template_type: str = Field(
        default="general",
        description="Template category (general, hackathon, code_review, etc.)"
    )

    target_providers: list[str] = Field(
        default_factory=lambda: ["gemini"],
        description="LLM providers this template is optimized for"
    )

    @classmethod
    @field_validator('file_path')
    def validate_file_path(cls, v):
        """Validate that template file exists and is readable."""
        path = Path(v)
        if not path.is_absolute():
            # Convert relative path to absolute from project root
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            path = project_root / v

        if not path.exists():
            raise ValueError(f"Template file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Template path is not a file: {path}")

        try:
            path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as e:
            raise ValueError(f"Template file not readable: {e}")

        return str(path)

    @classmethod
    @field_validator('required_fields')
    def validate_required_fields(cls, v):
        """Validate that field names are valid Jinja2 identifiers."""
        import re
        identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')

        for field in v:
            if not identifier_pattern.match(field):
                raise ValueError(f"Invalid template field name: {field}")

        return v

    @classmethod
    @field_validator('content_limits')
    def validate_content_limits(cls, v):
        """Validate that content limits are positive integers."""
        for key, value in v.items():
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"Content limit '{key}' must be a positive integer, got: {value}")

        # Ensure required limits exist
        required_limits = ['max_evidence_items', 'max_checklist_items', 'max_description_length']
        for limit in required_limits:
            if limit not in v:
                raise ValueError(f"Missing required content limit: {limit}")

        return v

    @classmethod
    @field_validator('template_type')
    def validate_template_type(cls, v):
        """Validate template type is from allowed values."""
        allowed_types = [
            'general', 'hackathon', 'code_review', 'security_audit',
            'performance_review', 'minimal', 'detailed'
        ]

        if v not in allowed_types:
            raise ValueError(f"Template type must be one of: {', '.join(allowed_types)}")

        return v

    @classmethod
    @field_validator('target_providers')
    def validate_target_providers(cls, v):
        """Validate that provider names are recognized."""
        allowed_providers = ['gemini']

        for provider in v:
            if provider not in allowed_providers:
                raise ValueError(f"Unsupported provider: {provider}. Only Gemini is supported in this MVP version.")

        return v

    def get_absolute_path(self) -> Path:
        """Get absolute path to template file."""
        return Path(self.file_path)

    def load_template_content(self) -> str:
        """Load and return template file content."""
        return self.get_absolute_path().read_text(encoding='utf-8')

    def validate_template_syntax(self) -> bool:
        """
        Validate Jinja2 template syntax without rendering.

        Returns:
            True if template syntax is valid

        Raises:
            ValueError: If template has syntax errors
        """
        try:
            from jinja2 import Template, TemplateSyntaxError
            Template(self.load_template_content())
            return True
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error in {self.file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Template validation failed for {self.file_path}: {e}")

    def check_required_fields(self, available_fields: list[str]) -> list[str]:
        """
        Check if all required fields are available in template context.

        Args:
            available_fields: List of field names available for template rendering

        Returns:
            List of missing required fields (empty if all present)
        """
        missing = []
        for field in self.required_fields:
            if field not in available_fields:
                missing.append(field)
        return missing

    def get_content_limit(self, limit_type: str, default: int = 10) -> int:
        """
        Get specific content limit with fallback to default.

        Args:
            limit_type: Type of content limit to retrieve
            default: Default value if limit not found

        Returns:
            Content limit value
        """
        return self.content_limits.get(limit_type, default)

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "name": "Default LLM Report Template",
                "file_path": "specs/prompts/llm_report.md",
                "description": "Standard template for code quality evaluation reports",
                "required_fields": [
                    "repository.url",
                    "total.score",
                    "met_items",
                    "unmet_items",
                    "evidence_summary"
                ],
                "content_limits": {
                    "max_evidence_items": 3,
                    "max_checklist_items": 20,
                    "max_description_length": 200
                },
                "template_type": "general",
                "target_providers": ["gemini"]
            }
        }
