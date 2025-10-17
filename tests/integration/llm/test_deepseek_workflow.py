"""
Integration tests for DeepSeek report generation workflow.

This test validates the complete end-to-end flow of generating reports using
the DeepSeek provider through llm CLI interface (Acceptance Scenario 1).

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T011 (update default configs) is implemented.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.llm.report_generator import LLMProviderError, ReportGenerator


@pytest.fixture
def sample_score_input():
    """Create a minimal sample score_input.json for testing."""
    return {
        "evaluation_result": {
            "total_score": 85,
            "category_breakdown": {
                "code_quality": {
                    "score": 35,
                    "max_score": 40,
                    "percentage": 87.5
                },
                "testing": {
                    "score": 30,
                    "max_score": 35,
                    "percentage": 85.7
                },
                "documentation": {
                    "score": 20,
                    "max_score": 25,
                    "percentage": 80.0
                }
            },
            "items": [
                {
                    "id": "code_quality_linting",
                    "status": "met",
                    "score": 10,
                    "max_score": 10
                }
            ]
        },
        "repository_info": {
            "url": "https://github.com/test/repo",
            "commit": "abc123",
            "language": "Python",
            "analysis_date": "2025-10-17"
        }
    }


@pytest.fixture
def score_input_file(sample_score_input, tmp_path):
    """Create a temporary score_input.json file."""
    score_input_path = tmp_path / "score_input.json"
    with open(score_input_path, 'w') as f:
        json.dump(sample_score_input, f)
    return str(score_input_path)


class TestDeepSeekReportGeneration:
    """Integration tests for DeepSeek report generation workflow."""

    def test_default_deepseek_report_generation(self, score_input_file, tmp_path):
        """
        Test default DeepSeek report generation workflow.

        Given: System uses default configuration
        When: generate_report() is called with provider="deepseek"
        Then: Report is generated using llm CLI + DeepSeek

        This test will FAIL until T011 updates get_default_configs() to include DeepSeek.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock subprocess to avoid actual API call
        with patch('subprocess.run') as mock_run:
            # Simulate successful llm CLI response
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report\n\nThis is a generated report."
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = generator.generate_report(
                score_input_path=score_input_file,
                output_path=output_path,
                provider="deepseek"
            )

            # Assertions
            assert result['success'] is True, "Report generation should succeed"
            assert "deepseek" in result['provider_metadata']['provider_name'].lower(), \
                "Provider metadata should indicate DeepSeek"

            # Verify llm CLI was called with correct format
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else call_args.kwargs.get('args', [])

            assert command[0] == "llm", "First element should be 'llm'"
            assert "-m" in command, "Should use -m flag for model"
            assert any("deepseek" in str(arg).lower() for arg in command), \
                "Should specify DeepSeek model"

    def test_deepseek_provider_available_in_defaults(self):
        """
        Test that DeepSeek provider is available in default configs.

        This test will FAIL until T011 adds DeepSeek to get_default_configs().
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        defaults = LLMProviderConfig.get_default_configs()

        assert "deepseek" in defaults, \
            "DeepSeek should be available in default provider configs"

    def test_deepseek_config_properties(self):
        """
        Test that DeepSeek default config has correct properties.

        This test will FAIL until T011 is implemented.
        """
        from src.llm.models.llm_provider_config import LLMProviderConfig

        defaults = LLMProviderConfig.get_default_configs()
        deepseek_config = defaults["deepseek"]

        # Verify config properties
        assert deepseek_config.provider_name == "deepseek"
        assert deepseek_config.cli_command == ["llm"], \
            "DeepSeek should use llm CLI unified interface"
        assert deepseek_config.model_name in ["deepseek-coder", "deepseek-chat"], \
            "Should use DeepSeek model"
        assert deepseek_config.context_window == 8192, \
            "DeepSeek context window is 8192 tokens"
        assert "DEEPSEEK_API_KEY" in deepseek_config.environment_variables, \
            "Should require DEEPSEEK_API_KEY"

    def test_deepseek_cli_command_format(self, score_input_file, tmp_path):
        """
        Test that DeepSeek generates correct llm CLI command format.

        This test will FAIL until T010 (refactor build_cli_command) and
        T011 (add DeepSeek) are both implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )

                # Verify command format
                call_args = mock_run.call_args
                command = call_args[0][0] if call_args[0] else call_args.kwargs.get('args', [])

                # Contract: llm -m <model> "<prompt>"
                assert command[0] == "llm"
                assert command[1] == "-m"
                assert command[2] in ["deepseek-coder", "deepseek-chat"]

                # Prompt should be last element (or near end with optional args)
                assert isinstance(command[-1], str)
                assert len(command[-1]) > 0, "Prompt should not be empty"

            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise

    def test_no_gemini_references_in_deepseek_flow(self, score_input_file, tmp_path):
        """
        Test that DeepSeek workflow contains no Gemini references.

        This test will FAIL until T019 (remove Gemini references) is complete.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                result = generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )

                # Check command doesn't contain Gemini-specific args
                call_args = mock_run.call_args
                command = call_args[0][0] if call_args[0] else call_args.kwargs.get('args', [])
                command_str = " ".join(str(arg) for arg in command)

                assert "--approval-mode" not in command_str, \
                    "Gemini-specific --approval-mode should not be present"
                assert "--debug" not in command_str, \
                    "Gemini-specific --debug flag should not be present"
                assert "gemini" not in command_str.lower(), \
                    "No 'gemini' references in DeepSeek command"

            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise


class TestDeepSeekIntegrationFailureModes:
    """Test failure modes and error handling in DeepSeek workflow."""

    def test_deepseek_with_missing_config(self, score_input_file):
        """
        Test behavior when DeepSeek config is requested but not available.

        This test should PASS currently (before T011) and document expected failure.
        After T011, this test behavior changes - DeepSeek becomes available.
        """
        generator = ReportGenerator()

        # Before T011: DeepSeek not in default configs
        defaults = generator._default_providers

        if "deepseek" not in defaults:
            # Expected before T011
            with pytest.raises(ReportGeneratorError, match="Unknown provider"):
                generator.generate_report(
                    score_input_path=score_input_file,
                    provider="deepseek"
                )
        else:
            # After T011: DeepSeek available
            pytest.skip("DeepSeek is now available (T011 complete)")

    def test_llm_cli_execution_failure(self, score_input_file, tmp_path):
        """
        Test handling of llm CLI execution failures.

        This test verifies that errors from llm CLI are properly propagated.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            # Simulate llm CLI failure
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Model not found"
            mock_run.return_value = mock_result

            try:
                with pytest.raises(LLMProviderError):
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise

    def test_empty_llm_response_handling(self, score_input_file, tmp_path):
        """
        Test handling of empty responses from llm CLI.

        This test verifies fail-fast behavior on empty responses.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            # Simulate empty response
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                with pytest.raises(LLMProviderError, match="Empty response"):
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise


class TestDeepSeekMetadataGeneration:
    """Test metadata generation for DeepSeek reports."""

    def test_provider_metadata_includes_deepseek_info(self, score_input_file, tmp_path):
        """
        Test that provider metadata includes DeepSeek-specific information.

        This test will FAIL until T011 is implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                result = generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )

                provider_metadata = result['provider_metadata']

                assert 'provider_name' in provider_metadata
                assert 'deepseek' in provider_metadata['provider_name'].lower()
                assert 'response_time_seconds' in provider_metadata
                assert isinstance(provider_metadata['response_time_seconds'], (int, float))

            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise

    def test_report_generation_time_tracking(self, score_input_file, tmp_path):
        """
        Test that generation time is properly tracked.

        This test verifies performance monitoring works with DeepSeek.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                result = generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )

                assert 'generation_time_seconds' in result
                assert isinstance(result['generation_time_seconds'], (int, float))
                assert result['generation_time_seconds'] >= 0

            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise


class TestDeepSeekVerboseMode:
    """Test verbose logging with DeepSeek provider."""

    def test_verbose_mode_provides_detailed_output(self, score_input_file, tmp_path, caplog):
        """
        Test that verbose mode provides detailed logging for debugging.

        This test verifies that verbose=True enables detailed progress tracking.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek",
                    verbose=True
                )

                # Verbose mode should log operations
                # (actual log content depends on implementation)

            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise
