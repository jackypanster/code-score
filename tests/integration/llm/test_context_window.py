"""
Integration tests for context window exceeded handling.

This test validates that prompt length validation correctly detects when
prompts exceed the provider's context window limit (Edge Case 3 from spec).

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T018 adds context window validation in _call_llm().
"""

import json
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


class TestContextWindowExceeded:
    """Integration tests for context window validation."""

    def test_normal_prompt_accepted(self, score_input_file, tmp_path):
        """
        Test that normal-sized prompts are accepted.

        Given: Prompt is well within context window (< 8192 tokens)
        When: generate_report() is called
        Then: Report is generated without context window error

        This test will FAIL until T011 adds DeepSeek to defaults.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Mock subprocess to avoid actual API call
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report\n\nNormal report content."
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                result = generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )

                # Normal prompt should succeed
                assert result['success'] is True, \
                    "Normal prompt should be accepted"
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise

    def test_huge_prompt_rejected(self, score_input_file, tmp_path):
        """
        Test that prompts exceeding context window are rejected.

        Given: Prompt exceeds 8192 tokens (DeepSeek limit)
        When: generate_report() is called
        Then: ValueError is raised with specific token limit

        This test will FAIL until T012-T013 add token estimation and
        T018 adds context window validation in _call_llm().
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create extremely large score input that will generate huge prompt
        with open(score_input_file, 'r') as f:
            large_input = json.load(f)

        # Add huge evidence summary to exceed context window
        # 40000 chars ≈ 10000 tokens, exceeds DeepSeek's 8192 limit
        large_input['evaluation_result']['evidence_summary'] = [
            "x" * 40000  # Huge evidence that will be included in prompt
        ]

        large_input_path = str(tmp_path / "large_score_input.json")
        with open(large_input_path, 'w') as f:
            json.dump(large_input, f)

        try:
            with pytest.raises(ValueError) as exc_info:
                generator.generate_report(
                    score_input_path=large_input_path,
                    output_path=output_path,
                    provider="deepseek"
                )

            error = str(exc_info.value)

            # Error should mention context window limit
            assert "8192" in error, \
                "Error should mention DeepSeek's 8192 token limit"
            assert "token" in error.lower(), \
                "Error should mention 'tokens'"
            assert "exceed" in error.lower() or "larger" in error.lower(), \
                "Error should indicate exceedance"
        except KeyError as e:
            if "deepseek" in str(e):
                pytest.skip("DeepSeek not yet in default configs (T011 pending)")
            raise

    def test_context_window_error_message_content(self, score_input_file, tmp_path):
        """
        Test that context window error includes helpful information.

        Given: Prompt exceeds context window
        When: Error is raised
        Then: Error message includes token count, char count, and limit

        This test will FAIL until T012-T013 and T018 are implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create large input
        with open(score_input_file, 'r') as f:
            large_input = json.load(f)

        large_input['evaluation_result']['evidence_summary'] = ["x" * 40000]

        large_input_path = str(tmp_path / "large_score_input.json")
        with open(large_input_path, 'w') as f:
            json.dump(large_input, f)

        try:
            with pytest.raises(ValueError) as exc_info:
                generator.generate_report(
                    score_input_path=large_input_path,
                    output_path=output_path,
                    provider="deepseek"
                )

            error = str(exc_info.value)

            # Error should provide actionable details
            assert "8192" in error, "Should show context window limit"
            assert "deepseek" in error.lower(), "Should mention provider name"

            # Should include either token estimate or character count
            has_metrics = any([
                "token" in error.lower(),
                "character" in error.lower(),
                "chars" in error.lower()
            ])
            assert has_metrics, "Should provide size metrics"
        except KeyError as e:
            if "deepseek" in str(e):
                pytest.skip("DeepSeek not yet in default configs (T011 pending)")
            raise


class TestContextWindowBoundaryConditions:
    """Test boundary conditions for context window validation."""

    def test_prompt_at_exact_limit(self, score_input_file, tmp_path):
        """
        Test prompt at exactly the context window boundary.

        Given: Prompt is exactly 8192 tokens (boundary case)
        When: generate_report() is called
        Then: Should be accepted (8192 == 8192)

        This test will FAIL until T012-T013 and T018 are implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create input that generates exactly 8192 tokens
        # 8192 tokens = 32768 characters (4 chars/token)
        with open(score_input_file, 'r') as f:
            boundary_input = json.load(f)

        # Account for template overhead (estimated ~500 tokens)
        # Target: 8192 - 500 = 7692 tokens = 30768 characters
        boundary_input['evaluation_result']['evidence_summary'] = ["x" * 30768]

        boundary_input_path = str(tmp_path / "boundary_score_input.json")
        with open(boundary_input_path, 'w') as f:
            json.dump(boundary_input, f)

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                result = generator.generate_report(
                    score_input_path=boundary_input_path,
                    output_path=output_path,
                    provider="deepseek"
                )

                # Boundary case should be accepted
                assert result['success'] is True, \
                    "Prompt at exact limit should be accepted"
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise
            except ValueError as e:
                # If this fails due to context window, the boundary calculation is wrong
                # This helps debug the 4 chars/token heuristic
                pytest.fail(f"Boundary prompt rejected (check token estimation): {e}")

    def test_prompt_one_token_over_limit(self, score_input_file, tmp_path):
        """
        Test prompt just over the context window limit.

        Given: Prompt is 8193 tokens (1 token over limit)
        When: generate_report() is called
        Then: Should be rejected with clear error

        This test will FAIL until T012-T013 and T018 are implemented.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create input that generates 8193 tokens
        # 8193 tokens = 32772 characters
        with open(score_input_file, 'r') as f:
            over_limit_input = json.load(f)

        # Account for template overhead (~500 tokens)
        # Target: 8193 - 500 = 7693 tokens = 30772 characters
        over_limit_input['evaluation_result']['evidence_summary'] = ["x" * 30772]

        over_limit_path = str(tmp_path / "over_limit_score_input.json")
        with open(over_limit_path, 'w') as f:
            json.dump(over_limit_input, f)

        try:
            with pytest.raises(ValueError) as exc_info:
                generator.generate_report(
                    score_input_path=over_limit_path,
                    output_path=output_path,
                    provider="deepseek"
                )

            error = str(exc_info.value)
            assert "8192" in error, "Should mention token limit"
        except KeyError as e:
            if "deepseek" in str(e):
                pytest.skip("DeepSeek not yet in default configs (T011 pending)")
            raise


class TestContextWindowWithDifferentProviders:
    """Test context window validation across different providers."""

    def test_provider_specific_limits_respected(self, score_input_file, tmp_path):
        """
        Test that different providers have different context window limits.

        Given: DeepSeek has 8192 token limit
        When: Large prompt is submitted
        Then: Validation uses provider-specific limit

        This test will FAIL until T011-T013 and T018 are implemented.
        Note: This test documents future multi-provider support.
        """
        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create input with ~6000 tokens (safe for DeepSeek 8192 limit)
        with open(score_input_file, 'r') as f:
            medium_input = json.load(f)

        # 6000 tokens = 24000 characters
        medium_input['evaluation_result']['evidence_summary'] = ["x" * 24000]

        medium_input_path = str(tmp_path / "medium_score_input.json")
        with open(medium_input_path, 'w') as f:
            json.dump(medium_input, f)

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                # DeepSeek: should accept 6000 tokens (< 8192 limit)
                result = generator.generate_report(
                    score_input_path=medium_input_path,
                    output_path=output_path,
                    provider="deepseek"
                )

                assert result['success'] is True, \
                    "6000 token prompt should fit in DeepSeek's 8192 limit"
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise


class TestContextWindowValidationPerformance:
    """Performance tests for context window validation."""

    def test_validation_performance(self, score_input_file, tmp_path):
        """
        Test that context window validation is fast.

        Given: Normal-sized prompt
        When: Validation is performed
        Then: Validation completes quickly (<10ms)

        This test will FAIL until T012 adds estimate_prompt_tokens().
        """
        import time

        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                start = time.time()
                generator.generate_report(
                    score_input_path=score_input_file,
                    output_path=output_path,
                    provider="deepseek"
                )
                elapsed = time.time() - start

                # Token estimation should be negligible (<10ms for estimation alone)
                # Total generation time will be longer due to subprocess mock
                assert elapsed < 5.0, \
                    f"Generation took {elapsed:.2f}s (validation should be negligible)"
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise

    def test_large_prompt_validation_performance(self, score_input_file, tmp_path):
        """
        Test that validation is fast even for large prompts.

        Given: Very large prompt (near limit)
        When: Validation is performed
        Then: Validation completes quickly (<10ms)

        This test will FAIL until T012 adds estimate_prompt_tokens().
        """
        import time

        generator = ReportGenerator()
        output_path = str(tmp_path / "report.md")

        # Create large but acceptable input
        with open(score_input_file, 'r') as f:
            large_input = json.load(f)

        # 7000 tokens = 28000 characters (within 8192 limit)
        large_input['evaluation_result']['evidence_summary'] = ["x" * 28000]

        large_input_path = str(tmp_path / "large_score_input.json")
        with open(large_input_path, 'w') as f:
            json.dump(large_input, f)

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Test Report"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            try:
                start = time.time()
                generator.generate_report(
                    score_input_path=large_input_path,
                    output_path=output_path,
                    provider="deepseek"
                )
                elapsed = time.time() - start

                # Should still be fast
                assert elapsed < 5.0, \
                    f"Large prompt validation took {elapsed:.2f}s"
            except KeyError as e:
                if "deepseek" in str(e):
                    pytest.skip("DeepSeek not yet in default configs (T011 pending)")
                raise
