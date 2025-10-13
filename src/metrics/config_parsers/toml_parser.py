"""TOML parser for Python test framework and coverage configurations.

This module provides functions to verify the presence of required sections
in Python configuration files (pyproject.toml, pytest.ini, .coveragerc).

Constitutional Compliance:
- Principle II (KISS): Fail-fast on parsing errors, no complex recovery logic
- Principle III (Transparency): Clear return values and error messages
"""

from pathlib import Path

import tomli


def verify_pytest_section(file_path: Path) -> tuple[bool, str]:
    """Verify that pyproject.toml contains [tool.pytest] section (FR-005).

    Args:
        file_path: Path to pyproject.toml or pytest.ini file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if required section present, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_pytest_section(Path("pyproject.toml"))
        (True, "Found [tool.pytest] section in pyproject.toml")

    Note:
        - pytest.ini files are accepted if they exist (any content)
        - pyproject.toml requires [tool.pytest] section presence
        - Malformed TOML returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # pytest.ini files are valid if they exist (any content per FR-005)
    if file_path.name == "pytest.ini":
        return True, f"Found pytest.ini configuration file"

    # For pyproject.toml, must verify [tool.pytest] section
    if file_path.name == "pyproject.toml":
        try:
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            # Check for [tool.pytest] or [tool.pytest.ini_options]
            if "tool" in data and "pytest" in data["tool"]:
                return True, "Found [tool.pytest] section in pyproject.toml"
            else:
                return False, "Missing [tool.pytest] section in pyproject.toml"

        except tomli.TOMLDecodeError as e:
            # Fail-fast on parsing errors (KISS principle)
            return False, f"TOML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    # tox.ini files are valid if they exist (any content per FR-005)
    if file_path.name == "tox.ini":
        return True, f"Found tox.ini configuration file"

    return False, f"Unexpected file type: {file_path.name}"


def verify_coverage_section(file_path: Path) -> tuple[bool, str]:
    """Verify that pyproject.toml or .coveragerc contains coverage config (FR-006).

    Args:
        file_path: Path to pyproject.toml or .coveragerc file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if required section present, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_coverage_section(Path("pyproject.toml"))
        (True, "Found [tool.coverage] section in pyproject.toml")

    Note:
        - .coveragerc files are accepted if they exist (any content)
        - pyproject.toml requires [tool.coverage] section presence
        - Malformed TOML returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # .coveragerc files are valid if they exist (any content per FR-006)
    if file_path.name == ".coveragerc":
        return True, f"Found .coveragerc configuration file"

    # For pyproject.toml, must verify [tool.coverage] section
    if file_path.name == "pyproject.toml":
        try:
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            # Check for [tool.coverage]
            if "tool" in data and "coverage" in data["tool"]:
                return True, "Found [tool.coverage] section in pyproject.toml"
            else:
                return False, "Missing [tool.coverage] section in pyproject.toml"

        except tomli.TOMLDecodeError as e:
            # Fail-fast on parsing errors (KISS principle)
            return False, f"TOML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    return False, f"Unexpected file type: {file_path.name}"
