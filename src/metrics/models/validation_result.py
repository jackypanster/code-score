"""Validation result dataclass for individual tool validation outcomes.

This module defines the ValidationResult mutable dataclass that captures
the outcome of validating a single tool per data-model.md.
"""

from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validating a single tool's availability and compatibility.

    This mutable dataclass captures all relevant information from validating
    whether a required tool is present, executable, and meets version requirements.

    Attributes:
        tool_name: Name of the validated tool (e.g., "ruff", "npm")
        found: Whether tool was found in PATH via shutil.which()
        path: Absolute path to tool executable (if found)
        version: Detected version string (if retrievable, e.g., "0.1.8")
        version_ok: Whether version meets minimum requirement (True by default if no requirement)
        permissions: File permission string in Unix format (e.g., "-rw-r--r--") if permission error
        error_category: Classification of validation error:
                       - "missing": Tool not found via shutil.which()
                       - "outdated": Tool found but version < minimum
                       - "permission": Tool found but not executable
                       - "other": Version check failed or unexpected error
                       - None: No error (successful validation)
        error_details: Human-readable error explanation (formatted Chinese message)

    Error Categories (FR-017):
        The error_category field enables grouping of validation errors:
        - missing: Tools not found in PATH
        - outdated: Tools with insufficient versions
        - permission: Tools that exist but aren't executable
        - other: Miscellaneous validation failures

    Examples:
        >>> # Successful validation
        >>> ValidationResult(
        ...     tool_name="ruff",
        ...     found=True,
        ...     path="/usr/bin/ruff",
        ...     version="0.1.8",
        ...     version_ok=True
        ... )

        >>> # Missing tool
        >>> ValidationResult(
        ...     tool_name="pytest",
        ...     found=False,
        ...     error_category="missing",
        ...     error_details="Tool not found in PATH"
        ... )

        >>> # Outdated version
        >>> ValidationResult(
        ...     tool_name="npm",
        ...     found=True,
        ...     path="/usr/local/bin/npm",
        ...     version="7.5.0",
        ...     version_ok=False,
        ...     error_category="outdated",
        ...     error_details="Current: 7.5.0, Minimum: 8.0.0"
        ... )

        >>> # Permission error
        >>> ValidationResult(
        ...     tool_name="ruff",
        ...     found=True,
        ...     path="/usr/bin/ruff",
        ...     permissions="-rw-r--r--",
        ...     version_ok=False,
        ...     error_category="permission",
        ...     error_details="Tool exists but is not executable"
        ... )

    Raises:
        ValueError: If error_category is not in the valid enum set
    """

    tool_name: str
    found: bool
    path: str | None = None
    version: str | None = None
    version_ok: bool = True  # True by default (no version requirement means any version is OK)
    permissions: str | None = None
    error_category: str | None = None  # "missing" | "outdated" | "permission" | "other" | None
    error_details: str | None = None

    def __post_init__(self):
        """Validate error_category enum after dataclass initialization.

        Raises:
            ValueError: If error_category is not in the valid set
        """
        valid_error_categories = {"missing", "outdated", "permission", "other"}
        if self.error_category is not None and self.error_category not in valid_error_categories:
            raise ValueError(
                f"Invalid error_category: {self.error_category}. "
                f"Must be one of {sorted(valid_error_categories)} or None"
            )

    def is_valid(self) -> bool:
        """Check if tool passed all validation checks.

        A tool is considered valid if:
        1. It was found in the system PATH
        2. Its version meets minimum requirements (or no version requirement exists)
        3. No error category was assigned

        Returns:
            bool: True if tool passed validation, False otherwise

        Examples:
            >>> # Valid tool
            >>> result = ValidationResult(tool_name="ruff", found=True, version_ok=True)
            >>> result.is_valid()
            True

            >>> # Invalid tool (missing)
            >>> result = ValidationResult(tool_name="pytest", found=False, error_category="missing")
            >>> result.is_valid()
            False

            >>> # Invalid tool (version problem)
            >>> result = ValidationResult(tool_name="npm", found=True, version_ok=False, error_category="outdated")
            >>> result.is_valid()
            False
        """
        return self.found and self.version_ok and self.error_category is None
