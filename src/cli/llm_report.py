"""
Standalone CLI command for LLM report generation.

This module provides the `llm-report` command interface for generating
human-readable evaluation reports from score_input.json files.
"""

import sys
import click
import logging
from pathlib import Path
from typing import Optional

from ..llm.report_generator import ReportGenerator, ReportGeneratorError, LLMProviderError
from ..llm.template_loader import TemplateLoaderError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


@click.command(name='llm-report')
@click.argument('score_input_path', type=click.Path(exists=True, dir_okay=False))
@click.option('--prompt', '--template',
              type=click.Path(exists=True, dir_okay=False),
              help='Path to custom prompt template file (default: specs/prompts/llm_report.md)')
@click.option('--output', '-o',
              type=click.Path(dir_okay=False),
              default='output/final_report.md',
              help='Output path for generated report (default: output/final_report.md)')
@click.option('--provider',
              type=click.Choice(['gemini', 'openai', 'claude'], case_sensitive=False),
              default='gemini',
              help='LLM provider to use for generation (default: gemini)')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable detailed logging and progress information')
@click.option('--timeout',
              type=int,
              help='Override default timeout for LLM calls (seconds)')
@click.option('--validate-only',
              is_flag=True,
              help='Validate inputs and prerequisites without generating report')
def main(score_input_path: str,
         prompt: Optional[str],
         output: str,
         provider: str,
         verbose: bool,
         timeout: Optional[int],
         validate_only: bool):
    """
    Generate human-readable evaluation reports from code quality analysis data.

    Takes a score_input.json file from the checklist evaluation pipeline
    and generates a comprehensive, human-readable report using external LLM services.

    \b
    SCORE_INPUT_PATH: Path to score_input.json file from evaluation pipeline

    \b
    Examples:
      # Generate report with default settings
      uv run python -m src.cli.llm_report output/score_input.json

      # Use custom template and output location
      uv run python -m src.cli.llm_report output/score_input.json \\
        --prompt custom_template.md --output evaluation_report.md

      # Use different LLM provider
      uv run python -m src.cli.llm_report output/score_input.json \\
        --provider openai --timeout 60
    """
    try:
        # Validate argument combinations
        if validate_only and (timeout or prompt):
            logger.warning("⚠️  Additional options ignored in validate-only mode")

        if timeout and timeout < 10:
            logger.error("❌ Timeout must be at least 10 seconds")
            sys.exit(2)

        if timeout and timeout > 300:
            logger.warning("⚠️  Timeout over 5 minutes may cause issues")

        # Configure logging based on verbose flag
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")

        # Initialize report generator
        logger.info("🤖 Code Score LLM Report Generator")
        logger.info(f"📊 Processing: {score_input_path}")

        generator = ReportGenerator()

        # Handle validation-only mode
        if validate_only:
            return _handle_validation_only(generator, provider, prompt)

        # Validate prerequisites
        validation_result = generator.validate_prerequisites(provider)
        if not validation_result['valid']:
            logger.error("❌ Prerequisites validation failed:")
            for issue in validation_result['issues']:
                logger.error(f"   • {issue}")

            _print_setup_help(provider)
            sys.exit(2)

        logger.info("✅ Prerequisites validated")

        # Generate report
        logger.info(f"🚀 Generating report using {provider}")

        result = generator.generate_report(
            score_input_path=score_input_path,
            output_path=output,
            template_path=prompt,
            provider=provider,
            verbose=verbose,
            timeout=timeout
        )

        # Handle results
        _handle_generation_output(result, verbose)

        sys.exit(0)

    except ReportGeneratorError as e:
        logger.error(f"❌ Report generation failed: {e}")
        logger.info("💡 Try using --validate-only to check prerequisites")
        sys.exit(3)
    except LLMProviderError as e:
        logger.error(f"❌ LLM provider error: {e}")
        logger.info("💡 Check your LLM provider configuration and credentials")
        _print_provider_help(provider)
        sys.exit(4)
    except TemplateLoaderError as e:
        logger.error(f"❌ Template error: {e}")
        logger.info("💡 Check template syntax or use default template")
        if prompt:
            logger.info(f"💡 Problematic template: {prompt}")
        sys.exit(5)
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.info("💡 Ensure score_input.json exists from prior analysis")
        logger.info("💡 Run: uv run python -m src.cli.main <repo_url> --enable-checklist")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"❌ Permission denied: {e}")
        logger.info("💡 Check file permissions and output directory access")
        sys.exit(6)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.info("💡 Use --verbose for detailed error information")
        logger.info("💡 Use --validate-only to check system configuration")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(99)


def _handle_validation_only(generator: ReportGenerator,
                           provider: str,
                           template_path: Optional[str]) -> None:
    """Handle validation-only mode."""
    logger.info("🔍 Validating prerequisites and configuration...")

    # Validate provider
    validation_result = generator.validate_prerequisites(provider)

    logger.info(f"\n📋 Validation Results:")
    logger.info(f"   Provider ({provider}): {'✅' if validation_result['provider_available'] else '❌'}")
    logger.info(f"   Environment: {'✅' if validation_result['environment_valid'] else '❌'}")
    logger.info(f"   Template: {'✅' if validation_result['template_available'] else '❌'}")

    if validation_result['issues']:
        logger.info(f"\n⚠️  Issues found:")
        for issue in validation_result['issues']:
            logger.info(f"   • {issue}")

    # Validate template if provided
    if template_path:
        template_info = generator.get_template_info(template_path)
        logger.info(f"\n📄 Template: {'✅' if template_info['valid'] else '❌'}")
        if template_info['valid']:
            logger.info(f"   Name: {template_info['name']}")
            logger.info(f"   Type: {template_info['type']}")
            logger.info(f"   Fields: {len(template_info['required_fields'])}")

    # Show available providers
    providers = generator.get_available_providers()
    logger.info(f"\n🔌 Available Providers:")
    for p in providers:
        status = "✅" if p['available'] and p['environment_ready'] else "❌"
        logger.info(f"   {status} {p['name']} ({p['model']})")

    # Exit with appropriate code
    if validation_result['valid']:
        logger.info(f"\n✅ All validations passed - ready for report generation")
        sys.exit(0)
    else:
        logger.info(f"\n❌ Validation failed - please resolve issues above")
        sys.exit(2)



def _handle_generation_output(result: dict, verbose: bool) -> None:
    """Handle successful generation output."""
    logger.info("✅ Report generated successfully")

    metadata = result['report_metadata']
    logger.info(f"📄 Report Details:")
    logger.info(f"   • Output: {result['output_path']}")
    logger.info(f"   • Word count: {metadata['word_count']:,}")
    logger.info(f"   • Generation time: {result['generation_time_seconds']:.1f}s")
    logger.info(f"   • Status: {metadata['validation_status']}")

    if metadata['warnings']:
        logger.info(f"⚠️  Warnings ({len(metadata['warnings'])}):")
        for warning in metadata['warnings']:
            logger.info(f"   • {warning}")

    if verbose:
        provider_info = result['provider_metadata']
        template_info = result['template_metadata']

        logger.info(f"\n🔧 Provider Details:")
        logger.info(f"   • Provider: {provider_info['provider_name']}")
        logger.info(f"   • Model: {provider_info['model_name']}")
        logger.info(f"   • Response time: {provider_info['response_time_seconds']:.1f}s")

        logger.info(f"\n📋 Template Details:")
        logger.info(f"   • Template: {template_info['template_name']}")
        logger.info(f"   • Type: {template_info['template_type']}")
        logger.info(f"   • Path: {template_info['file_path']}")


def _print_setup_help(provider: str) -> None:
    """Print setup help for the specified provider."""
    help_text = {
        'gemini': """
💡 Gemini Setup Help:
   1. Install Gemini CLI: https://ai.google.dev/gemini-api/docs/quickstart
   2. Set environment variable: export GEMINI_API_KEY=your_api_key
   3. Verify installation: gemini --version
        """,
        'openai': """
💡 OpenAI Setup Help:
   1. Install OpenAI CLI: pip install openai
   2. Set environment variable: export OPENAI_API_KEY=your_api_key
   3. Verify installation: openai --version
        """,
        'claude': """
💡 Claude Setup Help:
   1. Install Claude CLI: pip install anthropic
   2. Set environment variable: export ANTHROPIC_API_KEY=your_api_key
   3. Verify installation: claude --version
        """
    }

    logger.info(help_text.get(provider, "No setup help available for this provider"))


def _print_provider_help(provider: str) -> None:
    """Print provider-specific troubleshooting help."""
    logger.info(f"\n🔧 Troubleshooting {provider}:")
    logger.info("   • Check API key is set correctly")
    logger.info("   • Verify CLI tool is installed and in PATH")
    logger.info("   • Check network connectivity")
    logger.info("   • Try increasing timeout with --timeout option")
    logger.info("   • Use --validate-only to check configuration")


if __name__ == '__main__':
    main()