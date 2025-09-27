"""ChecklistItem model for individual checklist evaluation criteria."""

from typing import List, Literal
from pydantic import BaseModel, Field, validator

from .evidence_reference import EvidenceReference


class ChecklistItem(BaseModel):
    """Represents one of the 11 evaluation criteria from ai-code-review-judgement.md."""

    id: str = Field(..., description="Unique identifier (e.g., 'code_quality_lint')")
    name: str = Field(..., description="Human-readable name (e.g., 'Static Linting Passed')")
    dimension: Literal["code_quality", "testing", "documentation"]
    max_points: int = Field(..., description="Maximum possible points for this item")
    description: str = Field(..., description="Evaluation criteria description")
    evaluation_status: Literal["met", "partial", "unmet"] = Field(default="unmet")
    score: float = Field(default=0.0, ge=0.0, description="Calculated score for this item")
    evidence_references: List[EvidenceReference] = Field(default_factory=list)

    @validator("score")
    def score_must_not_exceed_max_points(cls, v, values):
        """Validate that score doesn't exceed max_points."""
        if "max_points" in values and v > values["max_points"]:
            raise ValueError(f"Score {v} cannot exceed max_points {values['max_points']}")
        return v

    @validator("max_points")
    def max_points_must_be_valid(cls, v):
        """Validate that max_points is one of the expected values from the checklist."""
        valid_points = {4, 6, 7, 8, 10, 12, 15}
        if v not in valid_points:
            raise ValueError(f"max_points must be one of {valid_points}, got {v}")
        return v

    def calculate_score_from_status(self) -> float:
        """Calculate score based on evaluation status."""
        if self.evaluation_status == "met":
            return float(self.max_points)
        elif self.evaluation_status == "partial":
            return float(self.max_points) * 0.5
        else:  # unmet
            return 0.0

    def add_evidence(
        self,
        source_type: str,
        source_path: str,
        description: str,
        confidence: float,
        raw_data: str = ""
    ) -> None:
        """Add evidence reference to support the evaluation."""
        evidence = EvidenceReference(
            source_type=source_type,
            source_path=source_path,
            description=description,
            confidence=confidence,
            raw_data=raw_data
        )
        self.evidence_references.append(evidence)

    def update_status_and_score(self, status: Literal["met", "partial", "unmet"]) -> None:
        """Update evaluation status and recalculate score."""
        self.evaluation_status = status
        self.score = self.calculate_score_from_status()

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"