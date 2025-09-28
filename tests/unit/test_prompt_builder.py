"""
Unit tests for PromptBuilder class.

This module tests all functionality of the PromptBuilder class including
prompt building, context management, content truncation, and provider optimization.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from jinja2 import Template, TemplateSyntaxError

# Import the modules to test
from src.llm.prompt_builder import (
    PromptBuilder,
    PromptBuilderError,
    ContextLimitExceededError
)
from src.llm.models.template_context import TemplateContext
from src.llm.models.report_template import ReportTemplate
from src.llm.template_loader import TemplateLoader


class TestPromptBuilder:
    """Unit tests for PromptBuilder class."""

    @pytest.fixture
    def mock_template_loader(self):
        """Create mock TemplateLoader for testing."""
        loader = Mock(spec=TemplateLoader)
        return loader

    @pytest.fixture
    def prompt_builder(self, mock_template_loader):
        """Create PromptBuilder instance for testing."""
        return PromptBuilder(template_loader=mock_template_loader)

    @pytest.fixture
    def prompt_builder_default(self):
        """Create PromptBuilder with default TemplateLoader."""
        return PromptBuilder()

    @pytest.fixture
    def sample_score_input(self):
        """Sample score_input.json data for testing."""
        return {
            "schema_version": "1.0.0",
            "repository_info": {
                "url": "https://github.com/test/repository.git",
                "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                "primary_language": "python",
                "analysis_timestamp": "2025-09-27T10:30:00Z"
            },
            "evaluation_result": {
                "checklist_items": [
                    {
                        "id": "code_quality_lint",
                        "name": "Static Linting Passed",
                        "dimension": "code_quality",
                        "max_points": 15,
                        "evaluation_status": "met",
                        "score": 15.0,
                        "actual_points": 15.0,
                        "evidence_references": [
                            {
                                "source": "ruff_output.txt",
                                "description": "No linting errors found",
                                "confidence": 1.0
                            }
                        ]
                    },
                    {
                        "id": "testing_automation",
                        "name": "Automated Tests Present",
                        "dimension": "testing",
                        "max_points": 15,
                        "evaluation_status": "partial",
                        "score": 7.5,
                        "actual_points": 7.5,
                        "evidence_references": [
                            {
                                "source": "pytest_output.txt",
                                "description": "Some tests found but coverage low",
                                "confidence": 0.8
                            }
                        ]
                    },
                    {
                        "id": "documentation_readme",
                        "name": "README Documentation",
                        "dimension": "documentation",
                        "max_points": 10,
                        "evaluation_status": "unmet",
                        "score": 0.0,
                        "actual_points": 0.0,
                        "evidence_references": [
                            {
                                "source": "file_analysis.txt",
                                "description": "README.md missing or inadequate",
                                "confidence": 0.9
                            }
                        ]
                    }
                ],
                "total_score": 22.5,
                "max_possible_score": 100,
                "score_percentage": 22.5,
                "category_breakdowns": {
                    "code_quality": {"score": 15.0, "actual_points": 15.0, "max_points": 40, "percentage": 37.5},
                    "testing": {"score": 7.5, "actual_points": 7.5, "max_points": 35, "percentage": 21.4},
                    "documentation": {"score": 0.0, "actual_points": 0.0, "max_points": 25, "percentage": 0.0}
                },
                "evidence_summary": [
                    {
                        "category": "code_quality",
                        "items": [
                            {
                                "source": "ruff_output.txt",
                                "description": "No linting errors found",
                                "confidence": 1.0
                            }
                        ]
                    }
                ]
            },
            "human_summary": "Basic evaluation summary"
        }

    @pytest.fixture
    def sample_template_config(self):
        """Sample ReportTemplate configuration."""
        return ReportTemplate(
            name="test_template",
            file_path="/path/to/template.md",
            description="Test template",
            required_fields=["repository", "total", "met_items"],
            content_limits={"max_evidence_items": 2}
        )

    @pytest.fixture
    def mock_compiled_template(self):
        """Mock compiled Jinja2 template."""
        template = Mock(spec=Template)
        template.render.return_value = "# Test Report\n\nRepository: {{repository.url}}\nScore: {{total.score}}"
        return template

    @pytest.fixture
    def sample_template_context(self, sample_score_input):
        """Sample TemplateContext for testing."""
        return TemplateContext.from_score_input(sample_score_input)

    def test_init_with_template_loader(self, mock_template_loader):
        """Test PromptBuilder initialization with provided TemplateLoader."""
        builder = PromptBuilder(template_loader=mock_template_loader)

        assert builder.template_loader is mock_template_loader
        assert 'max_evidence_items' in builder._context_limits
        assert 'max_prompt_length' in builder._context_limits

    def test_init_default_template_loader(self):
        """Test PromptBuilder initialization with default TemplateLoader."""
        builder = PromptBuilder()

        assert isinstance(builder.template_loader, TemplateLoader)
        assert builder._context_limits['max_evidence_items'] == 3
        assert builder._context_limits['max_prompt_length'] == 32000

    def test_build_prompt_success(self, prompt_builder, sample_score_input,
                                sample_template_config, mock_compiled_template):
        """Test successful prompt building."""
        # Setup mocks
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = "# Test Report\nRepository: https://github.com/test/repository.git\nScore: 22.5"

        # Build prompt
        prompt = prompt_builder.build_prompt(sample_score_input, sample_template_config)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Test Report" in prompt
        prompt_builder.template_loader.compile_template.assert_called_once_with(sample_template_config)

    def test_build_prompt_with_custom_limits(self, prompt_builder, sample_score_input,
                                           sample_template_config, mock_compiled_template):
        """Test prompt building with custom limits."""
        # Setup mocks
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = "Short prompt"

        custom_limits = {'max_evidence_items': 1, 'max_description_length': 50}

        prompt = prompt_builder.build_prompt(sample_score_input, sample_template_config, custom_limits)

        assert isinstance(prompt, str)
        assert "Short prompt" in prompt

    def test_build_prompt_with_template_limits(self, prompt_builder, sample_score_input,
                                             mock_compiled_template):
        """Test prompt building with template content limits."""
        # Create template with content limits
        template_config = ReportTemplate(
            name="limited_template",
            file_path="/path/to/template.md",
            description="Template with limits",
            content_limits={"max_evidence_items": 1, "max_description_length": 100}
        )

        # Setup mocks
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = "Limited prompt"

        prompt = prompt_builder.build_prompt(sample_score_input, template_config)

        assert isinstance(prompt, str)
        assert "Limited prompt" in prompt

    def test_build_prompt_long_output_truncation(self, prompt_builder, sample_score_input,
                                               sample_template_config, mock_compiled_template):
        """Test prompt building with output that exceeds length limits."""
        # Create very long output
        long_output = "x" * 40000  # Exceeds default 32000 limit

        # Setup mocks
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = long_output

        prompt = prompt_builder.build_prompt(sample_score_input, sample_template_config)

        assert len(prompt) < len(long_output)
        assert "[Content truncated due to length limits]" in prompt

    def test_build_prompt_template_context_error(self, prompt_builder, sample_template_config):
        """Test prompt building with invalid score input data."""
        invalid_data = {"invalid": "data"}

        with pytest.raises(PromptBuilderError) as exc_info:
            prompt_builder.build_prompt(invalid_data, sample_template_config)

        assert "Failed to build prompt" in str(exc_info.value)

    def test_build_prompt_template_compilation_error(self, prompt_builder, sample_score_input,
                                                   sample_template_config):
        """Test prompt building with template compilation error."""
        # Setup mock to raise exception
        prompt_builder.template_loader.compile_template.side_effect = Exception("Compilation failed")

        with pytest.raises(PromptBuilderError) as exc_info:
            prompt_builder.build_prompt(sample_score_input, sample_template_config)

        assert "Failed to build prompt" in str(exc_info.value)
        assert "Compilation failed" in str(exc_info.value)

    def test_render_prompt_success(self, prompt_builder, sample_template_context, mock_compiled_template):
        """Test successful template rendering."""
        mock_compiled_template.render.return_value = "# Rendered Content\nTest output"

        result = prompt_builder._render_prompt(mock_compiled_template, sample_template_context)

        assert isinstance(result, str)
        assert "Rendered Content" in result
        # Check that render was called with proper data
        mock_compiled_template.render.assert_called_once()
        call_args = mock_compiled_template.render.call_args[1]
        assert 'generation_time' in call_args
        assert 'has_warnings' in call_args

    def test_render_prompt_template_error(self, prompt_builder, sample_template_context, mock_compiled_template):
        """Test template rendering with error."""
        mock_compiled_template.render.side_effect = Exception("Rendering failed")

        with pytest.raises(PromptBuilderError) as exc_info:
            prompt_builder._render_prompt(mock_compiled_template, sample_template_context)

        assert "Template rendering failed" in str(exc_info.value)

    def test_clean_prompt_text_basic(self, prompt_builder):
        """Test basic prompt text cleaning."""
        messy_text = "Line 1\n\n\n\nLine 2\n\n\nLine 3\n\n\n\n\n"

        cleaned = prompt_builder._clean_prompt_text(messy_text)

        # Should remove excessive blank lines
        assert "\n\n\n\n" not in cleaned
        assert "Line 1" in cleaned
        assert "Line 2" in cleaned
        assert "Line 3" in cleaned

    def test_clean_prompt_text_preserve_double_newlines(self, prompt_builder):
        """Test that double newlines are preserved."""
        text = "Section 1\n\nSection 2\n\nSection 3"

        cleaned = prompt_builder._clean_prompt_text(text)

        assert cleaned == text  # Should be unchanged

    def test_clean_prompt_text_strip_ends(self, prompt_builder):
        """Test that leading/trailing whitespace is stripped."""
        text = "\n\n  Content with spaces  \n\n"

        cleaned = prompt_builder._clean_prompt_text(text)

        assert cleaned == "Content with spaces"

    def test_truncate_prompt_no_truncation_needed(self, prompt_builder):
        """Test prompt truncation when no truncation is needed."""
        short_prompt = "This is a short prompt"

        result = prompt_builder._truncate_prompt(short_prompt, 1000)

        assert result == short_prompt

    def test_truncate_prompt_basic_truncation(self, prompt_builder):
        """Test basic prompt truncation."""
        long_prompt = "x" * 1000

        result = prompt_builder._truncate_prompt(long_prompt, 500)

        assert len(result) < len(long_prompt)
        assert "[Content truncated due to length limits]" in result

    def test_truncate_prompt_find_newline(self, prompt_builder):
        """Test truncation that finds appropriate newline."""
        prompt = "Line 1\nLine 2\nLine 3\n" + ("x" * 1000)

        result = prompt_builder._truncate_prompt(prompt, 500)

        assert len(result) < len(prompt)
        assert "Line 1" in result
        assert "[Content truncated due to length limits]" in result

    def test_validate_context_data_valid(self, prompt_builder, sample_score_input):
        """Test validation of valid context data."""
        issues = prompt_builder.validate_context_data(sample_score_input)

        assert issues == []

    def test_validate_context_data_missing_top_level(self, prompt_builder):
        """Test validation with missing top-level fields."""
        invalid_data = {"incomplete": "data"}

        issues = prompt_builder.validate_context_data(invalid_data)

        assert len(issues) > 0
        assert any("Missing required field: repository_info" in issue for issue in issues)
        assert any("Missing required field: evaluation_result" in issue for issue in issues)

    def test_validate_context_data_missing_repository_fields(self, prompt_builder):
        """Test validation with missing repository info fields."""
        data = {
            "repository_info": {"url": "https://github.com/test/repo"},
            "evaluation_result": {"checklist_items": [], "total_score": 0, "category_breakdowns": {}}
        }

        issues = prompt_builder.validate_context_data(data)

        assert any("Missing repository_info.commit_sha" in issue for issue in issues)
        assert any("Missing repository_info.primary_language" in issue for issue in issues)

    def test_validate_context_data_missing_evaluation_fields(self, prompt_builder):
        """Test validation with missing evaluation result fields."""
        data = {
            "repository_info": {
                "url": "https://github.com/test/repo",
                "commit_sha": "abc123",
                "primary_language": "python"
            },
            "evaluation_result": {"checklist_items": []}
        }

        issues = prompt_builder.validate_context_data(data)

        assert any("Missing evaluation_result.total_score" in issue for issue in issues)
        assert any("Missing evaluation_result.category_breakdowns" in issue for issue in issues)

    def test_validate_context_data_invalid_checklist_items(self, prompt_builder):
        """Test validation with invalid checklist items."""
        data = {
            "repository_info": {
                "url": "https://github.com/test/repo",
                "commit_sha": "abc123",
                "primary_language": "python"
            },
            "evaluation_result": {
                "checklist_items": [{"id": "test"}],  # Missing required fields
                "total_score": 0,
                "category_breakdowns": {}
            }
        }

        issues = prompt_builder.validate_context_data(data)

        assert any("Missing checklist_items[0].name" in issue for issue in issues)
        assert any("Missing checklist_items[0].evaluation_status" in issue for issue in issues)
        assert any("Missing checklist_items[0].score" in issue for issue in issues)

    def test_validate_context_data_exception_handling(self, prompt_builder):
        """Test validation with data that causes exceptions."""
        # Non-dict data that will cause attribute errors
        invalid_data = "not a dictionary"

        issues = prompt_builder.validate_context_data(invalid_data)

        assert len(issues) > 0
        assert any("Validation error:" in issue for issue in issues)

    def test_estimate_token_usage(self, prompt_builder):
        """Test token usage estimation."""
        prompt = "This is a test prompt with some content."

        estimates = prompt_builder.estimate_token_usage(prompt)

        assert 'character_count' in estimates
        assert 'estimated_tokens' in estimates
        assert 'estimated_tokens_conservative' in estimates
        assert 'estimated_cost_gpt4' in estimates
        assert 'estimated_cost_gemini' in estimates

        assert estimates['character_count'] == len(prompt)
        assert estimates['estimated_tokens'] == len(prompt) // 4
        assert estimates['estimated_tokens_conservative'] == len(prompt) // 3

    def test_optimize_context_for_provider_gemini(self, prompt_builder, sample_template_context):
        """Test context optimization for Gemini provider."""
        optimized = prompt_builder.optimize_context_for_provider(sample_template_context, "gemini")

        assert optimized.generation_metadata['optimized_for'] == "gemini"
        assert 'optimization_applied' in optimized.generation_metadata

    def test_optimize_context_for_provider_openai(self, prompt_builder, sample_template_context):
        """Test context optimization for OpenAI provider."""
        optimized = prompt_builder.optimize_context_for_provider(sample_template_context, "openai")

        assert optimized.generation_metadata['optimized_for'] == "openai"

    def test_optimize_context_for_provider_claude(self, prompt_builder, sample_template_context):
        """Test context optimization for Claude provider."""
        optimized = prompt_builder.optimize_context_for_provider(sample_template_context, "claude")

        assert optimized.generation_metadata['optimized_for'] == "claude"

    def test_optimize_context_for_provider_unknown(self, prompt_builder, sample_template_context):
        """Test context optimization for unknown provider."""
        optimized = prompt_builder.optimize_context_for_provider(sample_template_context, "unknown_provider")

        assert optimized.generation_metadata['optimized_for'] == "unknown_provider"
        # Should use default limits

    def test_get_context_statistics(self, prompt_builder, sample_template_context):
        """Test getting context statistics."""
        stats = prompt_builder.get_context_statistics(sample_template_context)

        assert 'items' in stats
        assert 'evidence' in stats
        assert 'repository' in stats
        assert 'scores' in stats
        assert 'warnings' in stats
        assert 'metadata_keys' in stats

        # Check items stats
        assert 'total' in stats['items']
        assert 'met' in stats['items']
        assert 'partial' in stats['items']
        assert 'unmet' in stats['items']

        # Check evidence stats
        assert 'categories' in stats['evidence']
        assert 'total_items' in stats['evidence']

        # Check repository stats
        assert 'url' in stats['repository']
        assert 'language' in stats['repository']

        # Check scores stats
        assert 'total' in stats['scores']
        assert 'percentage' in stats['scores']
        assert 'grade' in stats['scores']

    def test_set_context_limits(self, prompt_builder):
        """Test setting context limits."""
        new_limits = {'max_evidence_items': 5, 'max_description_length': 300}

        prompt_builder.set_context_limits(new_limits)

        assert prompt_builder._context_limits['max_evidence_items'] == 5
        assert prompt_builder._context_limits['max_description_length'] == 300
        # Should preserve other limits
        assert 'max_prompt_length' in prompt_builder._context_limits

    def test_get_context_limits(self, prompt_builder):
        """Test getting context limits."""
        limits = prompt_builder.get_context_limits()

        assert isinstance(limits, dict)
        assert 'max_evidence_items' in limits
        assert 'max_prompt_length' in limits
        assert limits['max_evidence_items'] == 3  # Default value

        # Should return a copy
        limits['test'] = 'value'
        assert 'test' not in prompt_builder._context_limits

    def test_exception_hierarchy(self):
        """Test exception hierarchy is correct."""
        assert issubclass(ContextLimitExceededError, PromptBuilderError)
        assert issubclass(PromptBuilderError, Exception)

    @patch('src.llm.prompt_builder.datetime')
    def test_render_prompt_generation_time(self, mock_datetime, prompt_builder,
                                         sample_template_context, mock_compiled_template):
        """Test that generation time is properly added to template data."""
        mock_datetime.utcnow.return_value.isoformat.return_value = "2025-09-27T10:30:00"
        mock_compiled_template.render.return_value = "Rendered content"

        prompt_builder._render_prompt(mock_compiled_template, sample_template_context)

        # Check that generation_time was passed to template
        call_kwargs = mock_compiled_template.render.call_args[1]
        assert call_kwargs['generation_time'] == "2025-09-27T10:30:00"

    def test_build_prompt_context_creation_integration(self, prompt_builder, sample_score_input,
                                                     sample_template_config, mock_compiled_template):
        """Test integration of context creation in build_prompt."""
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = "Integrated test"

        with patch('src.llm.models.template_context.TemplateContext.from_score_input') as mock_from_score:
            mock_context = Mock(spec=TemplateContext)
            mock_context.warnings = []
            mock_context.apply_content_limits = Mock()
            mock_context.add_warning = Mock()
            mock_context.to_jinja_dict = Mock(return_value={})
            mock_from_score.return_value = mock_context

            prompt = prompt_builder.build_prompt(sample_score_input, sample_template_config)

            mock_from_score.assert_called_once_with(sample_score_input)
            mock_context.apply_content_limits.assert_called_once()

    def test_build_prompt_logging_integration(self, prompt_builder, sample_score_input,
                                            sample_template_config, mock_compiled_template, caplog):
        """Test that appropriate log messages are generated."""
        prompt_builder.template_loader.compile_template.return_value = mock_compiled_template
        mock_compiled_template.render.return_value = "Logging test content"

        with caplog.at_level("INFO"):
            prompt_builder.build_prompt(sample_score_input, sample_template_config)

        # Check that relevant log messages were generated
        log_messages = [record.message for record in caplog.records]
        assert any("Built prompt:" in msg for msg in log_messages)

    @pytest.mark.parametrize("provider,expected_items", [
        ("gemini", 3),
        ("openai", 4),
        ("claude", 5),
        ("unknown", 3)
    ])
    def test_provider_specific_limits(self, prompt_builder, sample_template_context, provider, expected_items):
        """Test provider-specific optimization limits."""
        optimized = prompt_builder.optimize_context_for_provider(sample_template_context, provider)

        assert optimized.generation_metadata['optimized_for'] == provider
        # Verify optimization was applied
        assert 'optimization_applied' in optimized.generation_metadata

    def test_build_prompt_end_to_end_realistic(self, prompt_builder_default, sample_score_input):
        """Test end-to-end prompt building with realistic data."""
        # Create a real template config (mocking file operations)
        template_config = ReportTemplate(
            name="realistic_template",
            file_path="/mock/path/template.md",
            description="Realistic test template"
        )

        # Mock the template loading and compilation
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = """# Code Review Report

Repository: https://github.com/test/repository.git
Total Score: 22.5/100 (22.5%)

## Strengths
✅ Static Linting Passed

## Areas for Improvement
❌ README Documentation
"""

        with patch.object(prompt_builder_default.template_loader, 'compile_template',
                         return_value=mock_template):
            prompt = prompt_builder_default.build_prompt(sample_score_input, template_config)

            assert isinstance(prompt, str)
            assert "Code Review Report" in prompt
            assert "https://github.com/test/repository.git" in prompt
            assert "22.5" in prompt