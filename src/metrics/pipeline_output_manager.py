"""Enhanced output manager for pipeline integration with checklist evaluation."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .checklist_evaluator import ChecklistEvaluator
from .evidence_tracker import EvidenceTracker
from .scoring_mapper import ScoringMapper
from .submission_pipeline import PipelineIntegrator
from .models.evaluation_result import EvaluationResult, RepositoryInfo


class PipelineOutputManager:
    """Manages output generation for the integrated pipeline including checklist evaluation."""

    def __init__(self,
                 output_dir: str,
                 checklist_config_path: Optional[str] = None,
                 enable_checklist_evaluation: bool = True,
                 enable_llm_report: bool = False,
                 llm_provider: str = "gemini",
                 llm_template_path: Optional[str] = None):
        """
        Initialize the pipeline output manager.

        Args:
            output_dir: Base output directory
            checklist_config_path: Path to checklist configuration YAML
            enable_checklist_evaluation: Whether to run checklist evaluation
            enable_llm_report: Whether to generate LLM reports
            llm_provider: LLM provider to use for report generation
            llm_template_path: Path to custom LLM template
        """
        self.output_dir = Path(output_dir)
        self.enable_checklist_evaluation = enable_checklist_evaluation
        self.enable_llm_report = enable_llm_report
        self.llm_provider = llm_provider
        self.llm_template_path = llm_template_path

        # Initialize components
        if enable_checklist_evaluation:
            if checklist_config_path is None:
                # Default to the checklist mapping in the contracts directory
                base_path = Path(__file__).parent.parent.parent / "specs" / "contracts"
                config_path = str(base_path / "checklist_mapping.yaml")
            else:
                config_path = checklist_config_path
            self.checklist_evaluator = ChecklistEvaluator(config_path)
            self.scoring_mapper = ScoringMapper(output_base_path=str(self.output_dir))
            self.pipeline_integrator = PipelineIntegrator()
        else:
            self.checklist_evaluator = None
            self.scoring_mapper = None
            self.pipeline_integrator = None

        # Initialize LLM report generator if enabled
        if enable_llm_report:
            try:
                from ..llm.report_generator import ReportGenerator
                self.llm_generator = ReportGenerator()
            except ImportError:
                print("⚠️  LLM report generation not available - missing dependencies")
                self.enable_llm_report = False
                self.llm_generator = None
        else:
            self.llm_generator = None

    def process_submission_with_checklist(self,
                                        submission_path: str,
                                        output_format: str = "both") -> Dict[str, List[str]]:
        """
        Process a submission.json file and generate all outputs including checklist evaluation.

        Args:
            submission_path: Path to the submission.json file
            output_format: Output format ("json", "markdown", or "both")

        Returns:
            Dictionary mapping output type to list of generated file paths
        """
        generated_files = {
            "original": [],
            "checklist": [],
            "evidence": []
        }

        if not self.enable_checklist_evaluation:
            raise ValueError("Checklist evaluation is disabled")

        # Step 1: Load and validate submission
        submission_data, warnings = self.pipeline_integrator.prepare_submission_for_evaluation(submission_path)

        # Step 2: Check if we should run evaluation
        if not self.pipeline_integrator.should_run_checklist_evaluation(submission_data):
            print("⚠️  Insufficient data for meaningful checklist evaluation")
            return generated_files

        # Step 3: Run checklist evaluation
        try:
            evaluation_result = self.checklist_evaluator.evaluate_from_dict(submission_data, submission_path)
        except Exception as e:
            print(f"❌ Checklist evaluation failed: {e}")
            return generated_files

        # Step 4: Generate outputs
        if "json" in output_format or output_format == "both":
            json_files = self._generate_json_outputs(evaluation_result, submission_data, warnings, submission_path)
            generated_files["checklist"].extend(json_files)

        if "markdown" in output_format or output_format == "both":
            markdown_files = self._generate_markdown_outputs(evaluation_result, warnings)
            generated_files["checklist"].extend(markdown_files)

        # Step 5: Generate evidence files
        evidence_files = self._generate_evidence_files(evaluation_result)
        generated_files["evidence"].extend(evidence_files)

        return generated_files

    def _generate_json_outputs(self,
                             evaluation_result: EvaluationResult,
                             submission_data: Dict[str, Any],
                             warnings: List[str],
                             submission_path: str) -> List[str]:
        """Generate JSON format outputs."""
        output_files = []

        # Generate score_input.json
        repository_info_dict = self.pipeline_integrator.submission_loader.extract_repository_info(submission_data)

        # Convert to RepositoryInfo object
        timestamp_str = repository_info_dict.get("analysis_timestamp", "unknown")
        if timestamp_str != "unknown":
            try:
                # Parse ISO format timestamp
                analysis_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                analysis_timestamp = datetime.now()
        else:
            analysis_timestamp = datetime.now()

        repository_info = RepositoryInfo(
            url=repository_info_dict["url"],
            commit_sha=repository_info_dict["commit_sha"],
            primary_language=repository_info_dict["primary_language"],
            analysis_timestamp=analysis_timestamp,
            metrics_source=repository_info_dict["metrics_source"]
        )

        score_input = self.scoring_mapper.map_to_score_input(
            evaluation_result, repository_info, submission_path
        )

        # Add warnings to evaluation result metadata
        if warnings:
            evaluation_result.evaluation_metadata.warnings.extend(warnings)

        # Save score_input.json
        score_input_path = self.output_dir / "score_input.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(score_input_path, 'w') as f:
            json.dump(score_input.model_dump(), f, indent=2, default=str)

        output_files.append(str(score_input_path))

        # Generate evaluation_result.json (detailed results)
        result_path = self.output_dir / "evaluation_result.json"
        with open(result_path, 'w') as f:
            json.dump(evaluation_result.model_dump(), f, indent=2, default=str)

        output_files.append(str(result_path))

        return output_files

    def _generate_markdown_outputs(self,
                                 evaluation_result: EvaluationResult,
                                 warnings: List[str]) -> List[str]:
        """Generate Markdown format outputs."""
        output_files = []

        # Generate evaluation_report.md
        report_content = self._create_markdown_report(evaluation_result, warnings)
        report_path = self.output_dir / "evaluation_report.md"

        with open(report_path, 'w') as f:
            f.write(report_content)

        output_files.append(str(report_path))

        return output_files

    def _generate_evidence_files(self, evaluation_result: EvaluationResult) -> List[str]:
        """Generate evidence files from evaluation result."""
        evidence_dir = self.output_dir / "evidence"
        tracker = EvidenceTracker(str(evidence_dir))

        # Track evidence for the entire evaluation result
        tracker.track_evaluation_evidence(evaluation_result)

        # Save evidence files - this returns Dict[str, str] mapping evidence_key -> file_path
        evidence_files_dict = tracker.save_evidence_files()

        # Extract the actual file paths (values) from the dictionary
        return list(evidence_files_dict.values())

    def _create_markdown_report(self,
                              evaluation_result: EvaluationResult,
                              warnings: List[str]) -> str:
        """Create a comprehensive Markdown evaluation report."""
        lines = []

        # Header
        lines.append("# Code Quality Evaluation Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"**Overall Score**: {evaluation_result.total_score:.1f}/{evaluation_result.max_possible_score} ({evaluation_result.score_percentage:.1f}%)")
        lines.append("")

        # Category Breakdown
        lines.append("## Category Breakdown")
        lines.append("")
        for dimension, breakdown in evaluation_result.category_breakdowns.items():
            grade = self._calculate_grade(breakdown.percentage)
            lines.append(f"### {dimension.replace('_', ' ').title()}")
            lines.append(f"- **Score**: {breakdown.actual_points:.1f}/{breakdown.max_points} ({breakdown.percentage:.1f}%)")
            lines.append(f"- **Grade**: {grade}")
            lines.append(f"- **Items**: {breakdown.items_count}")
            lines.append("")

        # Detailed Results
        lines.append("## Detailed Results")
        lines.append("")

        # Group items by status
        met_items = [item for item in evaluation_result.checklist_items if item.evaluation_status == "met"]
        partial_items = [item for item in evaluation_result.checklist_items if item.evaluation_status == "partial"]
        unmet_items = [item for item in evaluation_result.checklist_items if item.evaluation_status == "unmet"]

        if met_items:
            lines.append("### ✅ Met Criteria")
            for item in met_items:
                lines.append(f"- **{item.name}** ({item.score:.1f}/{item.max_points} points)")
                lines.append(f"  - {item.description}")
            lines.append("")

        if partial_items:
            lines.append("### ⚠️ Partially Met Criteria")
            for item in partial_items:
                lines.append(f"- **{item.name}** ({item.score:.1f}/{item.max_points} points)")
                lines.append(f"  - {item.description}")
            lines.append("")

        if unmet_items:
            lines.append("### ❌ Unmet Criteria")
            for item in unmet_items:
                lines.append(f"- **{item.name}** ({item.score:.1f}/{item.max_points} points)")
                lines.append(f"  - {item.description}")
            lines.append("")

        # Warnings
        if warnings:
            lines.append("## Evaluation Warnings")
            lines.append("")
            for warning in warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        # Evidence Summary
        if evaluation_result.evidence_summary:
            lines.append("## Evidence Summary")
            lines.append("")
            for evidence in evaluation_result.evidence_summary:
                lines.append(f"- {evidence}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Code Score Checklist Evaluation System*")

        return "\n".join(lines)

    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage."""
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

    def integrate_with_existing_pipeline(self,
                                       existing_output_files: List[str],
                                       submission_path: str) -> List[str]:
        """
        Integrate checklist evaluation with existing pipeline outputs.

        Args:
            existing_output_files: Files generated by the existing pipeline
            submission_path: Path to the submission.json file

        Returns:
            List of all generated files (existing + new)
        """
        all_files = list(existing_output_files)

        if not self.enable_checklist_evaluation:
            return all_files

        try:
            # Run checklist evaluation and generate additional outputs
            checklist_outputs = self.process_submission_with_checklist(submission_path, "both")

            # Add all generated files
            for category, files in checklist_outputs.items():
                all_files.extend(files)

            # Generate LLM report if enabled and score_input.json exists
            if self.enable_llm_report:
                llm_files = self._generate_llm_report(all_files)
                all_files.extend(llm_files)

            return all_files

        except Exception as e:
            print(f"⚠️  Checklist evaluation failed but existing pipeline succeeded: {e}")
            return all_files

    def _generate_llm_report(self, existing_files: List[str]) -> List[str]:
        """
        Generate LLM report from score_input.json if available.

        Args:
            existing_files: List of existing output files

        Returns:
            List of generated LLM report files
        """
        if not self.enable_llm_report or not self.llm_generator:
            return []

        try:
            # Find score_input.json file
            score_input_file = None
            for file_path in existing_files:
                if file_path.endswith('score_input.json'):
                    score_input_file = file_path
                    break

            if not score_input_file:
                print("⚠️  No score_input.json found, skipping LLM report generation")
                return []

            # Validate prerequisites
            validation_result = self.llm_generator.validate_prerequisites(self.llm_provider)
            if not validation_result['valid']:
                print(f"⚠️  LLM prerequisites not met, skipping report generation:")
                for issue in validation_result['issues']:
                    print(f"    • {issue}")
                return []

            # Generate final report
            final_report_path = str(self.output_dir / "final_report.md")

            result = self.llm_generator.generate_report(
                score_input_path=score_input_file,
                output_path=final_report_path,
                template_path=self.llm_template_path,
                provider=self.llm_provider,
                verbose=False  # Keep quiet in pipeline mode
            )

            if result.get('success'):
                print(f"✅ LLM report generated: {final_report_path}")
                return [final_report_path]
            else:
                print("⚠️  LLM report generation failed")
                return []

        except Exception as e:
            print(f"⚠️  LLM report generation error: {e}")
            return []