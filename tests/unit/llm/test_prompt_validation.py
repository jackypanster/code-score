"""
Unit tests for LLMProviderConfig.validate_prompt_length() method.

This test validates the context window validation logic for prompt length checking.
The method will be added in T013 as part of the core implementation phase.

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T013 adds the validate_prompt_length() method.
"""

import pytest

from src.llm.models.llm_provider_config import LLMProviderConfig


class TestPromptLengthValidation:
    """Unit tests for prompt length validation against context window limits."""

    def test_validate_prompt_length_normal_prompt(self):
        """
        Verify normal prompts within context window are accepted.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # Using deepseek as default provider
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Normal prompt: 1000 chars ≈ 500 tokens (well within 8192 limit)
        prompt = "x" * 1000

        # Should not raise any exception
        config.validate_prompt_length(prompt)

    def test_validate_prompt_length_exceeds_context_window(self):
        """
        Verify prompts exceeding context window raise ValueError.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Large prompt: 20000 chars ≈ 10000 tokens (exceeds 8192 limit)
        huge_prompt = "x" * 20000

        with pytest.raises(ValueError, match="exceeds.*8192"):
            config.validate_prompt_length(huge_prompt)

    def test_validate_prompt_length_error_message_content(self):
        """
        Verify error message includes token count, char count, and limit.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        huge_prompt = "x" * 20000  # 40000 chars ≈ 10000 tokens

        with pytest.raises(ValueError) as exc_info:
            config.validate_prompt_length(huge_prompt)

        error = str(exc_info.value)

        # Error message should include all relevant information
        assert "10000 tokens" in error, "Should show estimated token count"
        assert "8192" in error, "Should show context window limit"
        assert "20000 characters" in error, "Should show actual character count"

    def test_validate_prompt_length_empty_prompt(self):
        """
        Verify empty prompt is accepted (0 tokens < any limit).

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Empty prompt should be valid
        config.validate_prompt_length("")

    def test_validate_prompt_length_at_boundary(self):
        """
        Verify prompts at exactly the context window boundary.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Exactly 8192 tokens = 16384 characters
        boundary_prompt = "x" * 16384

        # Should not raise (8192 tokens == 8192 limit)
        config.validate_prompt_length(boundary_prompt)

    def test_validate_prompt_length_one_over_boundary(self):
        """
        Verify prompts just over the context window are rejected.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # 8193 tokens = 16386 characters (1 token over limit)
        over_boundary_prompt = "x" * 16386

        with pytest.raises(ValueError, match="exceeds"):
            config.validate_prompt_length(over_boundary_prompt)

    def test_validate_prompt_length_without_context_window(self):
        """
        Verify validation is skipped when context_window is None.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=None  # No context window set
        )

        # Even huge prompts should pass without context_window
        huge_prompt = "x" * 100000

        # Should not raise (no limit to validate against)
        config.validate_prompt_length(huge_prompt)

    def test_validate_prompt_length_small_context_window(self):
        """
        Verify validation works with small context windows.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=128  # Very small context window
        )

        # 100 chars ≈ 50 tokens (within 128 limit)
        small_prompt = "x" * 100
        config.validate_prompt_length(small_prompt)

        # 1000 chars ≈ 500 tokens (exceeds 128 limit)
        large_prompt = "x" * 1000
        with pytest.raises(ValueError):
            config.validate_prompt_length(large_prompt)

    def test_validate_prompt_length_large_context_window(self):
        """
        Verify validation works with large context windows (large context window).

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=1048576  # Large 1M token context window
        )

        # Very large prompt: 100000 chars ≈ 50000 tokens (well within 1M limit)
        large_prompt = "x" * 100000
        config.validate_prompt_length(large_prompt)

        # Extremely large prompt: 5000000 chars ≈ 2500000 tokens (exceeds 1M)
        extremely_large_prompt = "x" * 5000000
        with pytest.raises(ValueError):
            config.validate_prompt_length(extremely_large_prompt)


class TestPromptLengthValidationErrorMessages:
    """Tests for error message format and content."""

    def test_error_message_includes_provider_name(self):
        """
        Verify error message includes provider name for context.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        huge_prompt = "x" * 20000

        with pytest.raises(ValueError) as exc_info:
            config.validate_prompt_length(huge_prompt)

        error = str(exc_info.value)
        assert "deepseek" in error.lower(), "Error should mention provider name"

    def test_error_message_readable_format(self):
        """
        Verify error message is human-readable and actionable.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        huge_prompt = "x" * 20000

        with pytest.raises(ValueError) as exc_info:
            config.validate_prompt_length(huge_prompt)

        error = str(exc_info.value)

        # Should be clear about what happened
        assert "exceeds" in error.lower() or "larger than" in error.lower(), \
            "Error should clearly indicate exceedance"

        # Should provide actionable information
        assert "tokens" in error.lower(), "Error should mention tokens"
        assert "8192" in error, "Error should show the limit"

    def test_error_message_different_limits(self):
        """
        Verify error messages show correct limits for different context windows.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        # Small context window (8192 tokens)
        small_window_config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="deepseek-coder",
            context_window=8192
        )

        # Large context window (1M tokens)
        large_window_config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model-large",
            context_window=1048576
        )

        huge_prompt = "x" * 20000  # 10000 tokens

        # Small window should reject (10000 > 8192)
        with pytest.raises(ValueError) as exc_info_small:
            small_window_config.validate_prompt_length(huge_prompt)
        assert "8192" in str(exc_info_small.value)

        # Large window should accept (10000 < 1048576)
        large_window_config.validate_prompt_length(huge_prompt)  # No exception


class TestPromptLengthValidationIntegration:
    """Integration tests for prompt validation with other config properties."""

    def test_validate_prompt_length_uses_estimate_prompt_tokens(self):
        """
        Verify validation uses estimate_prompt_tokens() for counting.

        This test will FAIL until both T012 (estimate_prompt_tokens) and
        T013 (validate_prompt_length) are implemented.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # This test verifies the integration between the two methods
        # validate_prompt_length should call estimate_prompt_tokens internally

        prompt = "x" * 20000  # 10000 tokens

        # Manual calculation
        estimated_tokens = config.estimate_prompt_tokens(prompt)
        assert estimated_tokens == 10000

        # Validation should use the same estimation
        with pytest.raises(ValueError) as exc_info:
            config.validate_prompt_length(prompt)

        error = str(exc_info.value)
        assert "10000" in error, "Error should show the estimated token count"

    def test_validate_prompt_length_consistency(self):
        """
        Verify multiple validations of same prompt give consistent results.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        prompt = "x" * 1000  # 250 tokens, within limit

        # Multiple validations should all pass
        for _ in range(10):
            config.validate_prompt_length(prompt)

        # Multiple validations of over-limit prompt should all fail
        huge_prompt = "x" * 20000  # 10000 tokens, over limit

        for _ in range(10):
            with pytest.raises(ValueError):
                config.validate_prompt_length(huge_prompt)

    def test_validate_prompt_length_with_real_content(self):
        """
        Verify validation works with realistic prompt content.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Realistic prompt with mixed content
        realistic_prompt = """
        # Repository Analysis Request

        **Project**: code-score
        **Language**: Python
        **Metrics**:
        - Linting: 42 issues
        - Tests: 156 passing
        - Coverage: 87%

        ```python
        def calculate_score(metrics):
            weights = {
                'code_quality': 0.4,
                'testing': 0.35,
                'documentation': 0.25
            }
            return sum(
                metrics[key] * weight
                for key, weight in weights.items()
            )
        ```

        Please analyze this code and provide recommendations for improvement.
        """

        # Realistic prompt should be accepted (much smaller than 8192 tokens)
        config.validate_prompt_length(realistic_prompt)


class TestPromptLengthValidationEdgeCases:
    """Edge case tests for prompt length validation."""

    def test_validate_prompt_length_unicode_characters(self):
        """
        Verify validation handles Unicode characters correctly.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Unicode text (emojis, Chinese characters)
        unicode_prompt = "Hello 👋 世界 🌍 Testing 🧪 " * 100

        # Python's len() counts Unicode correctly
        estimated_tokens = config.estimate_prompt_tokens(unicode_prompt)

        # If estimated tokens < 8192, should pass
        if estimated_tokens < 8192:
            config.validate_prompt_length(unicode_prompt)
        else:
            with pytest.raises(ValueError):
                config.validate_prompt_length(unicode_prompt)

    def test_validate_prompt_length_whitespace_only(self):
        """
        Verify validation handles whitespace-only prompts.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Large whitespace-only prompt
        whitespace_prompt = " " * 1000  # 250 tokens

        # Should be accepted (within limit)
        config.validate_prompt_length(whitespace_prompt)

    def test_validate_prompt_length_special_characters(self):
        """
        Verify validation handles special characters.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Special characters
        special_prompt = "!@#$%^&*()_+-=[]{}|;:',.<>?/" * 100

        # Should validate based on character count, not content
        config.validate_prompt_length(special_prompt)

    def test_validate_prompt_length_newlines_and_tabs(self):
        """
        Verify validation counts newlines and tabs as characters.

        This test will FAIL until T013 adds validate_prompt_length() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Prompt with many newlines and tabs
        formatted_prompt = "Line 1\n\tIndented line\n\t\tDouble indented\n" * 100

        # Should count all characters including whitespace
        estimated_tokens = config.estimate_prompt_tokens(formatted_prompt)

        # Validation should use the same counting logic
        if estimated_tokens < 8192:
            config.validate_prompt_length(formatted_prompt)
        else:
            with pytest.raises(ValueError):
                config.validate_prompt_length(formatted_prompt)
