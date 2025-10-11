"""Tool detection functions for toolchain validation.

This module provides low-level functions for detecting CLI tools,
checking their versions, and validating file permissions.
"""

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path


class ToolDetector:
    """Low-level tool detection and validation functions.

    This class provides stateless utility methods for detecting tools,
    checking versions, and validating permissions. All methods handle
    errors gracefully and return None/False on failure rather than raising
    exceptions.

    Usage:
        detector = ToolDetector()
        path = detector.check_availability("python3")
        if path:
            version = detector.get_version(path, "--version")
            is_ok = detector.compare_versions(version, "3.11.0")
    """

    # Version regex pattern: matches "1.2.3", "v1.2.3", "1.2"
    VERSION_PATTERN = re.compile(r'v?(\d+\.\d+(?:\.\d+)?)')

    # Subprocess timeout: 3 seconds to accommodate JVM tools (mvn, gradle)
    # Lightweight tools (ruff, npm) respond in <100ms
    # JVM tools (mvn, gradle) need 1-2s to start JVM
    TIMEOUT_MS = 3.0

    def check_availability(self, tool_name: str) -> str | None:
        """Check if a tool is available in the system PATH.

        Uses `shutil.which()` to locate the tool (research decision #1).

        Args:
            tool_name: Name of the CLI tool (e.g., "ruff", "npm")

        Returns:
            Absolute path to the tool executable, or None if not found

        Examples:
            >>> detector = ToolDetector()
            >>> path = detector.check_availability("python3")
            >>> path is not None  # True if python3 installed
            True
            >>> detector.check_availability("nonexistent-tool")
            None
        """
        try:
            return shutil.which(tool_name)
        except Exception:
            # shutil.which() shouldn't raise, but catch just in case
            return None

    def get_version(self, tool_path: str, version_command: str) -> str | None:
        """Get version string from a tool by running it with version flag.

        Runs `tool_path version_command` and extracts version number using regex.
        Uses subprocess with timeout (research decision #2).

        Args:
            tool_path: Absolute path to tool executable
            version_command: CLI flag to get version (e.g., "--version", "version")

        Returns:
            Version string (e.g., "1.2.3"), or None if detection fails

        Examples:
            >>> detector = ToolDetector()
            >>> version = detector.get_version("/usr/bin/python3", "--version")
            >>> version is not None
            True
            >>> version = detector.get_version("/nonexistent/tool", "--version")
            >>> version is None
            True
        """
        try:
            # Run tool with version command
            result = subprocess.run(
                [tool_path, version_command],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_MS
            )

            # Check both stdout and stderr (some tools output to stderr)
            version_output = result.stdout + result.stderr

            # Extract version number using regex
            match = self.VERSION_PATTERN.search(version_output)
            if match:
                return match.group(1)  # Return version without 'v' prefix

            return None

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
            # Timeout, process error, or file not found -> return None
            return None
        except Exception:
            # Unexpected error -> return None (fail gracefully)
            return None

    def compare_versions(self, current: str, minimum: str) -> bool:
        """Compare two version strings using tuple comparison.

        Uses tuple comparison for semver (research decision #2).
        Handles versions with 2 or 3 components (e.g., "1.2" or "1.2.3").

        Args:
            current: Current installed version (e.g., "7.5.0")
            minimum: Minimum required version (e.g., "8.0.0")

        Returns:
            True if current >= minimum, False otherwise

        Examples:
            >>> detector = ToolDetector()
            >>> detector.compare_versions("8.1.0", "8.0.0")
            True
            >>> detector.compare_versions("7.5.0", "8.0.0")
            False
            >>> detector.compare_versions("1.2", "1.1.9")
            True
        """
        try:
            # Parse version strings into tuples of integers
            def parse_version(v: str) -> tuple[int, ...]:
                """Parse version string into tuple of integers."""
                parts = v.split(".")
                return tuple(int(p) for p in parts)

            current_tuple = parse_version(current)
            minimum_tuple = parse_version(minimum)

            # Tuple comparison handles different lengths automatically
            # (1, 2) < (1, 2, 0) is True in Python
            return current_tuple >= minimum_tuple

        except (ValueError, AttributeError):
            # Invalid version format -> assume outdated
            return False

    def check_permissions(self, tool_path: str) -> tuple[bool, str]:
        """Check if a tool has execute permissions.

        Uses `os.access(os.X_OK)` for permission check (research decision #4)
        and `stat.filemode()` for permission string formatting.

        Args:
            tool_path: Absolute path to tool executable

        Returns:
            Tuple of (has_execute_permission, permission_string)
            - has_execute_permission: True if tool is executable
            - permission_string: Unix-style permission string (e.g., "-rw-r--r--")

        Examples:
            >>> detector = ToolDetector()
            >>> has_exec, perms = detector.check_permissions("/usr/bin/python3")
            >>> has_exec
            True
            >>> perms.startswith("-rwx") or perms.startswith("-r-x")  # Executable
            True
        """
        try:
            # Check if path exists and is accessible
            if not os.path.exists(tool_path):
                return (False, "file not found")

            # Check execute permission using os.access()
            has_execute = os.access(tool_path, os.X_OK)

            # Get file permissions using stat.filemode()
            file_stat = Path(tool_path).stat()
            permission_string = stat.filemode(file_stat.st_mode)

            return (has_execute, permission_string)

        except (OSError, PermissionError):
            # File system error -> assume no permission
            return (False, "permission denied")
        except Exception:
            # Unexpected error -> assume no permission
            return (False, "unknown error")
