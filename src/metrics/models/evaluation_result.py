"""EvaluationResult model for complete checklist evaluation results."""

from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .checklist_item import ChecklistItem
from .category_breakdown import CategoryBreakdown


class RepositoryInfo(BaseModel):
    """Repository context for the evaluation."""

    url: str = Field(..., description="Repository URL")
    commit_sha: str = Field(..., description="Specific commit evaluated")
    primary_language: str = Field(..., description="Detected programming language")
    analysis_timestamp: datetime = Field(..., description="When metrics were collected")
    metrics_source: str = Field(..., description="Path to submission.json file")



class EvaluationMetadata(BaseModel):
    """Execution details for the evaluation process."""

    evaluator_version: str = Field(..., description="Version of evaluation logic")
    processing_duration: float = Field(..., ge=0.0, description="Seconds taken for evaluation")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal issues encountered")
    metrics_completeness: float = Field(..., ge=0.0, le=100.0, description="Percentage of required metrics available")


class EvaluationResult(BaseModel):
    """Container for complete checklist evaluation results."""

    checklist_items: List[ChecklistItem] = Field(..., description="All 11 evaluated items")
    total_score: float = Field(..., ge=0.0, description="Sum of all item scores")
    max_possible_score: int = Field(default=100, description="Maximum possible total (100 points)")
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage score")
    category_breakdowns: Dict[str, CategoryBreakdown] = Field(..., description="Score by dimension")
    evaluation_metadata: EvaluationMetadata = Field(..., description="Execution details")
    evidence_summary: List[str] = Field(default_factory=list, description="Key evidence points for human review")

    @validator("checklist_items")
    def must_have_exactly_11_items(cls, v):
        """Validate that there are exactly 11 checklist items."""
        if len(v) != 11:
            raise ValueError(f"Must have exactly 11 checklist items, got {len(v)}")
        return v

    @validator("total_score")
    def total_score_must_equal_sum(cls, v, values):
        """Validate that total_score equals sum of individual item scores."""
        if "checklist_items" in values:
            calculated_total = sum(item.score for item in values["checklist_items"])
            if abs(v - calculated_total) > 0.01:  # Allow small floating point differences
                raise ValueError(f"Total score {v} doesn't match sum of items {calculated_total}")
        return v

    @validator("score_percentage")
    def score_percentage_must_match_calculation(cls, v, values):
        """Validate that score_percentage matches calculation."""
        if "total_score" in values and "max_possible_score" in values:
            total_score = values["total_score"]
            max_possible_score = values["max_possible_score"]
            expected_percentage = (total_score / max_possible_score) * 100.0
            if abs(v - expected_percentage) > 0.01:  # Allow small floating point differences
                raise ValueError(f"Score percentage {v} doesn't match calculation {expected_percentage}")
        return v

    @validator("category_breakdowns")
    def category_breakdowns_must_have_required_dimensions(cls, v):
        """Validate that all required dimensions are present."""
        required_dimensions = {"code_quality", "testing", "documentation"}
        present_dimensions = set(v.keys())
        if not required_dimensions.issubset(present_dimensions):
            missing = required_dimensions - present_dimensions
            raise ValueError(f"Missing required dimensions: {missing}")
        return v

    def calculate_score_percentage(self) -> float:
        """Calculate score percentage from total score."""
        if self.max_possible_score == 0:
            return 0.0
        return (self.total_score / self.max_possible_score) * 100.0

    def update_totals_from_items(self) -> None:
        """Update total_score and score_percentage from checklist items."""
        self.total_score = sum(item.score for item in self.checklist_items)
        self.score_percentage = self.calculate_score_percentage()

    def get_items_by_dimension(self, dimension: str) -> List[ChecklistItem]:
        """Get all checklist items for a specific dimension."""
        return [item for item in self.checklist_items if item.dimension == dimension]

    def calculate_category_breakdown(self, dimension: str) -> CategoryBreakdown:
        """Calculate breakdown for a specific category dimension."""
        items = self.get_items_by_dimension(dimension)
        if not items:
            return CategoryBreakdown(
                dimension=dimension,
                items_count=0,
                max_points=0,
                actual_points=0.0,
                percentage=0.0
            )

        max_points = sum(item.max_points for item in items)
        actual_points = sum(item.score for item in items)
        percentage = (actual_points / max_points * 100.0) if max_points > 0 else 0.0

        return CategoryBreakdown(
            dimension=dimension,
            items_count=len(items),
            max_points=max_points,
            actual_points=actual_points,
            percentage=percentage
        )

    def update_category_breakdowns(self) -> None:
        """Update category breakdowns from current checklist items."""
        for dimension in ["code_quality", "testing", "documentation"]:
            self.category_breakdowns[dimension] = self.calculate_category_breakdown(dimension)

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"