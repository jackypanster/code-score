"""Tool requirement dataclass for toolchain validation.

This module defines the ToolRequirement frozen dataclass that specifies
required CLI tools with their validation criteria per data-model.md.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolRequirement:
    """Specification for a required analysis tool.

    This frozen dataclass defines the validation criteria for a CLI tool
    required by the code analysis system. All tool requirements are immutable
    and defined at module load time.

    Attributes:
        name: CLI command name (e.g., "ruff", "npm", "go")
        language: Target language or "global" for all repositories
                 Valid values: "python", "javascript", "typescript", "java", "go", "global"
        category: Tool purpose category
                 Valid values: "lint", "test", "security", "build"
        doc_url: Official documentation URL for error messages (must be HTTP/HTTPS)
        min_version: Optional minimum version requirement in semver format (e.g., "0.1.0")
        version_command: CLI flag to get version (default: "--version")

    Examples:
        >>> # Python linter
        >>> ToolRequirement(
        ...     name="ruff",
        ...     language="python",
        ...     category="lint",
        ...     doc_url="https://docs.astral.sh/ruff",
        ...     min_version="0.1.0",
        ...     version_command="--version"
        ... )

        >>> # Global tool (no version requirement)
        >>> ToolRequirement(
        ...     name="git",
        ...     language="global",
        ...     category="build",
        ...     doc_url="https://git-scm.com/doc",
        ...     min_version=None
        ... )

        >>> # Go tool with custom version command
        >>> ToolRequirement(
        ...     name="go",
        ...     language="go",
        ...     category="build",
        ...     doc_url="https://go.dev/doc/",
        ...     min_version="1.19.0",
        ...     version_command="version"  # Go uses "go version" not "go --version"
        ... )

    Raises:
        ValueError: If any field validation fails in __post_init__
    """

    name: str
    language: str
    category: str
    doc_url: str
    min_version: str | None = None
    version_command: str = "--version"

    def __post_init__(self):
        """Validate field constraints after dataclass initialization.

        This method enforces enum constraints and format validation for all fields.
        Since this is a frozen dataclass, we cannot modify fields after creation,
        so validation must raise exceptions for invalid inputs.

        Raises:
            ValueError: If any field fails validation
        """
        # Validate name is non-empty
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Tool name cannot be empty")

        # Validate language enum
        valid_languages = {"python", "javascript", "typescript", "java", "go", "global"}
        if self.language not in valid_languages:
            raise ValueError(
                f"Invalid language: {self.language}. "
                f"Must be one of {sorted(valid_languages)}"
            )

        # Validate category enum
        valid_categories = {"lint", "test", "security", "build"}
        if self.category not in valid_categories:
            raise ValueError(
                f"Invalid category: {self.category}. "
                f"Must be one of {sorted(valid_categories)}"
            )

        # Validate doc_url is HTTP/HTTPS
        if not self.doc_url or not self.doc_url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid doc_url: {self.doc_url}. "
                f"Must be a valid HTTP/HTTPS URL"
            )

        # Validate version_command is non-empty
        if not self.version_command or not isinstance(self.version_command, str):
            raise ValueError("version_command cannot be empty")

        # min_version can be None or a string (validation happens in ToolDetector)
        if self.min_version is not None and not isinstance(self.min_version, str):
            raise ValueError("min_version must be None or a string")
