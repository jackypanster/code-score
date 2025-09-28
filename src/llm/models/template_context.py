"""
Template context data structure.

This module defines the TemplateContext data structure for passing evaluation
data to Jinja2 template rendering with proper truncation and formatting.
"""

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from ...metrics.models.checklist_item import ChecklistItem
from ...metrics.models.evidence_reference import EvidenceReference


class RepositoryContext(BaseModel):
    """Repository information for template rendering."""

    url: str = Field(
        ...,
        description="Repository URL"
    )

    commit_sha: str = Field(
        ...,
        description="Commit SHA analyzed"
    )

    primary_language: str = Field(
        ...,
        description="Primary programming language"
    )

    analysis_timestamp: str = Field(
        ...,
        description="When analysis was performed (ISO format)"
    )

    branch_name: str | None = Field(
        None,
        description="Git branch analyzed"
    )

    repository_size_mb: float | None = Field(
        None,
        description="Repository size in megabytes"
    )


class ScoreContext(BaseModel):
    """Score information for template rendering."""

    score: float = Field(
        ...,
        description="Total evaluation score",
        ge=0.0,
        le=100.0
    )

    max_score: float = Field(
        ...,
        description="Maximum possible score",
        ge=0.0,
        le=100.0
    )

    percentage: float = Field(
        ...,
        description="Score as percentage",
        ge=0.0,
        le=100.0
    )

    @computed_field
    @property
    def grade_letter(self) -> str:
        """Letter grade (A-F) based on percentage."""
        if self.percentage >= 90:
            return "A"
        elif self.percentage >= 80:
            return "B"
        elif self.percentage >= 70:
            return "C"
        elif self.percentage >= 60:
            return "D"
        else:
            return "F"

    def calculate_grade(self) -> str:
        """Calculate letter grade from percentage."""
        return self.grade_letter


class CategoryScore(BaseModel):
    """Category-specific score breakdown."""

    score: float = Field(
        ...,
        description="Points earned in category",
        ge=0.0
    )

    max_points: float = Field(
        ...,
        description="Maximum points available",
        ge=0.0
    )

    percentage: float = Field(
        ...,
        description="Category score as percentage",
        ge=0.0,
        le=100.0
    )

    @computed_field
    @property
    def status(self) -> str:
        """Category status (excellent, good, needs_improvement, poor)."""
        if self.percentage >= 85:
            return "excellent"
        elif self.percentage >= 70:
            return "good"
        elif self.percentage >= 50:
            return "needs_improvement"
        else:
            return "poor"

    def calculate_status(self) -> str:
        """Calculate status from percentage."""
        return self.status


class ChecklistItemContext(BaseModel):
    """Simplified checklist item for template rendering."""

    id: str = Field(
        ...,
        description="Unique identifier"
    )

    name: str = Field(
        ...,
        description="Human-readable name"
    )

    dimension: str = Field(
        ...,
        description="Category dimension (code_quality, testing, documentation)"
    )

    evaluation_status: str = Field(
        ...,
        description="Status: met, partial, unmet"
    )

    score: float = Field(
        ...,
        description="Points earned",
        ge=0.0
    )

    max_points: float = Field(
        ...,
        description="Maximum points available",
        ge=0.0
    )

    description: str | None = Field(
        None,
        description="Brief description of what this item evaluates"
    )

    evidence_count: int = Field(
        default=0,
        description="Number of evidence items supporting this evaluation",
        ge=0
    )

    @classmethod
    def from_checklist_item(cls, item: ChecklistItem) -> 'ChecklistItemContext':
        """Create context from ChecklistItem model."""
        return cls(
            id=item.id,
            name=item.name,
            dimension=item.dimension,
            evaluation_status=item.evaluation_status,
            score=item.score,
            max_points=item.max_points,
            evidence_count=len(item.evidence_references) if item.evidence_references else 0
        )


class EvidenceContext(BaseModel):
    """Simplified evidence for template rendering."""

    source: str = Field(
        ...,
        description="Evidence source file or identifier"
    )

    description: str = Field(
        ...,
        description="Evidence description",
        max_length=200  # Truncated for templates
    )

    confidence: float = Field(
        ...,
        description="Confidence level",
        ge=0.0,
        le=1.0
    )

    category: str = Field(
        ...,
        description="Evidence category"
    )

    @classmethod
    def from_evidence_reference(cls, ref: EvidenceReference, category: str) -> 'EvidenceContext':
        """Create context from EvidenceReference model."""
        # Truncate description if too long
        description = ref.description
        if len(description) > 200:
            description = description[:197] + "..."

        return cls(
            source=ref.source,
            description=description,
            confidence=ref.confidence,
            category=category
        )


class EvidenceSummary(BaseModel):
    """Evidence summary by category."""

    category: str = Field(
        ...,
        description="Evidence category name"
    )

    items: list[EvidenceContext] = Field(
        default_factory=list,
        description="Evidence items for this category"
    )

    total_items: int = Field(
        default=0,
        description="Total number of evidence items (before truncation)",
        ge=0
    )

    truncated: bool = Field(
        default=False,
        description="Whether items were truncated"
    )


class TemplateContext(BaseModel):
    """
    Complete context data for template rendering.

    This structure contains all data needed for Jinja2 template rendering,
    with proper truncation and formatting for LLM context limits.
    """

    repository: RepositoryContext = Field(
        ...,
        description="Repository information"
    )

    total: ScoreContext = Field(
        ...,
        description="Overall score information"
    )

    category_scores: dict[str, CategoryScore] = Field(
        default_factory=dict,
        description="Score breakdown by category"
    )

    met_items: list[ChecklistItemContext] = Field(
        default_factory=list,
        description="Successfully completed checklist items"
    )

    partial_items: list[ChecklistItemContext] = Field(
        default_factory=list,
        description="Partially completed checklist items"
    )

    unmet_items: list[ChecklistItemContext] = Field(
        default_factory=list,
        description="Failed checklist items"
    )

    evidence_summary: list[EvidenceSummary] = Field(
        default_factory=list,
        description="Evidence organized by category (truncated for context limits)"
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Processing warnings and issues"
    )

    generation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about template generation process"
    )

    @field_validator('category_scores')
    @classmethod
    def validate_category_scores(cls, v):
        """Validate category scores structure."""
        expected_categories = ['code_quality', 'testing', 'documentation']

        for category in expected_categories:
            if category not in v:
                raise ValueError(f"Missing required category: {category}")

        return v

    def add_warning(self, warning: str) -> None:
        """Add a processing warning."""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def get_all_items(self) -> list[ChecklistItemContext]:
        """Get all checklist items regardless of status."""
        return self.met_items + self.partial_items + self.unmet_items

    def get_items_by_dimension(self, dimension: str) -> list[ChecklistItemContext]:
        """Get all items for a specific dimension."""
        return [item for item in self.get_all_items() if item.dimension == dimension]

    def get_score_summary(self) -> dict[str, int | float | str]:
        """Get summary statistics about scores."""
        all_items = self.get_all_items()

        return {
            'total_items': len(all_items),
            'met_count': len(self.met_items),
            'partial_count': len(self.partial_items),
            'unmet_count': len(self.unmet_items),
            'completion_rate': len(self.met_items) / len(all_items) if all_items else 0.0,
            'overall_grade': self.total.grade_letter,
            'needs_improvement': len(self.unmet_items) > len(self.met_items)
        }

    def get_evidence_counts(self) -> dict[str, int]:
        """Get evidence counts by category."""
        counts = {}
        for summary in self.evidence_summary:
            counts[summary.category] = len(summary.items)
        return counts

    def apply_content_limits(self, limits: dict[str, int]) -> None:
        """
        Apply content limits for LLM context management.

        Args:
            limits: Dictionary with limits (max_evidence_items, max_checklist_items, etc.)
        """
        max_evidence = limits.get('max_evidence_items', 3)
        max_description = limits.get('max_description_length', 200)

        # Truncate evidence items per category
        for summary in self.evidence_summary:
            if len(summary.items) > max_evidence:
                # Keep highest confidence items
                summary.items.sort(key=lambda x: x.confidence, reverse=True)
                original_count = len(summary.items)
                summary.items = summary.items[:max_evidence]
                summary.truncated = True
                summary.total_items = original_count

                self.add_warning(f"Evidence truncated in {summary.category}: "
                               f"{original_count} → {max_evidence} items")

            # Truncate descriptions
            for item in summary.items:
                if len(item.description) > max_description:
                    item.description = item.description[:max_description-3] + "..."

    def to_jinja_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary suitable for Jinja2 template rendering.

        Returns:
            Dictionary with all context data
        """
        return {
            'repository': self.repository.dict(),
            'total': self.total.dict(),
            'category_scores': {k: v.dict() for k, v in self.category_scores.items()},
            'met_items': [item.dict() for item in self.met_items],
            'partial_items': [item.dict() for item in self.partial_items],
            'unmet_items': [item.dict() for item in self.unmet_items],
            'evidence_summary': [summary.dict() for summary in self.evidence_summary],
            'warnings': self.warnings,
            'metadata': self.generation_metadata,
            'summary': self.get_score_summary(),
            'evidence_counts': self.get_evidence_counts()
        }

    @classmethod
    def from_score_input(cls, score_input_data: dict[str, Any]) -> 'TemplateContext':
        """
        Create TemplateContext from score_input.json data.

        This method parses structured evaluation results and creates a template-ready
        context object for LLM prompt generation. It handles categorization of checklist
        items by status and provides backward compatibility for different data formats.

        Args:
            score_input_data: Loaded score_input.json data containing:
                - repository_info: Repository metadata (url, commit, language)
                - evaluation_result: Complete evaluation with checklist items and scores
                - Optional evidence_summary and category_breakdowns

        Returns:
            TemplateContext instance with categorized items, scores, and metadata
            ready for Jinja2 template rendering

        Raises:
            KeyError: If required fields are missing from input data
            ValueError: If data format is invalid or incompatible

        Examples:
            >>> with open('score_input.json') as f:
            ...     data = json.load(f)
            >>> context = TemplateContext.from_score_input(data)
            >>> print(f"Total items: {len(context.get_all_items())}")
            >>> print(f"Met items: {len(context.met_items)}")
        """
        repo_info = score_input_data['repository_info']
        eval_result = score_input_data['evaluation_result']

        # Build repository context
        repository = RepositoryContext(
            url=repo_info['url'],
            commit_sha=repo_info['commit_sha'],
            primary_language=repo_info['primary_language'],
            analysis_timestamp=repo_info['analysis_timestamp']
        )

        # Build score context
        total_score = ScoreContext(
            score=eval_result['total_score'],
            max_score=eval_result['max_possible_score'],
            percentage=eval_result['score_percentage']
        )

        # Build category scores
        category_scores = {}
        for category, breakdown in eval_result['category_breakdowns'].items():
            # Handle both possible key formats for backward compatibility
            score_value = breakdown.get('score', breakdown.get('actual_points', 0.0))
            category_scores[category] = CategoryScore(
                score=score_value,
                max_points=breakdown['max_points'],
                percentage=breakdown['percentage']
            )

        # Organize checklist items by status
        met_items = []
        partial_items = []
        unmet_items = []

        for item_data in eval_result['checklist_items']:
            item = ChecklistItemContext(
                id=item_data['id'],
                name=item_data['name'],
                dimension=item_data['dimension'],
                evaluation_status=item_data['evaluation_status'],
                score=item_data['score'],
                max_points=item_data['max_points'],
                evidence_count=len(item_data.get('evidence_references', []))
            )

            if item.evaluation_status == 'met':
                met_items.append(item)
            elif item.evaluation_status == 'partial':
                partial_items.append(item)
            else:
                unmet_items.append(item)

        # Build evidence summary
        evidence_summary = []
        raw_evidence = eval_result.get('evidence_summary', [])

        if raw_evidence:
            # Handle actual format: list of strings from ChecklistEvaluator
            if isinstance(raw_evidence[0], str):
                # Group evidence strings by status for better organization
                met_evidence = []
                partial_evidence = []
                unmet_evidence = []

                for evidence_text in raw_evidence:
                    if evidence_text.startswith('✅'):
                        met_evidence.append(EvidenceContext(
                            source="checklist_evaluation",
                            description=evidence_text[2:].strip(),  # Remove emoji
                            confidence=1.0,
                            category="met_requirements"
                        ))
                    elif evidence_text.startswith('⚠️'):
                        partial_evidence.append(EvidenceContext(
                            source="checklist_evaluation",
                            description=evidence_text[2:].strip(),  # Remove emoji
                            confidence=0.5,
                            category="partial_requirements"
                        ))
                    elif evidence_text.startswith('❌'):
                        unmet_evidence.append(EvidenceContext(
                            source="checklist_evaluation",
                            description=evidence_text[2:].strip(),  # Remove emoji
                            confidence=0.0,
                            category="unmet_requirements"
                        ))

                # Create evidence summaries by category
                if met_evidence:
                    evidence_summary.append(EvidenceSummary(
                        category="met_requirements",
                        items=met_evidence,
                        total_items=len(met_evidence)
                    ))
                if partial_evidence:
                    evidence_summary.append(EvidenceSummary(
                        category="partial_requirements",
                        items=partial_evidence,
                        total_items=len(partial_evidence)
                    ))
                if unmet_evidence:
                    evidence_summary.append(EvidenceSummary(
                        category="unmet_requirements",
                        items=unmet_evidence,
                        total_items=len(unmet_evidence)
                    ))
            else:
                # Handle legacy format: list of dictionaries (for backward compatibility)
                for summary_data in raw_evidence:
                    evidence_items = []
                    for item_data in summary_data['items']:
                        evidence = EvidenceContext(
                            source=item_data['source'],
                            description=item_data['description'],
                            confidence=item_data['confidence'],
                            category=summary_data['category']
                        )
                        evidence_items.append(evidence)

                    evidence_summary.append(EvidenceSummary(
                        category=summary_data['category'],
                        items=evidence_items,
                        total_items=len(evidence_items)
                    ))

        return cls(
            repository=repository,
            total=total_score,
            category_scores=category_scores,
            met_items=met_items,
            partial_items=partial_items,
            unmet_items=unmet_items,
            evidence_summary=evidence_summary
        )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "repository": {
                    "url": "https://github.com/user/repo.git",
                    "commit_sha": "abc123456",
                    "primary_language": "python",
                    "analysis_timestamp": "2025-09-27T15:30:00Z"
                },
                "total": {
                    "score": 67.5,
                    "max_score": 100.0,
                    "percentage": 67.5,
                    "grade_letter": "C"
                },
                "met_items": [
                    {
                        "id": "code_quality_lint",
                        "name": "Static Linting Passed",
                        "dimension": "code_quality",
                        "evaluation_status": "met",
                        "score": 15.0,
                        "max_points": 15.0
                    }
                ]
            }
        }
