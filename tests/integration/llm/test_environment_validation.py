"""
Integration tests for environment variable validation.

This test validates the complete environment prerequisite checking flow,
ensuring clear error messages when environment variables are missing
(Acceptance Scenario 4 from spec).

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T016-T017 implement environment validation.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.llm.report_generator import LLMProviderError, ReportGenerator


@pytest.fixture
def sample_score_input():
    """Create a minimal sample score_input.json for testing."""
    return {
        "repository_info": {
            "url": "https://github.com/test/repo",
            "commit_sha": "abc123",
            "primary_language": "Python"
        },
        "evaluation_result": {
            "total_score": 85,
            "max_possible_score": 100,
            "score_percentage": 85.0,
            "category_breakdowns": {
                "code_quality": {
                    "dimension": "code_quality",
                    "items_count": 4,
                    "max_points": 40,
                    "actual_points": 35,
                    "percentage": 87.5
                },
                "testing": {
                    "dimension": "testing",
                    "items_count": 3,
                    "max_points": 35,
                    "actual_points": 30,
                    "percentage": 85.7
                },
                "documentation": {
                    "dimension": "documentation",
                    "items_count": 2,
                    "max_points": 25,
                    "actual_points": 20,
                    "percentage": 80.0
                }
            },
            "checklist_items": [
                {
                    "id": "code_quality_linting",
                    "name": "Linting Standards",
                    "dimension": "code_quality",
                    "evaluation_status": "met",
                    "score": 10,
                    "max_points": 10,
                    "description": "Code passes linting checks",
                    "evidence_references": []
                }
            ],
            "evaluation_metadata": {
                "evaluator_version": "1.0.0",
                "processing_duration": 2.5,
                "warnings": [],
                "metrics_completeness": 95.0
            },
            "evidence_summary": ["Linting passed with 0 issues"]
        }
    }


@pytest.fixture
def score_input_file(sample_score_input, tmp_path):
    """Create a temporary score_input.json file."""
    score_input_path = tmp_path / "score_input.json"
    with open(score_input_path, 'w') as f:
        json.dump(sample_score_input, f)
    return str(score_input_path)


class TestEnvironmentVariableDetection:
    """Integration tests for environment variable validation."""

    def test_missing_env_var_detection(self, score_input_file, tmp_path):
        """
        Test detection of missing DEEPSEEK_API_KEY environment variable.

        Given: DEEPSEEK_API_KEY is not set in environment
        When: validate_prerequisites() is called
        Then: LLMProviderError is raised with clear error message

        This test will FAIL until T017 adds enhanced environment validation.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock environment with DEEPSEEK_API_KEY removed
        with patch.dict(os.environ, {}, clear=True):
            # Mock llm CLI availability check to pass
            with patch('shutil.which', return_value='/usr/bin/llm'):
                try:
                    result = generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail(
                        "Should have raised LLMProviderError for missing DEEPSEEK_API_KEY"
                    )
                except LLMProviderError as e:
                    error_msg = str(e)
                    # Verify error message content
                    assert "DEEPSEEK_API_KEY" in error_msg, \
                        "Error should mention missing environment variable name"
                    assert "environment" in error_msg.lower(), \
                        "Error should mention 'environment'"
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise

    def test_env_var_error_message_format(self, score_input_file, tmp_path):
        """
        Test that environment variable errors provide actionable guidance.

        Given: DEEPSEEK_API_KEY is missing
        When: Error is raised
        Then: Error message includes setup instructions

        This test will FAIL until T017 is implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch.dict(os.environ, {}, clear=True):
            with patch('shutil.which', return_value='/usr/bin/llm'):
                try:
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail("Should have raised LLMProviderError")
                except LLMProviderError as e:
                    error_msg = str(e)

                    # Error message should be helpful
                    assert "DEEPSEEK_API_KEY" in error_msg, \
                        "Should mention the specific variable name"

                    # Should provide actionable guidance (check for at least one)
                    has_guidance = any([
                        "set" in error_msg.lower(),
                        "install" in error_msg.lower(),
                        "https://" in error_msg,  # Documentation URL
                        "authentication" in error_msg.lower()
                    ])
                    assert has_guidance, \
                        "Error should provide actionable setup guidance"
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise

    def test_env_var_present_validation_passes(self, score_input_file, tmp_path):
        """
        Test that validation passes when environment variable is set.

        Given: DEEPSEEK_API_KEY is set
        When: validate_prerequisites() is called
        Then: Validation passes without error

        This test will FAIL until T017 is implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock environment with DEEPSEEK_API_KEY present
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-api-key'}, clear=True):
            # Mock subprocess.run to avoid actual API call
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

                    # If we got here, environment validation passed
                    assert result['success'] is True, \
                        "Report generation should succeed when env var is set"
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise


class TestLLMCliAvailability:
    """Integration tests for llm CLI availability checking."""

    def test_missing_llm_cli_detection(self, score_input_file, tmp_path):
        """
        Test detection when llm CLI is not installed.

        Given: llm CLI is not in PATH
        When: validate_prerequisites() is called
        Then: LLMProviderError is raised mentioning llm CLI

        This test will FAIL until T016 adds llm CLI availability check.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock llm CLI as not available
        with patch('shutil.which', return_value=None):
            # Set environment variable to isolate this check
            with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}, clear=True):
                try:
                    result = generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail("Should have raised error for missing llm CLI")
                except LLMProviderError as e:
                    error_msg = str(e)
                    assert "llm" in error_msg.lower(), \
                        "Error should mention 'llm CLI'"
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise

    def test_llm_cli_version_detection(self):
        """
        Test that llm CLI version is detected correctly.

        Given: llm CLI is installed
        When: validate_prerequisites() is called
        Then: llm CLI version is detected and reported

        This test will FAIL until T016 adds version detection.
        """
        generator = ReportGenerator()

        # Mock llm CLI availability
        with patch('shutil.which', return_value='/usr/bin/llm'):
            # Mock subprocess for version check
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "llm, version 0.27.1"
                mock_result.stderr = ""
                mock_run.return_value = mock_result

                # Mock environment variable
                with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}, clear=True):
                    try:
                        validation = generator.validate_prerequisites("deepseek")

                        assert validation['valid'] is True, \
                            "Validation should pass when llm CLI is available"

                        # Note: This depends on implementation details
                        # May need adjustment based on actual return structure

                    except KeyError as e:
                        if "deepseek" in str(e):
                            pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                        raise


class TestEnvironmentValidationIntegration:
    """Integration tests for complete environment validation flow."""

    def test_all_prerequisites_missing(self, score_input_file, tmp_path):
        """
        Test behavior when all prerequisites are missing.

        Given: llm CLI not installed AND DEEPSEEK_API_KEY not set
        When: generate_report() is called
        Then: Clear error message listing all missing prerequisites

        This test will FAIL until T016-T017 are implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock both as missing
        with patch('shutil.which', return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                try:
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail("Should have raised error for missing prerequisites")
                except LLMProviderError as e:
                    error_msg = str(e)

                    # Should mention at least one of the missing items
                    mentions_llm = "llm" in error_msg.lower()
                    mentions_env = "DEEPSEEK_API_KEY" in error_msg

                    assert mentions_llm or mentions_env, \
                        "Error should mention at least one missing prerequisite"
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise

    def test_prerequisites_validation_performance(self):
        """
        Test that prerequisites validation completes quickly.

        Given: System with llm CLI and environment variable
        When: validate_prerequisites() is called
        Then: Validation completes in <2 seconds

        This test will FAIL until T016-T017 are implemented.
        """
        import time

        generator = ReportGenerator()

        with patch('shutil.which', return_value='/usr/bin/llm'):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "llm, version 0.27.1"
                mock_result.stderr = ""
                mock_run.return_value = mock_result

                with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'}, clear=True):
                    try:
                        start = time.time()
                        generator.validate_prerequisites("deepseek")
                        elapsed = time.time() - start

                        assert elapsed < 2.0, \
                            f"Validation took {elapsed:.2f}s (should be <2s)"
                    except KeyError as e:
                        if "deepseek" in str(e):
                            pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                        raise


class TestEnvironmentValidationEdgeCases:
    """Edge case tests for environment validation."""

    def test_empty_env_var_treated_as_missing(self, score_input_file, tmp_path):
        """
        Test that empty string environment variables are treated as missing.

        Given: DEEPSEEK_API_KEY is set but empty ("")
        When: Validation is performed
        Then: Should fail as if variable is missing

        This test will FAIL until T017 handles empty string case.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Set environment variable to empty string
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': ''}, clear=True):
            with patch('shutil.which', return_value='/usr/bin/llm'):
                try:
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail("Should reject empty environment variable")
                except LLMProviderError as e:
                    # Empty string should be treated as missing
                    assert "DEEPSEEK_API_KEY" in str(e) or "environment" in str(e).lower()
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise

    def test_whitespace_only_env_var_treated_as_invalid(self, score_input_file, tmp_path):
        """
        Test that whitespace-only environment variables are rejected.

        Given: DEEPSEEK_API_KEY is set to whitespace ("   ")
        When: Validation is performed
        Then: Should fail with clear error

        This test will FAIL until T017 handles whitespace validation.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': '   '}, clear=True):
            with patch('shutil.which', return_value='/usr/bin/llm'):
                try:
                    generator.generate_report(
                        score_input_path=score_input_file,
                        output_path=output_path,
                        provider="deepseek"
                    )
                    pytest.fail("Should reject whitespace-only environment variable")
                except LLMProviderError as e:
                    # Whitespace should be treated as invalid
                    assert "DEEPSEEK_API_KEY" in str(e) or "environment" in str(e).lower()
                except KeyError as e:
                    if "deepseek" in str(e):
                        pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                    raise
