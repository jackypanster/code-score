"""CategoryBreakdown model for score breakdown by evaluation dimension."""

from pydantic import BaseModel, Field, validator


class CategoryBreakdown(BaseModel):
    """Score breakdown by evaluation dimension."""

    dimension: str = Field(..., description="Category name")
    items_count: int = Field(..., description="Number of items in category")
    max_points: int = Field(..., description="Maximum possible points")
    actual_points: float = Field(..., description="Achieved points")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Category percentage score")

    @validator("percentage")
    def percentage_must_match_calculation(cls, v, values):
        """Validate that percentage matches calculation."""
        if "max_points" in values and "actual_points" in values:
            max_points = values["max_points"]
            actual_points = values["actual_points"]
            if max_points > 0:
                expected_percentage = (actual_points / max_points) * 100.0
                if abs(v - expected_percentage) > 0.01:  # Allow small floating point differences
                    raise ValueError(f"Percentage {v} doesn't match calculation {expected_percentage}")
        return v

    @validator("dimension")
    def dimension_must_be_valid(cls, v):
        """Validate that dimension is one of the expected values."""
        valid_dimensions = {"code_quality", "testing", "documentation"}
        if v not in valid_dimensions:
            raise ValueError(f"Dimension must be one of {valid_dimensions}, got {v}")
        return v

    def calculate_percentage(self) -> float:
        """Calculate percentage from points."""
        if self.max_points == 0:
            return 0.0
        return (self.actual_points / self.max_points) * 100.0

    def update_percentage(self) -> None:
        """Update percentage based on current points."""
        self.percentage = self.calculate_percentage()

    def is_perfect_score(self) -> bool:
        """Check if this category achieved perfect score."""
        return abs(self.actual_points - self.max_points) < 0.01

    def get_grade(self) -> str:
        """Get letter grade based on percentage."""
        if self.percentage >= 90.0:
            return "A"
        elif self.percentage >= 80.0:
            return "B"
        elif self.percentage >= 70.0:
            return "C"
        elif self.percentage >= 60.0:
            return "D"
        else:
            return "F"

    def get_summary(self) -> str:
        """Get a brief summary of this category's performance."""
        grade = self.get_grade()
        return f"{self.dimension.replace('_', ' ').title()}: {self.actual_points:.1f}/{self.max_points} ({self.percentage:.1f}%, Grade: {grade})"

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"
