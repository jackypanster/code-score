"""
Unit tests for LLMProviderConfig.estimate_prompt_tokens() method.

This test validates the ceiling-based conservative heuristic with chars_per_token=1.0.
The method will be added in T012 as part of the core implementation phase.

These tests are written BEFORE implementation as part of TDD workflow.
They will FAIL until T012 adds the estimate_prompt_tokens() method.
"""

import math
import time

import pytest

from src.llm.models.llm_provider_config import LLMProviderConfig


class TestTokenEstimation:
    """Unit tests for token estimation heuristic."""

    def test_estimate_prompt_tokens_english_text(self):
        """
        Verify 4 chars ≈ 1 token for English text.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",  # Using deepseek as default provider
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # With chars_per_token=1.0: 4 chars = 4 tokens
        assert config.estimate_prompt_tokens("1234") == 4, \
            "4 characters should equal 4 tokens (ceil(4/1.0)=4)"

        # 1000 characters = 250 tokens
        assert config.estimate_prompt_tokens("x" * 1000) == 1000, \
            "1000 characters should equal 1000 tokens (ceil(1000/1.0)=1000)"

        # 8 characters = 2 tokens
        assert config.estimate_prompt_tokens("12345678") == 8, \
            "8 characters should equal 8 tokens (ceil(8/1.0)=8)"

    def test_estimate_prompt_tokens_empty_string(self):
        """
        Verify empty string returns 0 tokens.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        assert config.estimate_prompt_tokens("") == 0, \
            "Empty string should equal 0 tokens"

    def test_estimate_prompt_tokens_small_strings(self):
        """
        Verify token estimation for strings smaller than 4 characters.

        Expected behavior: len(prompt) // 4 (integer division)
        - 1 char = 0 tokens
        - 2 chars = 0 tokens
        - 3 chars = 0 tokens
        - 4 chars = 1 token

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        assert config.estimate_prompt_tokens("a") == 1, "1 char = 1 token (ceil(1/1.0)=1)"
        assert config.estimate_prompt_tokens("ab") == 2, "2 chars = 2 tokens (ceil(2/1.0)=2)"
        assert config.estimate_prompt_tokens("abc") == 3, "3 chars = 3 tokens (ceil(3/1.0)=3)"
        assert config.estimate_prompt_tokens("abcd") == 4, "4 chars = 4 tokens (ceil(4/1.0)=4)"

    def test_estimate_prompt_tokens_large_prompts(self):
        """
        Verify token estimation for large prompts (close to context window limits).

        DeepSeek context window: 8192 tokens = 8192 characters (with chars_per_token=1.0)
        DeepSeek context window: 1048576 tokens = 1048576 characters (with chars_per_token=1.0)

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # 8000 tokens (close to DeepSeek limit)
        prompt_8000_tokens = "x" * 8000
        assert config.estimate_prompt_tokens(prompt_8000_tokens) == 8000, \
            "8000 characters should equal 8000 tokens"

        # 10000 tokens (exceeds DeepSeek limit)
        prompt_10000_tokens = "x" * 10000
        assert config.estimate_prompt_tokens(prompt_10000_tokens) == 10000, \
            "10000 characters should equal 10000 tokens"

    def test_estimate_prompt_tokens_chinese_text(self):
        """
        Verify token estimation for Chinese text.

        Note: Chinese text typically uses ~2 chars/token (not 4),
        but this heuristic uses 4 chars/token for simplicity.
        Accuracy: ±10% is acceptable per research.md.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Chinese text example (16 characters)
        chinese_text = "这是一个测试提示这是一个测试提示"  # 16 chars
        estimated = config.estimate_prompt_tokens(chinese_text)

        # With chars_per_token=1.0: ceil(16 / 1.0) = 16 tokens
        # Actual for DeepSeek tokenizer (Qwen) is ~16 tokens (1 char/token) - now accurate!
        # Conservative heuristic matches DeepSeek/Qwen tokenizer (1 char=1 token for CJK)
        assert estimated == 16, \
            "16 Chinese characters should estimate 16 tokens (accurate for DeepSeek/Qwen)"

    def test_estimate_prompt_tokens_mixed_content(self):
        """
        Verify token estimation for mixed content (code, markdown, etc.).

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Realistic prompt with mixed content
        mixed_prompt = """
        # Repository Analysis

        **Project**: code-score
        **Language**: Python

        ```python
        def calculate_score(metrics):
            return sum(metrics.values())
        ```

        Please analyze this code and provide recommendations.
        """

        estimated = config.estimate_prompt_tokens(mixed_prompt)
        actual_length = len(mixed_prompt)
        expected = math.ceil(actual_length / 1.0)  # With chars_per_token=1.0

        assert estimated == expected, \
            f"Mixed content {actual_length} chars should equal {expected} tokens"

    def test_estimate_prompt_tokens_performance(self):
        """
        Verify token estimation performance is <0.1ms per call.

        Performance requirement: <10ms for typical usage (1000 calls should be <100ms)

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Warm-up call
        config.estimate_prompt_tokens("warmup")

        # Performance test: 1000 calls
        prompt = "x" * 1000
        start = time.time()

        for _ in range(1000):
            config.estimate_prompt_tokens(prompt)

        elapsed = time.time() - start

        # Requirement: <100ms for 1000 calls (<0.1ms per call)
        assert elapsed < 0.1, \
            f"1000 token estimations took {elapsed*1000:.2f}ms (should be <100ms)"

    def test_estimate_prompt_tokens_consistency(self):
        """
        Verify token estimation is deterministic and consistent.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        prompt = "This is a test prompt for consistency validation"

        # Call multiple times
        results = [config.estimate_prompt_tokens(prompt) for _ in range(10)]

        # All results should be identical
        assert len(set(results)) == 1, \
            "Token estimation should be deterministic"

        # Verify expected value
        expected = math.ceil(len(prompt) / 1.0)
        assert results[0] == expected, \
            f"Expected {expected} tokens, got {results[0]}"

    def test_estimate_prompt_tokens_without_context_window(self):
        """
        Verify token estimation works even without context_window set.

        The method should work for estimation purposes regardless of context_window.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=None  # No context window set
        )

        # Should still estimate tokens
        prompt = "x" * 1000
        estimated = config.estimate_prompt_tokens(prompt)

        assert estimated == 1000, \
            "Token estimation should work without context_window set (1000 tokens)"

    def test_estimate_prompt_tokens_unicode_characters(self):
        """
        Verify token estimation handles Unicode characters correctly.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Unicode characters (emojis, special symbols)
        unicode_text = "Hello 👋 World 🌍 Testing 🧪 123"
        estimated = config.estimate_prompt_tokens(unicode_text)

        # Python's len() counts Unicode code points correctly
        expected = math.ceil(len(unicode_text) / 1.0)

        assert estimated == expected, \
            f"Unicode text {len(unicode_text)} chars should equal {expected} tokens"


class TestTokenEstimationEdgeCases:
    """Edge case tests for token estimation."""

    def test_estimate_prompt_tokens_whitespace_only(self):
        """
        Verify token estimation for whitespace-only strings.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        # Various whitespace patterns
        spaces = "    "  # 4 spaces
        tabs = "\t\t\t\t"  # 4 tabs
        newlines = "\n\n\n\n"  # 4 newlines
        mixed = "  \t\n"  # 4 mixed whitespace

        assert config.estimate_prompt_tokens(spaces) == 4, "4 spaces = 4 tokens"
        assert config.estimate_prompt_tokens(tabs) == 4, "4 tabs = 4 tokens"
        assert config.estimate_prompt_tokens(newlines) == 4, "4 newlines = 4 tokens"
        assert config.estimate_prompt_tokens(mixed) == 4, "4 mixed whitespace = 4 tokens"

    def test_estimate_prompt_tokens_special_characters(self):
        """
        Verify token estimation for special characters and symbols.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=8192
        )

        special = "!@#$%^&*()_+-=[]{}|;:',.<>?/"  # Actually 28 chars
        estimated = config.estimate_prompt_tokens(special)

        assert estimated == 28, \
            "28 special characters should equal 28 tokens"

    def test_estimate_prompt_tokens_very_long_string(self):
        """
        Verify token estimation for very long strings (stress test).

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        config = LLMProviderConfig(
            provider_name="deepseek",
            cli_command=["llm"],
            model_name="test-model",
            context_window=1048576  # Large context window
        )

        # Very long string (100,000 characters = 100,000 tokens)
        very_long = "x" * 100000
        estimated = config.estimate_prompt_tokens(very_long)

        assert estimated == 100000, \
            "100000 characters should equal 100000 tokens"

        # Verify performance is still acceptable for large strings
        start = time.time()
        config.estimate_prompt_tokens(very_long)
        elapsed = time.time() - start

        assert elapsed < 0.001, \
            f"Large string estimation took {elapsed*1000:.2f}ms (should be <1ms)"


class TestTokenEstimationIntegration:
    """Integration tests for token estimation with other config properties."""

    def test_estimate_prompt_tokens_with_different_providers(self):
        """
        Verify token estimation is provider-agnostic.

        The 4 chars/token heuristic should work the same regardless of provider.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        providers = [
            ("deepseek", 8192),
            # Additional providers can be added as needed
            # ("openai", 128000),
            # ("anthropic", 200000)
        ]

        prompt = "x" * 1000

        for provider_name, context_window in providers:
            config = LLMProviderConfig(
                provider_name=provider_name,
                cli_command=["llm"],
                model_name=f"{provider_name}-model",
                context_window=context_window
            )

            estimated = config.estimate_prompt_tokens(prompt)

            assert estimated == 1000, \
                f"Token estimation for {provider_name} should be 1000 tokens"

    def test_estimate_prompt_tokens_relationship_with_context_window(self):
        """
        Verify token estimation is independent of context_window value.

        The estimation logic should not depend on context_window size.

        This test will FAIL until T012 adds estimate_prompt_tokens() method.
        """
        prompt = "x" * 1000  # 1000 tokens

        # Different context windows
        configs = [
            LLMProviderConfig(
                provider_name="deepseek",
                cli_command=["llm"],
                model_name="test",
                context_window=1024
            ),
            LLMProviderConfig(
                provider_name="deepseek",
                cli_command=["llm"],
                model_name="test",
                context_window=8192
            ),
            LLMProviderConfig(
                provider_name="deepseek",
                cli_command=["llm"],
                model_name="test",
                context_window=1048576
            ),
        ]

        estimates = [config.estimate_prompt_tokens(prompt) for config in configs]

        # All should return the same estimate
        assert len(set(estimates)) == 1, \
            "Token estimation should be independent of context_window"
        assert estimates[0] == 1000, \
            "All configs should estimate 1000 tokens"
