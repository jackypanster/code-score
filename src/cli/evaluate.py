"""CLI evaluate command for running checklist evaluation on submission.json files."""

import click
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..metrics.checklist_evaluator import ChecklistEvaluator
from ..metrics.scoring_mapper import ScoringMapper
from ..metrics.evidence_tracker import EvidenceTracker
from ..metrics.checklist_loader import ChecklistLoader
from ..metrics.models.evaluation_result import RepositoryInfo


@click.command()
@click.argument('submission_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    default='output',
    help='Output directory for generated files (default: output)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'markdown', 'both']),
    default='both',
    help='Output format: json, markdown, or both (default: both)'
)
@click.option(
    '--checklist-config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to checklist configuration YAML file'
)
@click.option(
    '--evidence-dir', '-e',
    type=click.Path(path_type=Path),
    default='evidence',
    help='Directory for evidence files (default: evidence)'
)
@click.option(
    '--validate-only', '-v',
    is_flag=True,
    help='Only validate input without generating outputs'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress output except errors'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Show detailed evaluation progress'
)
def evaluate(
    submission_file: Path,
    output_dir: Path,
    format: str,
    checklist_config: Optional[Path],
    evidence_dir: Path,
    validate_only: bool,
    quiet: bool,
    verbose: bool
):
    """
    Evaluate a repository submission against the quality checklist.

    SUBMISSION_FILE: Path to the submission.json file to evaluate.

    This command processes a repository metrics submission and evaluates it against
    the 11-item quality checklist, generating structured output for downstream
    processing or human review.

    Examples:
        # Basic evaluation
        code-score evaluate submission.json

        # Custom output directory and format
        code-score evaluate submission.json -o results -f json

        # Validation only
        code-score evaluate submission.json -v

        # Verbose evaluation with custom checklist
        code-score evaluate submission.json -c custom_checklist.yaml --verbose
    """
    start_time = datetime.now()

    try:
        # Initialize components
        if verbose and not quiet:
            click.echo(f"🔍 Initializing checklist evaluation...")

        # Load checklist configuration
        if checklist_config:
            loader = ChecklistLoader(str(checklist_config))
        else:
            loader = ChecklistLoader()

        if verbose and not quiet:
            click.echo(f"📋 Loaded checklist configuration")

        # Validate checklist configuration
        validation = loader.validate_checklist_config()
        if not validation["valid"]:
            click.echo("❌ Checklist configuration validation failed:", err=True)
            for error in validation["errors"]:
                click.echo(f"   • {error}", err=True)
            sys.exit(1)

        if verbose and not quiet:
            stats = validation["statistics"]
            click.echo(f"   ✅ {stats['total_checklist_items']} items, {stats['total_max_points']} total points")

        # Load and validate submission file
        if verbose and not quiet:
            click.echo(f"📄 Loading submission file: {submission_file}")

        try:
            with open(submission_file, 'r', encoding='utf-8') as f:
                submission_data = json.load(f)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON in submission file: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error reading submission file: {e}", err=True)
            sys.exit(1)

        # Basic submission structure validation
        required_sections = ["repository", "metrics"]
        missing_sections = [section for section in required_sections if section not in submission_data]
        if missing_sections:
            click.echo(f"❌ Missing required sections in submission: {missing_sections}", err=True)
            sys.exit(1)

        if validate_only:
            if not quiet:
                click.echo("✅ Submission file validation passed")
            return

        # Initialize evaluator and evidence tracker
        evaluator = ChecklistEvaluator(str(checklist_config) if checklist_config else None)
        evidence_tracker = EvidenceTracker(str(output_dir / evidence_dir))

        if verbose and not quiet:
            click.echo("⚙️  Running evaluation...")

        # Run evaluation
        evaluation_result = evaluator.evaluate_from_dict(submission_data, str(submission_file))

        # Track evidence
        evidence_tracker.track_evaluation_evidence(evaluation_result)

        # Create repository info
        repo_data = submission_data.get("repository", {})
        repository_info = RepositoryInfo(
            url=repo_data.get("url", "unknown"),
            commit_sha=repo_data.get("commit", "unknown"),
            primary_language=repo_data.get("language", "unknown"),
            analysis_timestamp=datetime.fromisoformat(
                repo_data.get("timestamp", datetime.now().isoformat()).replace('Z', '+00:00')
            ),
            metrics_source=str(submission_file)
        )

        # Generate score input
        mapper = ScoringMapper(str(output_dir))
        score_input = mapper.map_to_score_input(
            evaluation_result=evaluation_result,
            repository_info=repository_info,
            submission_path=str(submission_file),
            evidence_base_path=str(evidence_dir)
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Save evidence files first
        if verbose and not quiet:
            click.echo("📁 Saving evidence files...")

        evidence_files = evidence_tracker.save_evidence_files()

        # Update evidence paths in score input before generating outputs
        mapper.update_evidence_paths_with_generated_files(score_input, evidence_files)

        # Generate outputs based on format selection (after evidence paths are updated)
        if format in ['json', 'both']:
            if verbose and not quiet:
                click.echo("📝 Generating score_input.json...")

            json_output_path = output_dir / "score_input.json"
            mapper.generate_score_input_json(score_input, str(json_output_path))
            generated_files.append(str(json_output_path))

        if format in ['markdown', 'both']:
            if verbose and not quiet:
                click.echo("📝 Generating evaluation report...")

            markdown_output_path = output_dir / "evaluation_report.md"
            mapper.generate_markdown_report(score_input, str(markdown_output_path))
            generated_files.append(str(markdown_output_path))

        # Generate final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if not quiet:
            click.echo("\n🎉 Evaluation completed successfully!")
            click.echo(f"📊 Score: {evaluation_result.total_score:.1f}/{evaluation_result.max_possible_score} ({evaluation_result.score_percentage:.1f}%)")

            # Show category breakdown
            click.echo("\n📈 Category Breakdown:")
            for dimension, breakdown in evaluation_result.category_breakdowns.items():
                percentage = breakdown.percentage
                grade = get_letter_grade(percentage)
                click.echo(f"   {dimension.replace('_', ' ').title()}: {breakdown.actual_points:.1f}/{breakdown.max_points} ({percentage:.1f}%, Grade: {grade})")

            # Show status distribution
            met_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "met")
            partial_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "partial")
            unmet_count = sum(1 for item in evaluation_result.checklist_items if item.evaluation_status == "unmet")

            click.echo(f"\n📋 Items: {met_count} met, {partial_count} partial, {unmet_count} unmet")

            if evaluation_result.evaluation_metadata.warnings:
                click.echo(f"\n⚠️  Warnings ({len(evaluation_result.evaluation_metadata.warnings)}):")
                for warning in evaluation_result.evaluation_metadata.warnings:
                    click.echo(f"   • {warning}")

            click.echo(f"\n📁 Generated Files:")
            for file_path in generated_files:
                click.echo(f"   • {file_path}")

            click.echo(f"📁 Evidence Files: {len(evidence_files)} files in {output_dir / evidence_dir}")
            click.echo(f"⏱️  Processing Time: {duration:.2f} seconds")

        # Exit with non-zero code if score is very low (optional quality gate)
        if evaluation_result.score_percentage < 30:
            if not quiet:
                click.echo(f"\n⚠️  Quality gate: Score below 30% threshold", err=True)
            sys.exit(2)

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"❌ Validation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


def get_letter_grade(percentage: float) -> str:
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


# Allow running as standalone script for testing
def main():
    """Main entry point for standalone execution."""
    evaluate()


if __name__ == '__main__':
    main()