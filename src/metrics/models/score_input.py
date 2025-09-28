"""ScoreInput model for structured output format for downstream LLM processing."""

from datetime import datetime

from pydantic import BaseModel, Field, validator

from .evaluation_result import EvaluationResult, RepositoryInfo


class ScoreInput(BaseModel):
    """Structured output format for downstream LLM processing."""

    schema_version: str = Field(..., description="Format version (e.g., '1.0.0')")
    repository_info: RepositoryInfo = Field(..., description="Source repository details")
    evaluation_result: EvaluationResult = Field(..., description="Complete evaluation data")
    generation_timestamp: datetime = Field(..., description="When evaluation was performed")
    evidence_paths: dict[str, str] = Field(default_factory=dict, description="File paths to supporting evidence")
    human_summary: str = Field(..., description="Markdown summary for manual review")

    @validator("schema_version")
    def schema_version_must_be_semantic(cls, v):
        """Validate that schema_version follows semantic versioning."""
        import re
        # Basic semantic versioning pattern: MAJOR.MINOR.PATCH
        pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(pattern, v):
            raise ValueError(f"Schema version '{v}' must follow semantic versioning (e.g., '1.0.0')")
        return v

    @validator("generation_timestamp")
    def generation_timestamp_must_be_valid(cls, v):
        """Validate that generation_timestamp is a valid datetime."""
        if not isinstance(v, datetime):
            raise ValueError("Generation timestamp must be a valid datetime object")
        return v

    @validator("evidence_paths")
    def evidence_paths_must_be_valid(cls, v):
        """Validate that all evidence paths are valid references to existing files."""
        from pathlib import Path

        for key, path in v.items():
            if not isinstance(key, str) or not isinstance(path, str):
                raise ValueError("Evidence paths must be string key-value pairs")
            if not key.strip() or not path.strip():
                raise ValueError("Evidence path keys and values cannot be empty")

            # Check for phantom paths that should not be present
            phantom_paths = ["evaluation_summary", "category_breakdowns", "warnings_log"]
            if key in phantom_paths:
                raise ValueError(f"Phantom path '{key}' should not be in evidence_paths")

            # Validate that file exists (optional validation for file existence)
            # This validation can be disabled by setting SKIP_FILE_VALIDATION environment variable
            import os
            if not os.getenv("SKIP_FILE_VALIDATION"):
                file_path = Path(path)
                if not file_path.exists():
                    raise ValueError(f"Evidence file does not exist: {path}")
                if not file_path.is_file():
                    raise ValueError(f"Evidence path is not a file: {path}")

        return v

    @validator("human_summary")
    def human_summary_must_not_be_empty(cls, v):
        """Validate that human summary is not empty."""
        if not v.strip():
            raise ValueError("Human summary cannot be empty")
        return v

    def generate_human_summary(self) -> str:
        """Generate a markdown summary for manual review."""
        result = self.evaluation_result

        summary_lines = [
            "# Code Quality Evaluation Summary",
            "",
            f"**Repository**: {self.repository_info.url}",
            f"**Commit**: {self.repository_info.commit_sha}",
            f"**Language**: {self.repository_info.primary_language}",
            f"**Evaluation Date**: {self.generation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overall Score",
            "",
            f"**Total Score**: {result.total_score:.1f} / {result.max_possible_score} ({result.score_percentage:.1f}%)",
            "",
            "## Category Breakdown",
            ""
        ]

        for dimension, breakdown in result.category_breakdowns.items():
            summary_lines.extend([
                f"### {dimension.replace('_', ' ').title()}",
                f"- Score: {breakdown.actual_points:.1f} / {breakdown.max_points} ({breakdown.percentage:.1f}%)",
                f"- Items: {breakdown.items_count}",
                ""
            ])

        summary_lines.extend([
            "## Checklist Items",
            ""
        ])

        for item in result.checklist_items:
            status_icon = "✅" if item.evaluation_status == "met" else "⚠️" if item.evaluation_status == "partial" else "❌"
            summary_lines.extend([
                f"### {status_icon} {item.name}",
                f"- **Status**: {item.evaluation_status}",
                f"- **Score**: {item.score:.1f} / {item.max_points}",
                f"- **Description**: {item.description}",
                ""
            ])

        if result.evidence_summary:
            summary_lines.extend([
                "## Key Evidence",
                ""
            ])
            for evidence in result.evidence_summary:
                summary_lines.append(f"- {evidence}")

        if result.evaluation_metadata.warnings:
            summary_lines.extend([
                "",
                "## Warnings",
                ""
            ])
            for warning in result.evaluation_metadata.warnings:
                summary_lines.append(f"- ⚠️ {warning}")

        summary_lines.extend([
            "",
            "## Evaluation Metadata",
            "",
            f"- **Evaluator Version**: {result.evaluation_metadata.evaluator_version}",
            f"- **Processing Duration**: {result.evaluation_metadata.processing_duration:.2f}s",
            f"- **Metrics Completeness**: {result.evaluation_metadata.metrics_completeness:.1f}%",
            "",
            "---",
            f"*Generated at {self.generation_timestamp.isoformat()}*"
        ])

        return "\n".join(summary_lines)

    def update_human_summary(self) -> None:
        """Update the human summary based on current evaluation result."""
        self.human_summary = self.generate_human_summary()

    def to_json_dict(self) -> dict:
        """Convert to dictionary suitable for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "repository_info": {
                "url": self.repository_info.url,
                "commit_sha": self.repository_info.commit_sha,
                "primary_language": self.repository_info.primary_language,
                "analysis_timestamp": self.repository_info.analysis_timestamp.isoformat(),
                "metrics_source": self.repository_info.metrics_source
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "dimension": item.dimension,
                        "max_points": item.max_points,
                        "description": item.description,
                        "evaluation_status": item.evaluation_status,
                        "score": item.score,
                        "evidence_references": [
                            {
                                "source_type": evidence.source_type,
                                "source_path": evidence.source_path,
                                "description": evidence.description,
                                "confidence": evidence.confidence,
                                "raw_data": evidence.raw_data
                            }
                            for evidence in item.evidence_references
                        ]
                    }
                    for item in self.evaluation_result.checklist_items
                ],
                "total_score": self.evaluation_result.total_score,
                "max_possible_score": self.evaluation_result.max_possible_score,
                "score_percentage": self.evaluation_result.score_percentage,
                "category_breakdowns": {
                    dimension: {
                        "dimension": breakdown.dimension,
                        "items_count": breakdown.items_count,
                        "max_points": breakdown.max_points,
                        "actual_points": breakdown.actual_points,
                        "percentage": breakdown.percentage
                    }
                    for dimension, breakdown in self.evaluation_result.category_breakdowns.items()
                },
                "evaluation_metadata": {
                    "evaluator_version": self.evaluation_result.evaluation_metadata.evaluator_version,
                    "processing_duration": self.evaluation_result.evaluation_metadata.processing_duration,
                    "warnings": self.evaluation_result.evaluation_metadata.warnings,
                    "metrics_completeness": self.evaluation_result.evaluation_metadata.metrics_completeness
                },
                "evidence_summary": self.evaluation_result.evidence_summary
            },
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "evidence_paths": self.evidence_paths,
            "human_summary": self.human_summary
        }

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
