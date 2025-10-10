"""Build validation result data model."""

from typing import Optional

from pydantic import BaseModel, field_validator


class BuildValidationResult(BaseModel):
    """
    Structured result from build validation execution.

    This model represents the outcome of attempting to build a project,
    including success status, tool information, and diagnostic details.

    Fields:
        success: Build outcome - True (success), False (failure), None (tool unavailable)
        tool_used: Name of build tool executed ("uv", "npm", "go", "mvn", "gradle", "none")
        execution_time_seconds: Duration of build execution in seconds
        error_message: Error details if build failed (truncated to 1000 chars per NFR-002)
        exit_code: Process exit code from build tool

    Examples:
        >>> # Successful build
        >>> BuildValidationResult(
        ...     success=True,
        ...     tool_used="uv",
        ...     execution_time_seconds=3.14,
        ...     error_message=None,
        ...     exit_code=0
        ... )

        >>> # Failed build
        >>> BuildValidationResult(
        ...     success=False,
        ...     tool_used="npm",
        ...     execution_time_seconds=8.52,
        ...     error_message="Build failed: Module not found",
        ...     exit_code=1
        ... )

        >>> # Tool unavailable
        >>> BuildValidationResult(
        ...     success=None,
        ...     tool_used="none",
        ...     execution_time_seconds=0.0,
        ...     error_message="Maven not available in PATH",
        ...     exit_code=None
        ... )
    """

    success: Optional[bool]  # True=pass, False=fail, None=unavailable
    tool_used: str
    execution_time_seconds: float
    error_message: Optional[str] = None
    exit_code: Optional[int] = None

    @field_validator("error_message")
    @classmethod
    def truncate_error_message(cls, v: Optional[str]) -> Optional[str]:
        """
        Truncate error messages to 1000 characters per NFR-002.

        Long error messages are truncated to 997 characters plus "..." suffix
        to prevent output bloat while preserving diagnostic value.

        Args:
            v: Error message string or None

        Returns:
            Truncated error message if length > 1000, otherwise original value
        """
        if v and len(v) > 1000:
            return v[:997] + "..."
        return v

    @field_validator("execution_time_seconds")
    @classmethod
    def validate_execution_time(cls, v: float) -> float:
        """
        Ensure execution time is non-negative.

        Args:
            v: Execution time in seconds

        Returns:
            Validated execution time

        Raises:
            ValueError: If execution time is negative
        """
        if v < 0:
            raise ValueError("Execution time cannot be negative")
        return v

    @field_validator("tool_used")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """
        Validate tool_used is a known build tool name.

        Accepts standard build tools: uv, build, npm, yarn, go, mvn, gradle, none.
        Unknown tools are allowed (for extensibility) but not validated.

        Args:
            v: Tool name string

        Returns:
            Validated tool name
        """
        valid_tools = {"uv", "build", "npm", "yarn", "go", "mvn", "gradle", "none"}
        # Note: We don't raise an error for unknown tools to allow extensibility
        # Future build tools can be added without breaking existing code
        return v
