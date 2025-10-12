"""
Contract specification for programmatic API return objects.

This file defines the expected Pydantic model structures for return values.
Implementation will be in src/cli/models.py.

Contract tests in tests/contract/test_programmatic_api_contract.py will validate
compliance with this specification.
"""

from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("valid")
    @classmethod
    def validate_valid_consistency(cls, v: bool, info) -> bool:
        """If valid=True, passed_checks must equal items_checked."""
        if v and "passed_checks" in info.data and "items_checked" in info.data:
            passed = set(info.data["passed_checks"])
            items = set(info.data["items_checked"])
            if passed != items:
                raise ValueError(
                    "If valid=True, passed_checks must equal items_checked"
                )
        return v


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
    def validate_total_score(cls, v: float, info) -> float:
        """Validate total_score is non-negative and <= max_possible_score."""
        if v < 0:
            raise ValueError(f"total_score must be non-negative, got {v}")
        if "max_possible_score" in info.data:
            max_score = info.data["max_possible_score"]
            if v > max_score:
                raise ValueError(
                    f"total_score ({v}) cannot exceed max_possible_score ({max_score})"
                )
        return v

    @field_validator("max_possible_score")
    @classmethod
    def validate_max_possible_score(cls, v: float) -> float:
        """Validate max_possible_score is positive."""
        if v <= 0:
            raise ValueError(f"max_possible_score must be positive, got {v}")
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str, info) -> str:
        """Validate grade matches score percentage."""
        valid_grades = {"A", "B", "C", "D", "F"}
        if v not in valid_grades:
            raise ValueError(f"grade must be one of {valid_grades}, got '{v}'")

        # Validate grade matches score if both present
        if "total_score" in info.data and "max_possible_score" in info.data:
            total = info.data["total_score"]
            max_score = info.data["max_possible_score"]
            percentage = (total / max_score) * 100

            expected_grade = _calculate_grade(percentage)
            if v != expected_grade:
                raise ValueError(
                    f"grade '{v}' doesn't match score {percentage:.1f}% "
                    f"(expected '{expected_grade}')"
                )
        return v

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


# Contract validation utilities
def validate_validation_result_contract(result: ValidationResult) -> bool:
    """
    Validate ValidationResult meets contract requirements.

    Contract Requirements:
        - passed_checks must be subset of items_checked
        - If valid=True, passed_checks must equal items_checked
        - warnings must be list (may be empty)

    Raises:
        AssertionError if contract violated
    """
    assert isinstance(result.valid, bool), "valid must be bool"
    assert isinstance(result.items_checked, list), "items_checked must be list"
    assert isinstance(result.passed_checks, list), "passed_checks must be list"
    assert isinstance(result.warnings, list), "warnings must be list"

    passed_set = set(result.passed_checks)
    items_set = set(result.items_checked)
    assert passed_set.issubset(items_set), "passed_checks must be subset of items_checked"

    if result.valid:
        assert passed_set == items_set, "If valid=True, passed_checks must equal items_checked"

    return True


def validate_evaluation_result_contract(result: EvaluationResult) -> bool:
    """
    Validate EvaluationResult meets contract requirements.

    Contract Requirements:
        - total_score >= 0
        - total_score <= max_possible_score
        - max_possible_score > 0
        - grade in {A, B, C, D, F}
        - grade matches score percentage
        - generated_files is list of strings
        - evidence_files is dict with string values

    Raises:
        AssertionError if contract violated
    """
    assert isinstance(result.success, bool), "success must be bool"
    assert isinstance(result.total_score, (int, float)), "total_score must be numeric"
    assert isinstance(result.max_possible_score, (int, float)), "max_possible_score must be numeric"
    assert isinstance(result.grade, str), "grade must be string"
    assert isinstance(result.generated_files, list), "generated_files must be list"
    assert isinstance(result.evidence_files, dict), "evidence_files must be dict"

    assert result.total_score >= 0, "total_score must be non-negative"
    assert result.total_score <= result.max_possible_score, "total_score must be <= max_possible_score"
    assert result.max_possible_score > 0, "max_possible_score must be positive"

    assert result.grade in {"A", "B", "C", "D", "F"}, f"grade must be A-F, got '{result.grade}'"

    percentage = (result.total_score / result.max_possible_score) * 100
    expected_grade = _calculate_grade(percentage)
    assert result.grade == expected_grade, f"grade mismatch: expected '{expected_grade}' for {percentage:.1f}%"

    return True
