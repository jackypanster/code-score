"""EvidenceReference model for specific citations linking evaluation to source data."""

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    """Specific citation linking evaluation to source data."""

    source_type: Literal["lint_output", "test_result", "file_check", "security_audit", "documentation_analysis"] = Field(
        ..., description="Type of evidence source"
    )
    source_path: str = Field(..., description="JSON path or file reference to the evidence")
    description: str = Field(..., description="Human-readable explanation of the evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0.0 to 1.0)")
    raw_data: str = Field(default="", description="Optional excerpt of supporting data")

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.source_type}: {self.description} (confidence: {self.confidence:.2f})"

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if this evidence has high confidence."""
        return self.confidence >= threshold

    def get_summary(self) -> str:
        """Get a brief summary of this evidence."""
        confidence_label = "high" if self.is_high_confidence() else "medium" if self.confidence >= 0.5 else "low"
        return f"{self.description} ({confidence_label} confidence)"

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"
