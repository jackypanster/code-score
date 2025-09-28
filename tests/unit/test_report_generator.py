"""
Unit tests for ReportGenerator class.

This module tests all functionality of the ReportGenerator class including
report generation, LLM integration, error handling, and validation.
"""

import json
import subprocess
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.llm.models.generated_report import GeneratedReport
from src.llm.models.llm_provider_config import LLMProviderConfig
from src.llm.models.report_template import ReportTemplate
from src.llm.prompt_builder import PromptBuilder, PromptBuilderError

# Import the modules to test
from src.llm.report_generator import LLMProviderError, ReportGenerator, ReportGeneratorError
from src.llm.template_loader import TemplateLoader, TemplateLoaderError


class TestReportGenerator:
    """Unit tests for ReportGenerator class."""

    @pytest.fixture
    def mock_template_loader(self):
        """Create mock TemplateLoader for testing."""
        loader = Mock(spec=TemplateLoader)
        return loader

    @pytest.fixture
    def mock_prompt_builder(self):
        """Create mock PromptBuilder for testing."""
        builder = Mock(spec=PromptBuilder)
        builder.validate_context_data.return_value = []  # No validation issues
        builder.build_prompt.return_value = "Test prompt content"
        return builder

    @pytest.fixture
    def report_generator(self, mock_template_loader, mock_prompt_builder):
        """Create ReportGenerator instance for testing."""
        return ReportGenerator(template_loader=mock_template_loader,
                             prompt_builder=mock_prompt_builder)

    @pytest.fixture
    def report_generator_default(self):
        """Create ReportGenerator with default dependencies."""
        return ReportGenerator()

    @pytest.fixture
    def sample_score_input_data(self):
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
                        "evaluation_status": "met",
                        "score": 15.0
                    }
                ],
                "total_score": 22.5,
                "max_possible_score": 100,
                "category_breakdowns": {
                    "code_quality": {"score": 15.0, "max_points": 40}
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
            }
        }

    @pytest.fixture
    def sample_template_config(self):
        """Sample ReportTemplate configuration."""
        return ReportTemplate(
            name="test_template",
            file_path="/path/to/template.md",
            description="Test template",
            required_fields=["repository", "total", "met_items"]
        )

    @pytest.fixture
    def sample_provider_config(self):
        """Sample LLMProviderConfig for testing."""
        return LLMProviderConfig(
            provider_name="test_provider",
            cli_command=["echo", "Test LLM Response"],
            model_name="test-model",
            timeout_seconds=30,
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.fixture
    def temp_score_input_file(self, sample_score_input_data):
        """Create temporary score_input.json file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_score_input_data, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_init_with_dependencies(self, mock_template_loader, mock_prompt_builder):
        """Test ReportGenerator initialization with provided dependencies."""
        generator = ReportGenerator(template_loader=mock_template_loader,
                                  prompt_builder=mock_prompt_builder)

        assert generator.template_loader is mock_template_loader
        assert generator.prompt_builder is mock_prompt_builder
        assert isinstance(generator._default_providers, dict)

    def test_init_default_dependencies(self):
        """Test ReportGenerator initialization with default dependencies."""
        generator = ReportGenerator()

        assert isinstance(generator.template_loader, TemplateLoader)
        assert isinstance(generator.prompt_builder, PromptBuilder)
        assert isinstance(generator._default_providers, dict)

    @patch('subprocess.run')
    def test_generate_report_success(self, mock_subprocess, report_generator,
                                   temp_score_input_file, sample_template_config):
        """Test successful report generation."""
        # Setup mocks
        report_generator.template_loader.load_default_template.return_value = sample_template_config
        report_generator._default_providers = {
            'test_provider': Mock(spec=LLMProviderConfig,
                                provider_name='test_provider',
                                timeout_seconds=30,
                                validate_environment=Mock(return_value=[]),
                                build_cli_command=Mock(return_value=['echo', 'Test Response']))
        }

        # Mock subprocess call
        mock_subprocess.return_value.stdout = "# Test Report\n\nGenerated content"
        mock_subprocess.return_value.returncode = 0

        result = report_generator.generate_report(
            score_input_path=temp_score_input_file,
            output_path="/tmp/test_report.md",
            provider="test_provider"
        )

        assert result['success'] is True
        assert result['output_path'] == "/tmp/test_report.md"
        assert 'generation_time_seconds' in result
        assert 'report_metadata' in result

    def test_generate_report_file_not_found(self, report_generator):
        """Test report generation with non-existent score input file."""
        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator.generate_report("/non/existent/file.json")

        assert "Score input file not found" in str(exc_info.value)

    def test_generate_report_invalid_json(self, report_generator):
        """Test report generation with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(ReportGeneratorError) as exc_info:
                report_generator.generate_report(temp_path)

            assert "Invalid JSON in score input" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_generate_report_validation_errors(self, report_generator, temp_score_input_file):
        """Test report generation with validation errors."""
        # Setup mock to return validation issues
        report_generator.prompt_builder.validate_context_data.return_value = [
            "Missing required field: test_field"
        ]

        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator.generate_report(temp_score_input_file)

        assert "Invalid score input data" in str(exc_info.value)

    def test_generate_report_template_loading_error(self, report_generator, temp_score_input_file):
        """Test report generation with template loading error."""
        # Setup mock to raise TemplateLoaderError
        report_generator.template_loader.load_default_template.side_effect = TemplateLoaderError("Template error")

        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator.generate_report(temp_score_input_file)

        assert "Template loading failed" in str(exc_info.value)

    def test_generate_report_unknown_provider(self, report_generator, temp_score_input_file):
        """Test report generation with unknown provider."""
        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator.generate_report(temp_score_input_file, provider="unknown_provider")

        assert "Unknown provider: unknown_provider" in str(exc_info.value)

    def test_generate_report_provider_environment_error(self, report_generator, temp_score_input_file,
                                                       sample_template_config):
        """Test report generation with provider environment issues."""
        # Setup template loading
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        # Setup provider with missing environment variables
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.validate_environment.return_value = ['MISSING_API_KEY']
        report_generator._default_providers = {'test_provider': mock_provider}

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator.generate_report(temp_score_input_file, provider="test_provider")

        assert "Missing environment variables" in str(exc_info.value)

    def test_generate_report_prompt_building_error(self, report_generator, temp_score_input_file,
                                                  sample_template_config):
        """Test report generation with prompt building error."""
        # Setup mocks
        report_generator.template_loader.load_default_template.return_value = sample_template_config
        report_generator._default_providers = {
            'test_provider': Mock(validate_environment=Mock(return_value=[]))
        }
        report_generator.prompt_builder.build_prompt.side_effect = PromptBuilderError("Prompt error")

        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator.generate_report(temp_score_input_file, provider="test_provider")

        assert "Report generation failed" in str(exc_info.value)

    @patch('subprocess.run')
    def test_generate_report_llm_subprocess_error(self, mock_subprocess, report_generator,
                                                temp_score_input_file, sample_template_config):
        """Test report generation with LLM subprocess error."""
        # Setup mocks
        report_generator.template_loader.load_default_template.return_value = sample_template_config
        report_generator._default_providers = {
            'test_provider': Mock(spec=LLMProviderConfig,
                                provider_name='test_provider',
                                timeout_seconds=30,
                                validate_environment=Mock(return_value=[]),
                                build_cli_command=Mock(return_value=['false']))  # Command that fails
        }

        # Mock subprocess to raise CalledProcessError
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'false', stderr="Error message")

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator.generate_report(temp_score_input_file, provider="test_provider")

        assert "LLM provider failed" in str(exc_info.value)

    def test_load_score_input_success(self, report_generator, temp_score_input_file):
        """Test successful score input loading."""
        data = report_generator._load_score_input(temp_score_input_file)

        assert isinstance(data, dict)
        assert 'repository_info' in data
        assert 'evaluation_result' in data

    def test_load_score_input_file_not_found(self, report_generator):
        """Test score input loading with non-existent file."""
        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator._load_score_input("/non/existent/file.json")

        assert "Score input file not found" in str(exc_info.value)

    def test_load_template_with_path(self, report_generator, sample_template_config):
        """Test template loading with specific path."""
        report_generator.template_loader.load_template.return_value = sample_template_config

        template = report_generator._load_template("/path/to/template.md")

        assert template is sample_template_config
        report_generator.template_loader.load_template.assert_called_once_with("/path/to/template.md")

    def test_load_template_default(self, report_generator, sample_template_config):
        """Test loading default template."""
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        template = report_generator._load_template(None)

        assert template is sample_template_config
        report_generator.template_loader.load_default_template.assert_called_once()

    def test_get_provider_config_success(self, report_generator, sample_provider_config):
        """Test getting provider configuration."""
        report_generator._default_providers = {'test_provider': sample_provider_config}

        config = report_generator._get_provider_config('test_provider', None)

        assert config is sample_provider_config

    def test_get_provider_config_with_timeout_override(self, report_generator, sample_provider_config):
        """Test getting provider configuration with timeout override."""
        report_generator._default_providers = {'test_provider': sample_provider_config}

        config = report_generator._get_provider_config('test_provider', 60)

        assert config.timeout_seconds == 60

    def test_get_provider_config_unknown_provider(self, report_generator):
        """Test getting configuration for unknown provider."""
        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator._get_provider_config('unknown_provider', None)

        assert "Unknown provider: unknown_provider" in str(exc_info.value)

    @patch('subprocess.run')
    def test_call_llm_success(self, mock_subprocess, report_generator, sample_provider_config):
        """Test successful LLM call."""
        mock_subprocess.return_value.stdout = "Generated response"
        mock_subprocess.return_value.returncode = 0

        response = report_generator._call_llm("Test prompt", sample_provider_config)

        assert response == "Generated response"
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    def test_call_llm_empty_response(self, mock_subprocess, report_generator, sample_provider_config):
        """Test LLM call with empty response."""
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.returncode = 0

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator._call_llm("Test prompt", sample_provider_config)

        assert "Empty response from LLM provider" in str(exc_info.value)

    @patch('subprocess.run')
    def test_call_llm_timeout(self, mock_subprocess, report_generator, sample_provider_config):
        """Test LLM call with timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired('cmd', 30)

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator._call_llm("Test prompt", sample_provider_config)

        assert "LLM call timed out" in str(exc_info.value)

    @patch('subprocess.run')
    def test_call_llm_process_error(self, mock_subprocess, report_generator, sample_provider_config):
        """Test LLM call with process error."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, 'cmd', stderr="Authentication failed"
        )

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator._call_llm("Test prompt", sample_provider_config)

        assert "LLM provider failed" in str(exc_info.value)
        assert "Authentication failed" in str(exc_info.value)

    @patch('subprocess.run')
    def test_call_llm_file_not_found(self, mock_subprocess, report_generator, sample_provider_config):
        """Test LLM call with CLI not found."""
        mock_subprocess.side_effect = FileNotFoundError()

        with pytest.raises(LLMProviderError) as exc_info:
            report_generator._call_llm("Test prompt", sample_provider_config)

        assert "LLM provider CLI not found" in str(exc_info.value)

    @patch('threading.Thread')
    def test_call_llm_with_progress_indicator(self, mock_thread, report_generator):
        """Test LLM call that shows progress indicator for long timeouts."""
        # Create provider config with long timeout
        provider_config = LLMProviderConfig(
            provider_name="slow_provider",
            cli_command=["echo", "response"],
            timeout_seconds=60  # Long timeout should trigger progress indicator
        )

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.stdout = "Response"
            mock_subprocess.return_value.returncode = 0

            response = report_generator._call_llm("Test prompt", provider_config)

            assert response == "Response"
            mock_thread.assert_called_once()  # Progress thread should be created

    @patch('sys.stderr')
    @patch('time.time')
    def test_show_progress_indicator(self, mock_time, mock_stderr, report_generator):
        """Test progress indicator functionality."""
        # Mock time progression
        mock_time.side_effect = [0, 0.1, 0.2, 0.3, 35.0]  # Simulate timeout after a few cycles

        stop_event = threading.Event()

        # Should exit early when time runs out
        report_generator._show_progress_indicator(stop_event, 30)

        # Check that stderr was written to
        assert mock_stderr.write.call_count > 0

    def test_create_generated_report(self, report_generator, sample_score_input_data,
                                   sample_template_config, sample_provider_config):
        """Test creating GeneratedReport from components."""
        llm_response = "# Test Report\n\nGenerated content"

        report = report_generator._create_generated_report(
            llm_response, sample_score_input_data, sample_template_config,
            sample_provider_config, 5.0
        )

        assert isinstance(report, GeneratedReport)
        assert report.content == llm_response
        assert report.template_used.template_name == sample_template_config.name
        assert report.provider_used.provider_name == sample_provider_config.provider_name
        assert report.provider_used.response_time_seconds == 5.0

    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.mkdir')
    def test_save_report(self, mock_mkdir, mock_write_text, report_generator):
        """Test saving generated report to file."""
        # Create mock report
        mock_report = Mock(spec=GeneratedReport)
        mock_report.to_file_content.return_value = "Report content"

        output_path = "/tmp/test_report.md"

        report_generator._save_report(mock_report, output_path)

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once_with("Report content", encoding='utf-8')

    @patch('pathlib.Path.write_text')
    def test_save_report_error(self, mock_write_text, report_generator):
        """Test report saving with write error."""
        mock_write_text.side_effect = OSError("Permission denied")
        mock_report = Mock(spec=GeneratedReport)
        mock_report.to_file_content.return_value = "Report content"

        with pytest.raises(ReportGeneratorError) as exc_info:
            report_generator._save_report(mock_report, "/tmp/test_report.md")

        assert "Failed to save report" in str(exc_info.value)

    @patch('subprocess.run')
    def test_validate_prerequisites_success(self, mock_subprocess, report_generator,
                                          sample_template_config):
        """Test prerequisite validation when all requirements are met."""
        # Setup mocks
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.validate_environment.return_value = []
        mock_provider.cli_command = ['test_cli']
        report_generator._default_providers = {'test_provider': mock_provider}
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        # Mock successful CLI check
        mock_subprocess.return_value.returncode = 0

        results = report_generator.validate_prerequisites('test_provider')

        assert results['valid'] is True
        assert results['provider_available'] is True
        assert results['environment_valid'] is True
        assert results['template_available'] is True
        assert len(results['issues']) == 0

    def test_validate_prerequisites_unknown_provider(self, report_generator):
        """Test prerequisite validation with unknown provider."""
        results = report_generator.validate_prerequisites('unknown_provider')

        assert results['valid'] is False
        assert results['provider_available'] is False
        assert any("Unknown provider" in issue for issue in results['issues'])

    def test_validate_prerequisites_missing_environment(self, report_generator, sample_template_config):
        """Test prerequisite validation with missing environment variables."""
        # Setup mock provider with missing environment variables
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.validate_environment.return_value = ['MISSING_API_KEY']
        mock_provider.cli_command = ['test_cli']
        report_generator._default_providers = {'test_provider': mock_provider}
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        results = report_generator.validate_prerequisites('test_provider')

        assert results['valid'] is False
        assert results['environment_valid'] is False
        assert any("Missing environment variables" in issue for issue in results['issues'])

    @patch('subprocess.run')
    def test_validate_prerequisites_cli_not_available(self, mock_subprocess, report_generator,
                                                    sample_template_config):
        """Test prerequisite validation when CLI is not available."""
        # Setup mocks
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.validate_environment.return_value = []
        mock_provider.cli_command = ['missing_cli']
        report_generator._default_providers = {'test_provider': mock_provider}
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        # Mock CLI not found
        mock_subprocess.side_effect = FileNotFoundError()

        results = report_generator.validate_prerequisites('test_provider')

        assert results['valid'] is False
        assert any("Provider CLI not available" in issue for issue in results['issues'])

    def test_validate_prerequisites_template_error(self, report_generator):
        """Test prerequisite validation when template loading fails."""
        # Setup mock provider
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.validate_environment.return_value = []
        report_generator._default_providers = {'test_provider': mock_provider}
        report_generator.template_loader.load_default_template.side_effect = Exception("Template error")

        results = report_generator.validate_prerequisites('test_provider')

        assert results['valid'] is False
        assert results['template_available'] is False
        assert any("Default template not available" in issue for issue in results['issues'])

    @patch('subprocess.run')
    def test_get_available_providers(self, mock_subprocess, report_generator):
        """Test getting available providers with status."""
        # Setup mock providers
        mock_provider1 = Mock(spec=LLMProviderConfig)
        mock_provider1.model_name = "model1"
        mock_provider1.timeout_seconds = 30
        mock_provider1.validate_environment.return_value = []
        mock_provider1.cli_command = ['cli1']

        mock_provider2 = Mock(spec=LLMProviderConfig)
        mock_provider2.model_name = "model2"
        mock_provider2.timeout_seconds = 60
        mock_provider2.validate_environment.return_value = ['MISSING_KEY']
        mock_provider2.cli_command = ['cli2']

        report_generator._default_providers = {
            'provider1': mock_provider1,
            'provider2': mock_provider2
        }

        # Mock CLI availability
        def subprocess_side_effect(cmd, **kwargs):
            if cmd[0] == 'cli1':
                return Mock(returncode=0)
            else:
                raise FileNotFoundError()

        mock_subprocess.side_effect = subprocess_side_effect

        providers = report_generator.get_available_providers()

        assert len(providers) == 2

        provider1_info = next(p for p in providers if p['name'] == 'provider1')
        assert provider1_info['available'] is True
        assert provider1_info['environment_ready'] is True

        provider2_info = next(p for p in providers if p['name'] == 'provider2')
        assert provider2_info['available'] is False
        assert provider2_info['environment_ready'] is False
        assert 'MISSING_KEY' in provider2_info['missing_variables']

    def test_get_template_info_success(self, report_generator, sample_template_config):
        """Test getting template information."""
        report_generator.template_loader.load_template.return_value = sample_template_config

        info = report_generator.get_template_info("/path/to/template.md")

        assert info['valid'] is True
        assert info['name'] == sample_template_config.name
        assert info['path'] == sample_template_config.file_path
        assert info['required_fields'] == sample_template_config.required_fields

    def test_get_template_info_default(self, report_generator, sample_template_config):
        """Test getting default template information."""
        report_generator.template_loader.load_default_template.return_value = sample_template_config

        info = report_generator.get_template_info()

        assert info['valid'] is True
        assert info['name'] == sample_template_config.name

    def test_get_template_info_error(self, report_generator):
        """Test getting template information when loading fails."""
        report_generator.template_loader.load_default_template.side_effect = Exception("Template error")

        info = report_generator.get_template_info()

        assert info['valid'] is False
        assert "Template error" in info['error']

    def test_exception_hierarchy(self):
        """Test exception hierarchy is correct."""
        assert issubclass(LLMProviderError, ReportGeneratorError)
        assert issubclass(ReportGeneratorError, Exception)

    @patch('subprocess.run')
    def test_generate_report_verbose_logging(self, mock_subprocess, report_generator,
                                           temp_score_input_file, sample_template_config, caplog):
        """Test report generation with verbose logging enabled."""
        # Setup mocks
        report_generator.template_loader.load_default_template.return_value = sample_template_config
        report_generator._default_providers = {
            'test_provider': Mock(spec=LLMProviderConfig,
                                provider_name='test_provider',
                                timeout_seconds=30,
                                validate_environment=Mock(return_value=[]),
                                build_cli_command=Mock(return_value=['echo', 'Response']))
        }
        mock_subprocess.return_value.stdout = "Test response"
        mock_subprocess.return_value.returncode = 0

        with caplog.at_level("DEBUG"):
            report_generator.generate_report(
                temp_score_input_file,
                provider="test_provider",
                verbose=True
            )

        # Check that debug messages were logged
        debug_messages = [record.message for record in caplog.records if record.levelname == "DEBUG"]
        assert len(debug_messages) > 0

    @patch('subprocess.run')
    def test_generate_report_custom_timeout(self, mock_subprocess, report_generator,
                                          temp_score_input_file, sample_template_config):
        """Test report generation with custom timeout."""
        # Setup mocks
        report_generator.template_loader.load_default_template.return_value = sample_template_config
        mock_provider = Mock(spec=LLMProviderConfig)
        mock_provider.provider_name = 'test_provider'
        mock_provider.timeout_seconds = 30  # Will be overridden
        mock_provider.validate_environment.return_value = []
        mock_provider.build_cli_command.return_value = ['echo', 'Response']
        report_generator._default_providers = {'test_provider': mock_provider}

        mock_subprocess.return_value.stdout = "Test response"
        mock_subprocess.return_value.returncode = 0

        report_generator.generate_report(
            temp_score_input_file,
            provider="test_provider",
            timeout=120
        )

        # Verify timeout was updated
        assert mock_provider.timeout_seconds == 120

    def test_integration_with_real_dependencies(self, sample_score_input_data, temp_score_input_file):
        """Test ReportGenerator with real TemplateLoader and PromptBuilder."""
        generator = ReportGenerator()

        # Mock the LLM provider call since we don't want to make real API calls
        with patch.object(generator, '_call_llm', return_value="# Mock Report\nGenerated content"), \
             patch.object(generator, '_save_report'), \
             patch.object(generator.template_loader, 'load_default_template') as mock_load_template:

            # Setup template mock
            mock_template = ReportTemplate(
                name="test_template",
                file_path="/mock/path.md",
                description="Test template"
            )
            mock_load_template.return_value = mock_template

            # Mock provider config
            generator._default_providers = {
                'mock_provider': Mock(
                    provider_name='mock_provider',
                    timeout_seconds=30,
                    validate_environment=Mock(return_value=[])
                )
            }

            result = generator.generate_report(
                temp_score_input_file,
                provider="mock_provider"
            )

            assert result['success'] is True
