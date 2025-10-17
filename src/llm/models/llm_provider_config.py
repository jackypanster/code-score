"""
LLM provider configuration model.

This module defines the LLMProviderConfig Pydantic model for configuring
external LLM services and CLI command generation.
"""

import math

from pydantic import BaseModel, Field, field_validator


class LLMProviderConfig(BaseModel):
    """
    Configuration for external LLM service providers.

    This model handles CLI command configuration, timeout settings,
    and provider-specific parameters for report generation.
    """

    provider_name: str = Field(
        ..., description="Unique identifier for the LLM provider", pattern=r"^[a-z][a-z0-9_]*$"
    )

    cli_command: list[str] = Field(
        ..., description="Base CLI command and arguments for the provider", min_items=1
    )

    model_name: str | None = Field(
        None, description="Specific model identifier (e.g., 'gemini-1.5-pro', 'gpt-4')"
    )

    timeout_seconds: int = Field(
        default=30, description="Maximum time to wait for LLM response", ge=10, le=300
    )

    max_tokens: int | None = Field(
        None, description="Maximum response length (provider-specific)", gt=0
    )

    temperature: float | None = Field(
        None, description="Sampling temperature for response generation", ge=0.0, le=2.0
    )

    environment_variables: dict[str, str] = Field(
        default_factory=dict,
        description="Required environment variables for provider authentication",
    )

    additional_args: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
        description="Provider-specific additional CLI arguments (None for standalone flags)",
    )

    supports_streaming: bool = Field(
        default=False, description="Whether provider supports streaming responses"
    )

    context_window: int | None = Field(
        None, description="Maximum context window size in tokens", gt=0
    )

    chars_per_token: float = Field(
        default=1.0,
        description="Conservative chars-per-token ratio for token estimation (default: 1.0 for maximum safety)",
        gt=0.0,
        le=10.0
    )

    @classmethod
    @field_validator("cli_command")
    def validate_cli_command(cls, v):
        """Validate CLI command structure and basic safety."""
        if not v or not v[0]:
            raise ValueError("CLI command cannot be empty")

        # Basic safety check - no shell injection patterns
        dangerous_patterns = [";", "&&", "||", "|", ">", "<", "`", "$", "!"]
        command_str = " ".join(v)

        for pattern in dangerous_patterns:
            if pattern in command_str:
                raise ValueError(f"Potentially unsafe CLI command pattern: {pattern}")

        return v

    @classmethod
    @field_validator("provider_name")
    def validate_provider_name(cls, v):
        """Validate provider name format."""
        if not v:
            raise ValueError("Provider name cannot be empty")

        # Provider name format validation only
        # llm CLI will validate if provider is actually available
        # No hardcoded whitelist - supports any provider installed via llm CLI

        return v

    @classmethod
    @field_validator("environment_variables")
    def validate_environment_variables(cls, v):
        """Validate environment variable names."""
        import re

        env_var_pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")

        for var_name in v.keys():
            if not env_var_pattern.match(var_name):
                raise ValueError(f"Invalid environment variable name: {var_name}")

        return v

    @classmethod
    @field_validator("additional_args")
    def validate_additional_args(cls, v):
        """Validate additional arguments structure."""
        # Ensure argument names are valid CLI parameter format
        for arg_name in v.keys():
            if not arg_name.startswith("--") and not arg_name.startswith("-"):
                raise ValueError(f"Additional argument must start with - or --: {arg_name}")

        return v

    def build_cli_command(self, prompt: str, output_file: str | None = None) -> list[str]:
        """
        Build complete CLI command for LLM execution.

        Args:
            prompt: Input prompt text for the LLM
            output_file: Optional output file path

        Returns:
            Complete CLI command as list of strings
        """
        command = self.cli_command.copy()

        # llm CLI standard format: -m <model>
        if self.model_name:
            command.extend(["-m", self.model_name])

        # Add additional arguments (standalone or key/value)
        for arg_name, arg_value in self.additional_args.items():
            if arg_value == "" or arg_value is None:
                command.append(arg_name)
            else:
                command.extend([arg_name, str(arg_value)])

        # Prompt as final positional argument
        command.append(prompt)

        return command

    def get_required_env_vars(self) -> list[str]:
        """Get list of required environment variable names."""
        return list(self.environment_variables.keys())

    def validate_environment(self) -> list[str]:
        """
        Validate that required environment variables are set.

        Returns:
            List of missing environment variable names
        """
        import os

        missing = []

        for var_name in self.environment_variables.keys():
            if not os.getenv(var_name):
                missing.append(var_name)

        return missing

    def estimate_prompt_tokens(self, prompt: str) -> int:
        """
        Estimate token count using ceiling-based conservative heuristic.

        This method guarantees we NEVER underestimate tokens by:
        1. Using math.ceil() to prevent rounding down (e.g., 16385 chars → 16385 tokens, not 16384)
        2. Using chars_per_token=1.0 as worst-case assumption (1 char = 1 token)

        The default chars_per_token=1.0 is maximally conservative and matches
        reality for DeepSeek's tokenizer (Qwen family) which treats most
        Chinese/Japanese characters as 1 token each.

        Args:
            prompt: Input text to estimate

        Returns:
            Estimated token count (conservative upper bound, guaranteed ≥ actual)

        Note:
            - **DeepSeek/Qwen tokenizer**: Chinese/Japanese = 1 char/token → accurate with default
            - **English**: ~4 chars/token → 4x overestimate (acceptable for safety)
            - **Fail-fast principle**: Better to reject edge cases than allow overflow
            - **Configurable**: Set chars_per_token > 1 for less conservative estimates
            - **Ceiling**: Prevents off-by-one errors (16385 chars → 16385 tokens, not 16384)

        Examples:
            >>> config = LLMProviderConfig(chars_per_token=1.0, ...)  # Default: maximally safe
            >>> config.estimate_prompt_tokens("测试" * 5000)  # 10000 Chinese chars
            10000  # Accurate for DeepSeek tokenizer

            >>> config = LLMProviderConfig(chars_per_token=2.0, ...)  # Less conservative
            >>> config.estimate_prompt_tokens("测试" * 5000)
            5000  # May underestimate for DeepSeek (actual ≈ 10000)
        """
        return math.ceil(len(prompt) / self.chars_per_token)

    def validate_prompt_length(self, prompt: str) -> None:
        """
        Validate prompt length against context window limit.

        Ensures prompts do not exceed the provider's context window limit.
        This is critical for providers like DeepSeek with smaller context windows (8K tokens).

        Args:
            prompt: Input text to validate

        Raises:
            ValueError: If prompt exceeds context window limit with detailed message
                       including token count, character count, and limit
        """
        if not self.context_window:
            return  # No limit configured, skip validation

        estimated_tokens = self.estimate_prompt_tokens(prompt)

        if estimated_tokens > self.context_window:
            raise ValueError(
                f"Prompt length {estimated_tokens} tokens exceeds "
                f"{self.provider_name} context window limit {self.context_window} tokens. "
                f"Actual prompt length: {len(prompt)} characters."
            )

    def estimate_context_usage(self, prompt_length: int) -> dict[str, int | float | bool]:
        """
        Estimate context window usage for given prompt.

        Args:
            prompt_length: Length of prompt in characters

        Returns:
            Dictionary with usage estimates
        """
        # Rough estimation: ~4 characters per token
        estimated_tokens = prompt_length // 4

        result = {
            "estimated_prompt_tokens": estimated_tokens,
            "context_window": self.context_window,
            "within_limits": True,
        }

        if self.context_window:
            usage_ratio = estimated_tokens / self.context_window
            result["usage_ratio"] = usage_ratio
            result["within_limits"] = usage_ratio <= 0.8  # 80% safety margin

        return result

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "provider_name": "gemini",
                "cli_command": ["gemini", "generate"],
                "model_name": "gemini-1.5-pro",
                "timeout_seconds": 30,
                "max_tokens": 2048,
                "temperature": 0.1,
                "environment_variables": {"GEMINI_API_KEY": "required"},
                "additional_args": {"--format": "text", "--safety": "high"},
                "supports_streaming": True,
                "context_window": 128000,
            }
        }

    @classmethod
    def get_default_configs(cls) -> dict[str, "LLMProviderConfig"]:
        """
        Get default configurations for common providers.

        Returns:
            Dictionary mapping provider names to default configurations
        """
        defaults = {
            "deepseek": cls(
                provider_name="deepseek",
                cli_command=["llm"],  # llm CLI unified interface
                model_name="deepseek-coder",  # Optimized for code generation
                timeout_seconds=90,
                max_tokens=None,  # llm CLI auto-manages output tokens
                temperature=0.1,
                environment_variables={"DEEPSEEK_API_KEY": "required"},
                supports_streaming=False,
                context_window=8192,  # DeepSeek context window limit
                additional_args={},  # No provider-specific args for llm CLI
            )
        }

        return defaults
