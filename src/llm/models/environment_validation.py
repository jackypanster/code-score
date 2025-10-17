"""Environment validation results model for LLM provider prerequisites."""

from pydantic import BaseModel, Field


class EnvironmentValidation(BaseModel):
    """Environment validation results for LLM provider prerequisites."""

    llm_cli_available: bool = Field(
        ..., description="Whether llm CLI is found in PATH"
    )

    llm_cli_version: str | None = Field(
        None, description="Detected llm CLI version"
    )

    required_env_vars: dict[str, bool] = Field(
        default_factory=dict,
        description="Environment variable check results"
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation error messages"
    )

    def is_valid(self) -> bool:
        """Return True if all validation checks passed."""
        return (
            self.llm_cli_available
            and all(self.required_env_vars.values())
            and len(self.validation_errors) == 0
        )

    def get_error_summary(self) -> str:
        """Return formatted error summary for user display."""
        if self.is_valid():
            return "All prerequisites validated successfully."

        errors = []

        if not self.llm_cli_available:
            errors.append(
                "✗ llm CLI not found in PATH. "
                "Install: pip install llm"
            )

        missing_vars = [
            var for var, is_set in self.required_env_vars.items()
            if not is_set
        ]
        if missing_vars:
            errors.append(
                f"✗ Missing environment variables: {', '.join(missing_vars)}"
            )

        errors.extend(self.validation_errors)

        return "\n".join(errors)

    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = "forbid"
