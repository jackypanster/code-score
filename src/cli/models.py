"""Programmatic API return objects for evaluate_submission() function.

This module defines Pydantic models for structured return values from the
programmatic evaluation API, separate from internal ChecklistEvaluator models.
"""

from typing import Dict, List

from pydantic import BaseModel, Field, field_validator, model_validator


class ValidationResult(BaseModel):
    """
    Return value for evaluate_submission() when validate_only=True.

    This object provides validation feedback without performing the full evaluation.
    Useful for quick input validation in CI/CD pipelines or pre-flight checks.

    Attributes:
        valid: bool
            Overall validation status
            True if all critical validation checks passed

        items_checked: List[str]
            List of validation items that were performed
            Examples: ["submission_structure", "checklist_config", "required_sections"]
            Order is not guaranteed

        passed_checks: List[str]
            Subset of items_checked that passed validation
            If valid=True, this should equal items_checked
            Order matches items_checked

        warnings: List[str]
            Non-fatal validation warnings
            Empty list if no warnings
            Warnings do not prevent valid=True

    Example:
        >>> result = ValidationResult(
        ...     valid=True,
        ...     items_checked=["submission_structure", "checklist_config"],
        ...     passed_checks=["submission_structure", "checklist_config"],
        ...     warnings=[]
        ... )
        >>> assert result.valid
        >>> assert set(result.passed_checks) == set(result.items_checked)
    """

    valid: bool
    items_checked: List[str]
    passed_checks: List[str]
    warnings: List[str] = Field(default_factory=list)

    @field_validator("passed_checks")
    @classmethod
    def validate_passed_checks_subset(cls, v: List[str], info) -> List[str]:
        """Validate that passed_checks is a subset of items_checked."""
        if "items_checked" in info.data:
            items_checked = info.data["items_checked"]
            passed_set = set(v)
            items_set = set(items_checked)
            if not passed_set.issubset(items_set):
                extra = passed_set - items_set
                raise ValueError(
                    f"passed_checks contains items not in items_checked: {extra}"
                )
        return v

    @model_validator(mode="after")
    def validate_valid_consistency(self) -> "ValidationResult":
        """If valid=True, passed_checks must equal items_checked."""
        if self.valid:
            passed = set(self.passed_checks)
            items = set(self.items_checked)
            if passed != items:
                raise ValueError(
                    "If valid=True, passed_checks must equal items_checked"
                )
        return self


class EvaluationResult(BaseModel):
    """
    Return value for evaluate_submission() when validate_only=False.

    This object provides the evaluation outcome with score, grade, and generated
    file paths. Note: This is different from ChecklistEvaluator's EvaluationResult
    (which has more detailed checklist item breakdowns).

    Attributes:
        success: bool
            Evaluation completed successfully
            Note: Quality gate failures raise QualityGateException instead of
            returning success=False, so in practice this is always True if returned

        total_score: float
            Actual score achieved from checklist evaluation
            Range: 0.0 to max_possible_score
            Example: 85.5

        max_possible_score: float
            Maximum possible score from checklist
            Typically 100.0 but may vary with custom checklists
            Example: 100.0

        grade: str
            Letter grade A-F based on score percentage
            Calculation: (total_score / max_possible_score) * 100
            A: ≥90%, B: ≥80%, C: ≥70%, D: ≥60%, F: <60%

        generated_files: List[str]
            Absolute paths to generated output files
            Examples: ["/abs/path/output/score_input.json", "/abs/path/output/evaluation_report.md"]
            Empty if no files generated (shouldn't happen in normal mode)

        evidence_files: Dict[str, str]
            Evidence file mapping (key: evidence type, value: absolute path)
            Examples: {"code_quality_lint": "/abs/path/evidence/code_quality/lint.json"}
            Keys are evidence tracker categories
            All paths must exist at function return time

        warnings: List[str]
            Evaluation warnings from ChecklistEvaluator
            Empty list if no warnings
            Non-empty warnings do not prevent success=True

    Example:
        >>> result = EvaluationResult(
        ...     success=True,
        ...     total_score=85.5,
        ...     max_possible_score=100.0,
        ...     grade="B",
        ...     generated_files=["/path/score_input.json"],
        ...     evidence_files={"code_quality": "/path/evidence/code_quality.json"},
        ...     warnings=[]
        ... )
        >>> assert result.success
        >>> assert result.grade == "B"
        >>> assert result.total_score / result.max_possible_score == 0.855
    """

    success: bool
    total_score: float
    max_possible_score: float
    grade: str
    generated_files: List[str]
    evidence_files: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

    @field_validator("total_score")
    @classmethod
    def validate_total_score_non_negative(cls, v: float) -> float:
        """Validate total_score is non-negative."""
        if v < 0:
            raise ValueError(f"total_score must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_total_score_bounds(self) -> "EvaluationResult":
        """Validate total_score <= max_possible_score."""
        if self.total_score > self.max_possible_score:
            raise ValueError(
                f"total_score ({self.total_score}) cannot exceed max_possible_score ({self.max_possible_score})"
            )
        return self

    @field_validator("max_possible_score")
    @classmethod
    def validate_max_possible_score(cls, v: float) -> float:
        """Validate max_possible_score is positive."""
        if v <= 0:
            raise ValueError(f"max_possible_score must be positive, got {v}")
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade_value(cls, v: str) -> str:
        """Validate grade is a valid letter grade."""
        valid_grades = {"A", "B", "C", "D", "F"}
        if v not in valid_grades:
            raise ValueError(f"grade must be one of {valid_grades}, got '{v}'")
        return v

    @model_validator(mode="after")
    def validate_grade_matches_score(self) -> "EvaluationResult":
        """Validate grade matches score percentage."""
        percentage = (self.total_score / self.max_possible_score) * 100
        expected_grade = _calculate_grade(percentage)
        if self.grade != expected_grade:
            raise ValueError(
                f"grade '{self.grade}' doesn't match score {percentage:.1f}% "
                f"(expected '{expected_grade}')"
            )
        return self

    @property
    def score_percentage(self) -> float:
        """Calculate score percentage."""
        return (self.total_score / self.max_possible_score) * 100


def _calculate_grade(percentage: float) -> str:
    """
    Calculate letter grade from percentage.

    Args:
        percentage: Score percentage (0-100)

    Returns:
        Letter grade A-F

    Examples:
        >>> _calculate_grade(95.0)
        'A'
        >>> _calculate_grade(85.0)
        'B'
        >>> _calculate_grade(55.0)
        'F'
    """
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
