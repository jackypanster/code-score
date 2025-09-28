"""
LLM provider configuration model.

This module defines the LLMProviderConfig Pydantic model for configuring
external LLM services and CLI command generation.
"""

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

        allowed_providers = ["gemini"]

        if v not in allowed_providers:
            raise ValueError(
                f"Unsupported provider: {v}. Only Gemini is supported in this MVP version."
            )

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

        # Add model if specified (Gemini CLI expects --model)
        if self.model_name:
            command.extend(["--model", self.model_name])

        # Add additional arguments (standalone or key/value)
        for arg_name, arg_value in self.additional_args.items():
            if arg_value == "" or arg_value is None:
                command.append(arg_name)
            else:
                command.extend([arg_name, str(arg_value)])

        # Gemini CLI currently writes to stdout; higher layers capture the
        # output and persist it. Keep the prompt as a positional argument.
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

    def get_provider_specific_limits(self) -> dict[str, int | None]:
        """Get Gemini-specific limits and capabilities."""
        # Only Gemini is supported in current MVP
        if self.provider_name == "gemini":
            return {
                "context_window": self.context_window or 1048576,
                "max_output_tokens": self.max_tokens or 60000,
                "default_temperature": self.temperature if self.temperature is not None else 0.1,
            }
        return {}

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
            "gemini": cls(
                provider_name="gemini",
                cli_command=["gemini"],
                model_name="gemini-2.5-pro",
                timeout_seconds=90,
                max_tokens=60000,
                temperature=0.1,
                environment_variables={"GEMINI_API_KEY": "required"},
                supports_streaming=True,
                context_window=1048576,
                # Critical: --approval-mode yolo enables non-interactive execution
                # --debug provides detailed execution information for troubleshooting
                additional_args={"--approval-mode": "yolo", "--debug": None},
            )
        }

        return defaults
