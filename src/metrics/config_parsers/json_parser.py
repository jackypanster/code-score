"""JSON parser for JavaScript test framework and coverage configurations.

This module provides functions to verify the presence of required keys
in JavaScript configuration files (package.json, jest.config.js).

Constitutional Compliance:
- Principle II (KISS): Fail-fast on parsing errors, simple key checks
- Principle III (Transparency): Clear return values and error messages
"""

import json
from pathlib import Path


def verify_test_script(file_path: Path) -> tuple[bool, str]:
    """Verify that package.json contains scripts.test key (FR-005).

    Args:
        file_path: Path to package.json file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if scripts.test key present, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_test_script(Path("package.json"))
        (True, "Found scripts.test in package.json")

    Note:
        - Must find scripts.test key specifically
        - jest.config.js files are accepted if they exist (FR-005)
        - Malformed JSON returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # jest.config.js files are valid if they exist (any content per FR-005)
    if file_path.name == "jest.config.js":
        return True, f"Found jest.config.js configuration file"

    # For package.json, must verify scripts.test key
    if file_path.name == "package.json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check for scripts.test key
            if "scripts" in data and "test" in data["scripts"]:
                return True, "Found scripts.test in package.json"
            else:
                return False, "Missing scripts.test key in package.json"

        except json.JSONDecodeError as e:
            # Fail-fast on parsing errors (KISS principle)
            return False, f"JSON parse error: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    return False, f"Unexpected file type: {file_path.name}"


def verify_coverage_threshold(file_path: Path) -> tuple[bool, str]:
    """Verify that jest config contains coverageThreshold key (FR-006).

    Args:
        file_path: Path to jest.config.json or jest.config.js file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if coverageThreshold key present, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_coverage_threshold(Path("jest.config.json"))
        (True, "Found coverageThreshold in jest.config.json")

    Note:
        - Must find coverageThreshold key specifically
        - Only works with .json files (not .js files with exports)
        - Malformed JSON returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # Only parse .json files (not .js files with module.exports)
    if file_path.suffix != ".json":
        # Fail-closed for .js files: cannot safely verify coverageThreshold without code execution
        # This prevents false positives (FR-006/FR-006a compliance)
        return False, f"Cannot parse {file_path.name} (JavaScript file requires AST parsing)"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check for coverageThreshold key
        if "coverageThreshold" in data:
            return True, f"Found coverageThreshold in {file_path.name}"
        else:
            return False, f"Missing coverageThreshold key in {file_path.name}"

    except json.JSONDecodeError as e:
        # Fail-fast on parsing errors (KISS principle)
        return False, f"JSON parse error: {str(e)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
