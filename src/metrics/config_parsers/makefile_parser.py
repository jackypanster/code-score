"""Makefile parser for Go coverage configuration detection.

This module provides functions to verify the presence of coverage-related
flags or keywords in Makefile (e.g., -cover, coverage).

Constitutional Compliance:
- Principle II (KISS): Simple text search, no make parsing
- Principle III (Transparency): Clear return values and error messages
"""

from pathlib import Path


def verify_coverage_flags(file_path: Path) -> tuple[bool, str]:
    """Verify that Makefile contains coverage-related flags (FR-006).

    Args:
        file_path: Path to Makefile

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if coverage flags/keywords found, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_coverage_flags(Path("Makefile"))
        (True, "Found coverage flags in Makefile")

    Note:
        - Searches for: -cover, -coverprofile, coverage keyword
        - Simple text search, no make syntax parsing
        - Case-sensitive search
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for coverage-related flags and keywords
        coverage_indicators = [
            "-cover",  # Go test flag
            "-coverprofile",  # Coverage output flag
            "coverage",  # Coverage target or keyword
        ]

        found_indicators = [indicator for indicator in coverage_indicators if indicator in content]

        if found_indicators:
            indicators_str = ", ".join(found_indicators)
            return True, f"Found coverage flags in Makefile: {indicators_str}"
        else:
            return False, "No coverage references found in Makefile"

    except Exception as e:
        return False, f"Error reading file: {str(e)}"
