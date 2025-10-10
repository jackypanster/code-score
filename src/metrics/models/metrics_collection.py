"""MetricsCollection entity model for aggregating analysis results."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .build_validation import BuildValidationResult


class LintIssue(BaseModel):
    """Individual linting issue."""
    severity: str = Field(..., description="Issue severity (error, warning, info)")
    message: str = Field(..., description="Issue description")
    file: str = Field(..., description="File path")
    line: int = Field(..., description="Line number")
    column: int | None = Field(None, description="Column number")


class SecurityIssue(BaseModel):
    """Security vulnerability issue."""
    severity: str = Field(..., description="Vulnerability severity")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    cve_id: str | None = Field(None, description="CVE identifier")
    affected_package: str | None = Field(None, description="Affected package name")


class CodeQualityMetrics(BaseModel):
    """Code quality analysis results."""
    lint_results: dict[str, Any] | None = Field(None, description="Linting tool results")
    build_success: bool | None = Field(None, description="Build success status")
    build_details: BuildValidationResult | None = Field(None, description="Detailed build validation results")
    security_issues: list[SecurityIssue] = Field(default_factory=list, description="Security vulnerabilities")
    dependency_audit: dict[str, Any] | None = Field(None, description="Dependency audit results")


class TestingMetrics(BaseModel):
    """Testing execution and coverage results."""
    test_execution: dict[str, Any] | None = Field(None, description="Test execution results")
    coverage_report: dict[str, Any] | None = Field(None, description="Code coverage analysis")


class DocumentationMetrics(BaseModel):
    """Documentation quality assessment."""
    readme_present: bool = Field(False, description="README file exists")
    readme_quality_score: float = Field(0.0, description="README completeness score (0-1)")
    api_documentation: bool = Field(False, description="API documentation present")
    setup_instructions: bool = Field(False, description="Setup instructions present")
    usage_examples: bool = Field(False, description="Usage examples provided")


class ExecutionMetadata(BaseModel):
    """Tool execution metadata."""
    tools_used: list[str] = Field(default_factory=list, description="Analysis tools executed")
    errors: list[str] = Field(default_factory=list, description="Errors encountered")
    warnings: list[str] = Field(default_factory=list, description="Warnings generated")
    duration_seconds: float = Field(0.0, description="Total execution time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class MetricsCollection(BaseModel):
    """Container for all collected quality metrics."""

    repository_id: str = Field(default="", description="Reference to analyzed repository")
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When metrics were collected")
    code_quality: CodeQualityMetrics = Field(default_factory=CodeQualityMetrics, description="Code quality metrics")
    testing_metrics: TestingMetrics = Field(default_factory=TestingMetrics, description="Testing metrics")
    documentation_metrics: DocumentationMetrics = Field(default_factory=DocumentationMetrics, description="Documentation metrics")
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata, description="Execution metadata")
