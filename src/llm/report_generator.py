"""
Core LLM report generation orchestrator.

This module provides the main ReportGenerator class that orchestrates
template loading, prompt building, LLM calls, and report generation.
"""

import json
import subprocess
import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .models.report_template import ReportTemplate
from .models.llm_provider_config import LLMProviderConfig
from .models.generated_report import GeneratedReport, TemplateMetadata, ProviderMetadata, InputMetadata, TruncationInfo
from .models.template_context import TemplateContext
from .template_loader import TemplateLoader, TemplateLoaderError
from .prompt_builder import PromptBuilder, PromptBuilderError

logger = logging.getLogger(__name__)


class ReportGeneratorError(Exception):
    """Base exception for report generation errors."""
    pass


class LLMProviderError(ReportGeneratorError):
    """Exception raised when Gemini fails."""
    pass


class ReportGenerator:
    """
    Core class that orchestrates template loading, prompt building, and LLM calls.

    This class provides the main interface for generating human-readable reports
    from code evaluation data using external LLM services.
    """

    def __init__(self, template_loader: Optional[TemplateLoader] = None,
                 prompt_builder: Optional[PromptBuilder] = None):
        """
        Initialize ReportGenerator.

        Args:
            template_loader: TemplateLoader instance (creates new if None)
            prompt_builder: PromptBuilder instance (creates new if None)
        """
        self.template_loader = template_loader or TemplateLoader()
        self.prompt_builder = prompt_builder or PromptBuilder(self.template_loader)
        self._default_providers = LLMProviderConfig.get_default_configs()

    def generate_report(self, score_input_path: str,
                       output_path: Optional[str] = None,
                       template_path: Optional[str] = None,
                       provider: str = "gemini",
                       verbose: bool = False,
                       timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate complete LLM report from evaluation data.

        This method orchestrates the complete pipeline for generating human-readable
        reports from structured code evaluation data. It loads evaluation results,
        applies template rendering, calls external LLM services, and saves the final
        report with comprehensive metadata tracking.

        Args:
            score_input_path: Path to score_input.json file containing evaluation results
            output_path: Output path for generated report (default: None for in-memory only)
            template_path: Path to Jinja2 template file (uses default if None)
            provider: LLM provider name ("gemini" only)
            verbose: Enable detailed logging and progress tracking
            timeout: Override default timeout for LLM API calls (10-300 seconds)

        Returns:
            Dictionary with generation results and metadata:
            {
                "success": bool,
                "output_path": str,
                "generation_time_seconds": float,
                "report_metadata": {"word_count": int, "validation_status": str},
                "provider_metadata": {"provider_name": str, "response_time_seconds": float},
                "template_metadata": {"template_name": str, "required_fields_used": List[str]}
            }

        Raises:
            ReportGeneratorError: If any step in the generation pipeline fails
            LLMProviderError: If external LLM service is unavailable or returns errors
            FileNotFoundError: If score_input_path or template_path don't exist
            ValueError: If timeout is out of range or Gemini configuration is invalid

        Examples:
            >>> generator = ReportGenerator()
            >>> result = generator.generate_report(
            ...     score_input_path="output/score_input.json",
            ...     output_path="reports/final_report.md",
            ...     provider="gemini",
            ...     verbose=True
            ... )
            >>> print(f"Generated report in {result['generation_time_seconds']:.2f}s")
            >>> print(f"Word count: {result['report_metadata']['word_count']}")
        """
        start_time = time.time()

        try:
            # Configure logging
            if verbose:
                logging.getLogger(__name__).setLevel(logging.DEBUG)

            logger.info("Starting report generation")

            # Load and validate input data
            score_input_data = self._load_score_input(score_input_path)
            logger.debug(f"Loaded score input: {len(json.dumps(score_input_data))} chars")

            # Load template
            template_config = self._load_template(template_path)
            logger.debug(f"Loaded template: {template_config.name}")

            # Get provider configuration
            provider_config = self._get_provider_config(provider, timeout)
            logger.debug(f"Using provider: {provider_config.provider_name}")

            # Build prompt
            prompt = self.prompt_builder.build_prompt(score_input_data, template_config)
            logger.info(f"Built prompt: {len(prompt)} characters")

            # Generate report via LLM
            generation_start = time.time()
            llm_response = self._call_llm(prompt, provider_config)
            generation_time = time.time() - generation_start

            # Create generated report
            generated_report = self._create_generated_report(
                llm_response,
                score_input_data,
                template_config,
                provider_config,
                generation_time
            )

            # Save report if output path specified
            if output_path:
                self._save_report(generated_report, output_path)
                logger.info(f"Report saved to: {output_path}")

            total_time = time.time() - start_time
            logger.info(f"Report generation completed in {total_time:.2f}s")

            return {
                'success': True,
                'output_path': output_path,
                'generation_time_seconds': total_time,
                'report_metadata': {
                    'word_count': generated_report.word_count,
                    'validation_status': generated_report.validation_status,
                    'warnings': generated_report.generation_warnings
                },
                'provider_metadata': generated_report.provider_used.dict(),
                'template_metadata': generated_report.template_used.dict()
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ReportGeneratorError(f"Report generation failed: {e}")

    def _load_score_input(self, score_input_path: str) -> Dict[str, Any]:
        """Load and validate score input data."""
        try:
            with open(score_input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate data structure
            validation_issues = self.prompt_builder.validate_context_data(data)
            if validation_issues:
                raise ReportGeneratorError(f"Invalid score input data: {', '.join(validation_issues)}")

            return data

        except FileNotFoundError:
            raise ReportGeneratorError(f"Score input file not found: {score_input_path}")
        except json.JSONDecodeError as e:
            raise ReportGeneratorError(f"Invalid JSON in score input: {e}")

    def _load_template(self, template_path: Optional[str]) -> ReportTemplate:
        """Load template configuration."""
        try:
            if template_path:
                return self.template_loader.load_template(template_path)
            else:
                return self.template_loader.load_default_template()

        except TemplateLoaderError as e:
            raise ReportGeneratorError(f"Template loading failed: {e}")

    def _get_provider_config(self, provider: str, timeout: Optional[int]) -> LLMProviderConfig:
        """Get provider configuration with optional timeout override."""
        if provider not in self._default_providers:
            raise ReportGeneratorError(f"Unknown provider: {provider}")

        config = self._default_providers[provider]

        # Override timeout if specified
        if timeout is not None:
            config.timeout_seconds = timeout

        # Validate environment
        missing_vars = config.validate_environment()
        if missing_vars:
            raise LLMProviderError(f"Missing environment variables for {provider}: {', '.join(missing_vars)}")

        return config

    def _call_llm(self, prompt: str, provider_config: LLMProviderConfig) -> str:
        """Call external LLM service via subprocess with enhanced error recovery."""
        import signal
        import threading
        import time

        try:
            # Build CLI command
            cmd = provider_config.build_cli_command(prompt)
            logger.debug(f"Executing LLM command: {cmd[0]} [args hidden for security]")

            # Progress indicator for long-running calls
            progress_thread = None
            if provider_config.timeout_seconds > 30:
                stop_progress = threading.Event()
                progress_thread = threading.Thread(
                    target=self._show_progress_indicator,
                    args=(stop_progress, provider_config.timeout_seconds)
                )
                progress_thread.daemon = True
                progress_thread.start()

            try:
                # Execute subprocess with timeout
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=provider_config.timeout_seconds,
                    check=True
                )

                # Stop progress indicator
                if progress_thread:
                    stop_progress.set()
                    progress_thread.join(timeout=1)

                response = result.stdout.strip()
                if not response:
                    raise LLMProviderError("Empty response from Gemini")

                logger.debug(f"LLM response: {len(response)} characters")
                return response

            except subprocess.TimeoutExpired as e:
                # Stop progress indicator
                if progress_thread:
                    stop_progress.set()
                    progress_thread.join(timeout=1)

                # Attempt graceful termination first
                if e.args and len(e.args) > 0:
                    process = e.args[0] if hasattr(e.args[0], 'terminate') else None
                    if process:
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                        except:
                            try:
                                process.kill()
                            except:
                                pass

                timeout_msg = f"LLM call timed out after {provider_config.timeout_seconds}s"
                if provider_config.timeout_seconds < 60:
                    timeout_msg += " (consider increasing timeout for complex prompts)"

                raise LLMProviderError(timeout_msg)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"

            # Enhanced error context based on return code
            if e.returncode == 1:
                error_msg += " (likely authentication or API issue)"
            elif e.returncode == 2:
                error_msg += " (likely invalid arguments or configuration)"
            elif e.returncode in [124, 128, 130]:
                error_msg += " (process interrupted or killed)"

            raise LLMProviderError(f"LLM provider failed (exit {e.returncode}): {error_msg}")

        except FileNotFoundError:
            raise LLMProviderError(
                f"LLM provider CLI not found: {provider_config.cli_command[0]}. "
                f"Ensure {provider_config.provider_name} CLI is installed and in PATH."
            )

        except Exception as e:
            raise LLMProviderError(f"Unexpected error calling LLM: {e}")

    def _show_progress_indicator(self, stop_event: threading.Event, timeout_seconds: int):
        """Show progress indicator for long-running LLM calls."""
        import sys

        start_time = time.time()
        chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0

        while not stop_event.wait(0.1):
            elapsed = time.time() - start_time
            remaining = max(0, timeout_seconds - elapsed)

            if remaining <= 0:
                break

            progress = f"\r{chars[i % len(chars)]} Generating report... ({remaining:.0f}s remaining)"
            sys.stderr.write(progress)
            sys.stderr.flush()
            i += 1

        # Clear progress indicator
        sys.stderr.write('\r' + ' ' * 50 + '\r')
        sys.stderr.flush()

    def _create_generated_report(self, llm_response: str,
                               score_input_data: Dict[str, Any],
                               template_config: ReportTemplate,
                               provider_config: LLMProviderConfig,
                               generation_time: float) -> GeneratedReport:
        """Create GeneratedReport from LLM response and metadata."""
        # Extract input metadata
        repo_info = score_input_data['repository_info']
        eval_result = score_input_data['evaluation_result']

        input_metadata = InputMetadata(
            repository_url=repo_info['url'],
            commit_sha=repo_info['commit_sha'],
            primary_language=repo_info['primary_language'],
            total_score=eval_result['total_score'],
            max_possible_score=eval_result['max_possible_score'],
            checklist_items_count=len(eval_result['checklist_items']),
            evidence_items_count=sum(len(cat.get('items', [])) for cat in eval_result.get('evidence_summary', []))
        )

        # Create template metadata
        template_metadata = TemplateMetadata(
            file_path=template_config.file_path,
            template_name=template_config.name,
            template_type=template_config.template_type,
            required_fields_used=template_config.required_fields
        )

        # Create provider metadata
        provider_metadata = ProviderMetadata(
            provider_name=provider_config.provider_name,
            model_name=provider_config.model_name,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
            response_time_seconds=generation_time
        )

        # Create generated report
        report = GeneratedReport(
            content=llm_response,
            template_used=template_metadata,
            provider_used=provider_metadata,
            input_metadata=input_metadata
        )

        # Calculate derived fields
        report.calculate_derived_fields()

        # Validate content
        validation_issues = report.validate_markdown_structure()
        if validation_issues:
            report.validation_status = "warnings"
            for issue in validation_issues:
                report.add_warning(f"Markdown validation: {issue}")

        return report

    def _save_report(self, report: GeneratedReport, output_path: str) -> None:
        """Save generated report to file."""
        try:
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write report with metadata
            content = report.to_file_content()
            output_file.write_text(content, encoding='utf-8')

            logger.debug(f"Report saved: {len(content)} characters to {output_path}")

        except Exception as e:
            raise ReportGeneratorError(f"Failed to save report: {e}")


    def validate_prerequisites(self, provider: str) -> Dict[str, Any]:
        """
        Validate that all prerequisites are met for report generation.

        Args:
            provider: LLM provider name

        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'provider_available': False,
            'environment_valid': False,
            'template_available': False,
            'issues': []
        }

        try:
            # Check provider configuration
            if provider in self._default_providers:
                provider_config = self._default_providers[provider]
                results['provider_available'] = True

                # Check environment variables
                missing_vars = provider_config.validate_environment()
                if not missing_vars:
                    results['environment_valid'] = True
                else:
                    results['issues'].append(f"Missing environment variables: {', '.join(missing_vars)}")

                # Check CLI command availability
                try:
                    subprocess.run([provider_config.cli_command[0], '--version'],
                                 capture_output=True, timeout=5, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    results['issues'].append(f"Provider CLI not available: {provider_config.cli_command[0]}")

            else:
                results['issues'].append(f"Unknown provider: {provider}")

            # Check default template
            try:
                self.template_loader.load_default_template()
                results['template_available'] = True
            except Exception as e:
                results['issues'].append(f"Default template not available: {e}")

            # Overall validation
            results['valid'] = (results['provider_available'] and
                              results['environment_valid'] and
                              results['template_available'] and
                              not results['issues'])

        except Exception as e:
            results['issues'].append(f"Validation error: {e}")
            results['valid'] = False

        return results

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of available providers with status (Gemini only).

        Returns:
            List of provider information dictionaries
        """
        providers = []

        for name, config in self._default_providers.items():
            provider_info = {
                'name': name,
                'model': config.model_name,
                'timeout': config.timeout_seconds,
                'available': False,
                'environment_ready': False
            }

            # Check environment
            missing_vars = config.validate_environment()
            provider_info['environment_ready'] = len(missing_vars) == 0
            provider_info['missing_variables'] = missing_vars

            # Check CLI availability
            try:
                subprocess.run([config.cli_command[0], '--version'],
                             capture_output=True, timeout=5, check=True)
                provider_info['available'] = True
            except:
                provider_info['available'] = False

            providers.append(provider_info)

        return providers

    def get_template_info(self, template_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about template configuration.

        Args:
            template_path: Path to template file (uses default if None)

        Returns:
            Dictionary with template information
        """
        try:
            template_config = self._load_template(template_path)

            return {
                'name': template_config.name,
                'path': template_config.file_path,
                'type': template_config.template_type,
                'required_fields': template_config.required_fields,
                'content_limits': template_config.content_limits,
                'target_providers': template_config.target_providers,
                'valid': True
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }