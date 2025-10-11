"""Main CLI interface for Code Score metrics collection."""

import sys
from pathlib import Path

import click

from ..metrics.cleanup import get_cleanup_manager
from ..metrics.error_handling import ToolchainValidationError, get_error_handler
from ..metrics.git_operations import GitOperationError, GitOperations
from ..metrics.language_detection import LanguageDetector
from ..metrics.output_generators import OutputManager
from ..metrics.tool_executor import ToolExecutor
from ..metrics.toolchain_manager import ToolchainManager


@click.command()
@click.argument('repository_url')
@click.argument('commit_sha', required=False)
@click.option('--output-dir', default='./output', help='Output directory for results')
@click.option('--format', 'output_format', default='both',
              type=click.Choice(['json', 'markdown', 'both']),
              help='Output format')
@click.option('--timeout', default=300, help='Analysis timeout in seconds')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--skip-toolchain-check', is_flag=True, default=False, help='Skip toolchain validation (emergency bypass)')
@click.option('--enable-checklist', type=bool, default=True, help='Enable checklist evaluation (default: enabled)')
@click.option('--checklist-config', help='Path to checklist configuration YAML file')
@click.option('--generate-llm-report', is_flag=True, default=False, help='Generate human-readable LLM report using Gemini after analysis')
@click.option('--llm-template', help='Path to custom LLM prompt template')
def main(repository_url: str, commit_sha: str | None, output_dir: str,
         output_format: str, timeout: int, verbose: bool, skip_toolchain_check: bool,
         enable_checklist: bool, checklist_config: str | None,
         generate_llm_report: bool, llm_template: str | None) -> None:
    """
    Analyze code quality metrics for a Git repository.

    REPOSITORY_URL: Git repository URL to analyze
    COMMIT_SHA: Optional specific commit to analyze
    """
    # Initialize error handling and cleanup
    error_handler = get_error_handler(verbose=verbose)
    cleanup_manager = get_cleanup_manager()

    try:
        if verbose:
            click.echo(f"Starting analysis of {repository_url}")
            if commit_sha:
                click.echo(f"Target commit: {commit_sha}")

        # Initialize components
        git_ops = GitOperations(timeout_seconds=timeout)
        language_detector = LanguageDetector()
        tool_executor = ToolExecutor(timeout_seconds=timeout)
        output_manager = OutputManager(output_dir=output_dir)

        # Step 1: Clone repository
        if verbose:
            click.echo("Cloning repository...")

        try:
            repository = git_ops.clone_repository(repository_url, commit_sha)
        except GitOperationError as e:
            error_handler.handle_repository_failure(repository_url, e)
            click.echo(f"Error: Failed to clone repository: {e}", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"Repository cloned to: {repository.local_path}")

        try:
            # Step 2: Detect language
            if verbose:
                click.echo("Detecting primary language...")

            detected_language = language_detector.detect_primary_language(repository.local_path)
            repository.detected_language = detected_language

            if verbose:
                click.echo(f"Detected language: {detected_language}")

            # Step 3: Toolchain validation (FR-001, FR-003)
            # Validate all required tools for the detected language before analysis
            if not skip_toolchain_check:
                if verbose:
                    click.echo(f"Validating toolchain for {detected_language}...")

                try:
                    toolchain_manager = ToolchainManager()
                    report = toolchain_manager.validate_for_language(detected_language)

                    # Validation passed - print success message (FR-009)
                    if verbose:
                        click.echo(report.format_error_message())

                except ToolchainValidationError as e:
                    # Validation failed - print error and exit immediately (FR-003)
                    click.echo(f"✗ 工具链验证失败:", err=True)
                    click.echo(e.message, err=True)

                    # Clean up cloned repository before exiting
                    try:
                        git_ops.cleanup_repository(repository)
                    except Exception:
                        pass  # Ignore cleanup errors when already failing

                    sys.exit(1)
            else:
                # Skip flag used - print warning
                click.echo("⚠ 警告: 已跳过工具链验证 (--skip-toolchain-check)", err=True)

            # Step 4: Execute analysis tools
            if verbose:
                click.echo("Running analysis tools...")

            metrics = tool_executor.execute_tools(detected_language, repository.local_path)

            if verbose:
                tools_used = metrics.execution_metadata.tools_used
                click.echo(f"Tools executed: {', '.join(tools_used) if tools_used else 'none'}")

            # Step 4: Generate output
            if verbose:
                click.echo(f"Generating {output_format} output...")

            saved_files = output_manager.save_results(repository, metrics, output_format)

            # Step 4.5: Checklist evaluation integration
            if enable_checklist:
                try:
                    if verbose:
                        click.echo("Running checklist evaluation...")

                    from ..metrics.pipeline_output_manager import PipelineOutputManager

                    # Initialize pipeline output manager
                    pipeline_manager = PipelineOutputManager(
                        output_dir=output_dir,
                        checklist_config_path=checklist_config,
                        enable_checklist_evaluation=True
                    )

                    # Find submission.json in the output files
                    submission_file = None
                    for file_path in saved_files:
                        if file_path.endswith('submission.json'):
                            submission_file = file_path
                            break

                    if submission_file:
                        # Integrate checklist evaluation
                        all_files = pipeline_manager.integrate_with_existing_pipeline(
                            saved_files, submission_file
                        )
                        saved_files = all_files

                        if verbose:
                            click.echo("✅ Checklist evaluation completed")
                    else:
                        if verbose:
                            click.echo("⚠️  No submission.json found, skipping checklist evaluation")

                except Exception as e:
                    if verbose:
                        click.echo(f"⚠️  Checklist evaluation failed: {e}")
                    # Continue with original results

            # Step 4.7: LLM Report Generation using Gemini (optional)
            if generate_llm_report:
                try:
                    if verbose:
                        click.echo("Generating LLM report using Gemini...")

                    from ..llm.report_generator import (
                        LLMProviderError,
                        ReportGenerator,
                        ReportGeneratorError,
                    )

                    # Find score_input.json file
                    score_input_file = None
                    for file_path in saved_files:
                        if file_path.endswith('score_input.json'):
                            score_input_file = file_path
                            break

                    if score_input_file:
                        # Initialize report generator
                        generator = ReportGenerator()

                        # Validate Gemini prerequisites
                        validation_result = generator.validate_prerequisites('gemini')
                        if not validation_result['valid']:
                            if verbose:
                                click.echo("⚠️  Gemini prerequisites not met:")
                                for issue in validation_result['issues']:
                                    click.echo(f"    • {issue}")
                                click.echo("⚠️  Install Gemini CLI and set GEMINI_API_KEY environment variable")
                                click.echo("⚠️  Skipping LLM report generation")
                            else:
                                click.echo("⚠️  LLM report generation skipped: Gemini CLI not configured")
                        else:
                            # Generate final report using Gemini
                            final_report_path = str(Path(output_dir) / "final_report.md")

                            result = generator.generate_report(
                                score_input_path=score_input_file,
                                output_path=final_report_path,
                                template_path=llm_template,
                                provider='gemini',
                                verbose=verbose,
                                timeout=timeout
                            )

                            if result.get('success'):
                                saved_files.append(final_report_path)
                                if verbose:
                                    metadata = result.get('report_metadata', {})
                                    click.echo(f"✅ Gemini report generated: {metadata.get('word_count', 0)} words")
                            else:
                                if verbose:
                                    click.echo("⚠️  Gemini report generation failed")

                    else:
                        if verbose:
                            click.echo("⚠️  No score_input.json found, skipping LLM report generation")

                except ReportGeneratorError as e:
                    if verbose:
                        click.echo(f"⚠️  LLM report generation failed: {e}")
                except LLMProviderError as e:
                    if verbose:
                        click.echo(f"⚠️  Gemini error: {e}")
                        click.echo("⚠️  Ensure Gemini CLI is installed and GEMINI_API_KEY is set")
                except Exception as e:
                    if verbose:
                        click.echo(f"⚠️  Unexpected error in LLM report generation: {e}")

            # Success message
            click.echo("Analysis completed successfully!")
            click.echo("Generated files:")
            for file_path in saved_files:
                click.echo(f"  - {file_path}")

            # Show summary
            click.echo("\nSummary:")
            click.echo(f"  Repository: {repository.url}")
            click.echo(f"  Language: {detected_language}")
            click.echo(f"  Duration: {metrics.execution_metadata.duration_seconds:.1f}s")

            if metrics.execution_metadata.errors:
                click.echo(f"  Errors: {len(metrics.execution_metadata.errors)}")
                if verbose:
                    for error in metrics.execution_metadata.errors:
                        click.echo(f"    - {error}")

            if metrics.execution_metadata.warnings:
                click.echo(f"  Warnings: {len(metrics.execution_metadata.warnings)}")
                if verbose:
                    for warning in metrics.execution_metadata.warnings:
                        click.echo(f"    - {warning}")

        finally:
            # Step 5: Cleanup
            if verbose:
                click.echo("Cleaning up temporary files...")

            try:
                git_ops.cleanup_repository(repository)
                cleanup_manager.cleanup_temporary_files()
            except Exception as e:
                error_handler.handle_error(e, "Cleanup")

            # Log summary
            error_handler.log_summary()

    except KeyboardInterrupt:
        click.echo("\nAnalysis interrupted by user", err=True)
        sys.exit(130)

    except Exception as e:
        click.echo(f"Error: Unexpected failure: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.group()
def cli() -> None:
    """Code Score - Git Repository Metrics Collection Tool."""
    pass


@cli.command()
@click.argument('repository_url')
@click.argument('commit_sha', required=False)
@click.option('--output-dir', default='./output')
@click.option('--format', 'output_format', default='both',
              type=click.Choice(['json', 'markdown', 'both']))
@click.option('--timeout', default=300)
@click.option('--verbose', is_flag=True)
@click.option('--enable-checklist', type=bool, default=True)
@click.option('--checklist-config', help='Path to checklist configuration YAML file')
@click.option('--generate-llm-report', is_flag=True, default=False, help='Generate human-readable LLM report using Gemini after analysis')
@click.option('--llm-template', help='Path to custom LLM prompt template')
def analyze(repository_url: str, commit_sha: str | None, output_dir: str,
           output_format: str, timeout: int, verbose: bool, enable_checklist: bool, checklist_config: str | None,
           generate_llm_report: bool, llm_template: str | None) -> None:
    """Analyze a Git repository for code quality metrics."""
    # This is the same as main() but accessible via 'code-score analyze'
    ctx = click.Context(main)
    ctx.invoke(main, repository_url=repository_url, commit_sha=commit_sha,
               output_dir=output_dir, output_format=output_format,
               timeout=timeout, verbose=verbose, enable_checklist=enable_checklist,
               checklist_config=checklist_config, generate_llm_report=generate_llm_report,
               llm_template=llm_template)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo("Code Score v0.1.0")


# Import and add the evaluate command
from .evaluate import evaluate

cli.add_command(evaluate)

# Import and add the llm-report command
from .llm_report import main as llm_report_main

cli.add_command(llm_report_main)


@cli.command()
@click.argument('repository_url')
def detect_language(repository_url: str) -> None:
    """Detect the primary language of a repository without full analysis."""
    try:
        git_ops = GitOperations()
        language_detector = LanguageDetector()

        # Clone repository
        repository = git_ops.clone_repository(repository_url)

        try:
            # Detect language
            stats = language_detector.get_language_statistics(repository.local_path)

            click.echo(f"Primary language: {stats['primary_language']}")
            click.echo(f"Confidence: {stats['confidence_score']:.2f}")
            click.echo(f"Files analyzed: {stats['total_files_analyzed']}")

            if stats['detected_languages']:
                click.echo("\nLanguage breakdown:")
                for lang, info in stats['detected_languages'].items():
                    click.echo(f"  {lang}: {info['file_count']} files ({info['percentage']:.1f}%)")

        finally:
            git_ops.cleanup_repository(repository)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    # Support both direct execution and 'python -m src.cli.main'
    if len(sys.argv) == 1:
        cli()
    else:
        main()
