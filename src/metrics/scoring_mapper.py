"""ScoringMapper class for transforming evaluation results to ScoreInput format."""

from datetime import datetime
from pathlib import Path

from .models.evaluation_result import EvaluationResult, RepositoryInfo
from .models.score_input import ScoreInput


class ScoringMapper:
    """Maps evaluation results to structured ScoreInput format for downstream processing."""

    def __init__(self, output_base_path: str = "output"):
        """Initialize mapper with output configuration."""
        self.output_base_path = Path(output_base_path)
        self.schema_version = "1.0.0"

    def map_to_score_input(
        self,
        evaluation_result: EvaluationResult,
        repository_info: RepositoryInfo,
        submission_path: str,
        evidence_base_path: str = "evidence"
    ) -> ScoreInput:
        """Transform EvaluationResult to ScoreInput format."""

        # Generate evidence paths mapping
        evidence_paths = self._generate_evidence_paths(evaluation_result, evidence_base_path)

        # Generate human summary
        human_summary = self._generate_comprehensive_summary(evaluation_result, repository_info)

        # Create ScoreInput object
        score_input = ScoreInput(
            schema_version=self.schema_version,
            repository_info=repository_info,
            evaluation_result=evaluation_result,
            generation_timestamp=datetime.now(),
            evidence_paths=evidence_paths,
            human_summary=human_summary
        )

        return score_input

    def _generate_evidence_paths(self, evaluation_result: EvaluationResult, evidence_base_path: str) -> dict[str, str]:
        """Generate mapping of evidence types to file paths.

        Only includes paths that point to existing files to ensure reliability
        for downstream systems consuming the evidence_paths.
        """
        evidence_paths = {}

        for item in evaluation_result.checklist_items:
            for evidence in item.evidence_references:
                evidence_key = f"{item.id}_{evidence.source_type}"
                evidence_file = f"{evidence_base_path}/{item.dimension}/{item.id}_{evidence.source_type}.json"

                # Only include evidence files that actually exist
                if Path(evidence_file).exists():
                    evidence_paths[evidence_key] = evidence_file

        # Note: Removed phantom path generation for non-existent files
        # Previously generated paths for evaluation_summary.json, category_breakdowns.json, warnings.log
        # that were never actually created by EvidenceTracker

        return evidence_paths

    def _generate_comprehensive_summary(self, evaluation_result: EvaluationResult, repository_info: RepositoryInfo) -> str:
        """Generate comprehensive markdown summary for human review."""
        lines = [
            "# Code Quality Evaluation Report",
            "",
            f"**Repository:** {repository_info.url}",
            f"**Commit:** {repository_info.commit_sha}",
            f"**Language:** {repository_info.primary_language}",
            f"**Analysis Date:** {repository_info.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Evaluation Version:** {evaluation_result.evaluation_metadata.evaluator_version}",
            "",
            "## Executive Summary",
            "",
            f"**Overall Score:** {evaluation_result.total_score:.1f} / {evaluation_result.max_possible_score} ({evaluation_result.score_percentage:.1f}%)",
            f"**Processing Time:** {evaluation_result.evaluation_metadata.processing_duration:.2f} seconds",
            f"**Metrics Completeness:** {evaluation_result.evaluation_metadata.metrics_completeness:.1f}%",
            "",
            self._get_grade_assessment(evaluation_result.score_percentage),
            ""
        ]

        # Category breakdown section
        lines.extend([
            "## Category Performance",
            ""
        ])

        for dimension, breakdown in evaluation_result.category_breakdowns.items():
            grade = self._get_letter_grade(breakdown.percentage)
            lines.extend([
                f"### {dimension.replace('_', ' ').title()} - Grade {grade}",
                f"- **Score:** {breakdown.actual_points:.1f} / {breakdown.max_points} ({breakdown.percentage:.1f}%)",
                f"- **Items Evaluated:** {breakdown.items_count}",
                ""
            ])

        # Detailed checklist results
        lines.extend([
            "## Detailed Checklist Results",
            ""
        ])

        # Group items by dimension
        by_dimension = {}
        for item in evaluation_result.checklist_items:
            if item.dimension not in by_dimension:
                by_dimension[item.dimension] = []
            by_dimension[item.dimension].append(item)

        for dimension in ["code_quality", "testing", "documentation"]:
            if dimension in by_dimension:
                lines.extend([
                    f"### {dimension.replace('_', ' ').title()}",
                    ""
                ])

                for item in by_dimension[dimension]:
                    status_icon = self._get_status_icon(item.evaluation_status)
                    lines.extend([
                        f"#### {status_icon} {item.name}",
                        f"- **Status:** {item.evaluation_status.upper()}",
                        f"- **Score:** {item.score:.1f} / {item.max_points}",
                        f"- **Criteria:** {item.description}",
                        ""
                    ])

                    # Add evidence details if available
                    if item.evidence_references:
                        lines.append("**Evidence:**")
                        for evidence in item.evidence_references:
                            confidence_label = self._get_confidence_label(evidence.confidence)
                            lines.append(f"- {evidence.description} ({confidence_label} confidence)")
                        lines.append("")

        # Key insights section
        lines.extend([
            "## Key Insights",
            ""
        ])

        insights = self._generate_insights(evaluation_result)
        for insight in insights:
            lines.append(f"- {insight}")

        # Warnings section
        if evaluation_result.evaluation_metadata.warnings:
            lines.extend([
                "",
                "## Warnings & Issues",
                ""
            ])
            for warning in evaluation_result.evaluation_metadata.warnings:
                lines.append(f"- ⚠️ {warning}")

        # Recommendations section
        lines.extend([
            "",
            "## Recommendations",
            ""
        ])

        recommendations = self._generate_recommendations(evaluation_result)
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")

        lines.extend([
            "",
            "---",
            f"*Report generated at {datetime.now().isoformat()} by ChecklistEvaluator v{evaluation_result.evaluation_metadata.evaluator_version}*"
        ])

        return "\n".join(lines)

    def _get_grade_assessment(self, percentage: float) -> str:
        """Get textual assessment of the overall grade."""
        if percentage >= 90:
            return "**Grade: A** - Excellent code quality with comprehensive coverage across all dimensions."
        elif percentage >= 80:
            return "**Grade: B** - Good code quality with minor areas for improvement."
        elif percentage >= 70:
            return "**Grade: C** - Acceptable code quality with several areas needing attention."
        elif percentage >= 60:
            return "**Grade: D** - Below-average code quality requiring significant improvements."
        else:
            return "**Grade: F** - Poor code quality requiring major refactoring and improvements."

    def _get_letter_grade(self, percentage: float) -> str:
        """Get letter grade for percentage."""
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

    def _get_status_icon(self, status: str) -> str:
        """Get icon for evaluation status."""
        return {
            "met": "✅",
            "partial": "⚠️",
            "unmet": "❌"
        }.get(status, "❓")

    def _get_confidence_label(self, confidence: float) -> str:
        """Get human-readable confidence label."""
        if confidence >= 0.9:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"

    def _generate_insights(self, evaluation_result: EvaluationResult) -> list[str]:
        """Generate key insights about the evaluation."""
        insights = []

        # Score distribution insights
        met_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "met")
        partial_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "partial")
        unmet_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "unmet")

        insights.append(f"Score distribution: {met_count} items fully met, {partial_count} partially met, {unmet_count} unmet")

        # Category insights
        best_category = max(evaluation_result.category_breakdowns.items(), key=lambda x: x[1].percentage)
        worst_category = min(evaluation_result.category_breakdowns.items(), key=lambda x: x[1].percentage)

        insights.append(f"Strongest area: {best_category[0].replace('_', ' ').title()} ({best_category[1].percentage:.1f}%)")
        insights.append(f"Weakest area: {worst_category[0].replace('_', ' ').title()} ({worst_category[1].percentage:.1f}%)")

        # Metrics completeness insight
        if evaluation_result.evaluation_metadata.metrics_completeness < 80:
            insights.append(f"Limited metrics available ({evaluation_result.evaluation_metadata.metrics_completeness:.1f}% completeness) - scores may not reflect full project quality")

        return insights

    def _generate_recommendations(self, evaluation_result: EvaluationResult) -> list[str]:
        """Generate actionable recommendations based on evaluation."""
        recommendations = []

        # Analyze unmet items for recommendations
        unmet_items = [item for item in evaluation_result.checklist_items if item.evaluation_status == "unmet"]

        if unmet_items:
            # Group by dimension for targeted recommendations
            unmet_by_dimension = {}
            for item in unmet_items:
                if item.dimension not in unmet_by_dimension:
                    unmet_by_dimension[item.dimension] = []
                unmet_by_dimension[item.dimension].append(item)

            if "code_quality" in unmet_by_dimension:
                recommendations.append("Implement static linting (e.g., ruff for Python, eslint for JavaScript)")
                recommendations.append("Set up automated builds and dependency security scanning")

            if "testing" in unmet_by_dimension:
                recommendations.append("Add automated tests with coverage reporting (target: >60% coverage)")
                recommendations.append("Implement integration tests to validate core functionality")

            if "documentation" in unmet_by_dimension:
                recommendations.append("Create comprehensive README with setup instructions and usage examples")
                recommendations.append("Document API interfaces and configuration requirements")

        # Score-based recommendations
        if evaluation_result.score_percentage < 70:
            recommendations.append("Focus on foundational items: linting, basic tests, and README documentation")
            recommendations.append("Consider establishing CI/CD pipeline for automated quality checks")

        return recommendations

    def generate_score_input_json(self, score_input: ScoreInput, output_path: str) -> str:
        """Generate and save score_input.json file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable dict
        score_input_dict = score_input.to_json_dict()

        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(score_input_dict, f, indent=2, ensure_ascii=False)

        return str(output_file)

    def generate_markdown_report(self, score_input: ScoreInput, output_path: str) -> str:
        """Generate and save markdown report file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(score_input.human_summary)

        return str(output_file)

    def update_evidence_paths_with_generated_files(self, score_input: ScoreInput, generated_files: dict[str, str]) -> None:
        """Update evidence paths with actual generated file paths.

        Ensures that only existing files are included in evidence_paths
        and removes any phantom paths that may have been generated.
        """
        from .models.evidence_validation import clean_evidence_paths

        # First, clean any existing phantom paths from the current evidence_paths
        cleaned_current_paths = clean_evidence_paths(score_input.evidence_paths)

        # Then, clean the generated files to ensure they exist
        cleaned_generated_files = clean_evidence_paths(generated_files)

        # Update with cleaned paths only
        score_input.evidence_paths = cleaned_current_paths
        score_input.evidence_paths.update(cleaned_generated_files)
