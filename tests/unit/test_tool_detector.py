"""Unit tests for ToolDetector class.

This module tests the low-level tool detection, version checking, and
permission validation functions with mocked system calls.

Test Strategy:
- Mock all system interactions (shutil.which, subprocess, os.access, Path.stat)
- Test both success and failure paths
- Test edge cases (timeout, parsing errors, permissions)
- Aim for >90% code coverage
"""

import os
import stat
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.metrics.tool_detector import ToolDetector


class TestCheckAvailability:
    """Tests for ToolDetector.check_availability() method."""

    def test_tool_found_returns_path(self):
        """Test that check_availability returns path when tool exists."""
        detector = ToolDetector()

        with patch('shutil.which', return_value='/usr/bin/python3'):
            result = detector.check_availability('python3')

        assert result == '/usr/bin/python3'

    def test_tool_not_found_returns_none(self):
        """Test that check_availability returns None when tool doesn't exist."""
        detector = ToolDetector()

        with patch('shutil.which', return_value=None):
            result = detector.check_availability('nonexistent-tool')

        assert result is None

    def test_exception_handled_gracefully(self):
        """Test that exceptions in shutil.which are caught and None returned."""
        detector = ToolDetector()

        with patch('shutil.which', side_effect=OSError("System error")):
            result = detector.check_availability('python3')

        assert result is None

    def test_empty_tool_name(self):
        """Test that empty tool name is handled correctly."""
        detector = ToolDetector()

        with patch('shutil.which', return_value=None):
            result = detector.check_availability('')

        assert result is None


class TestGetVersion:
    """Tests for ToolDetector.get_version() method."""

    def test_version_from_stdout(self):
        """Test extracting version from stdout."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "Python 3.11.5"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_version('/usr/bin/python3', '--version')

        assert version == '3.11.5'

    def test_version_from_stderr(self):
        """Test extracting version from stderr (some tools output to stderr)."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "npm v8.19.2"

        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_version('/usr/bin/npm', '--version')

        assert version == '8.19.2'

    def test_version_with_v_prefix(self):
        """Test version parsing with 'v' prefix."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "v1.2.3"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_version('/usr/bin/tool', '--version')

        assert version == '1.2.3'  # 'v' prefix removed

    def test_version_two_components(self):
        """Test version parsing with only major.minor."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "version 2.7"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_version('/usr/bin/tool', '--version')

        assert version == '2.7'

    def test_timeout_returns_none(self):
        """Test that subprocess timeout returns None."""
        detector = ToolDetector()

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 0.5)):
            version = detector.get_version('/usr/bin/slow-tool', '--version')

        assert version is None

    def test_subprocess_error_returns_none(self):
        """Test that subprocess error returns None."""
        detector = ToolDetector()

        with patch('subprocess.run', side_effect=subprocess.SubprocessError("Process failed")):
            version = detector.get_version('/usr/bin/tool', '--version')

        assert version is None

    def test_file_not_found_returns_none(self):
        """Test that FileNotFoundError returns None."""
        detector = ToolDetector()

        with patch('subprocess.run', side_effect=FileNotFoundError("Tool not found")):
            version = detector.get_version('/nonexistent/tool', '--version')

        assert version is None

    def test_os_error_returns_none(self):
        """Test that OSError returns None."""
        detector = ToolDetector()

        with patch('subprocess.run', side_effect=OSError("OS error")):
            version = detector.get_version('/usr/bin/tool', '--version')

        assert version is None

    def test_unparseable_output_returns_none(self):
        """Test that output without version number returns None."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "No version information available"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_version('/usr/bin/tool', '--version')

        assert version is None

    def test_subprocess_call_timeout_value(self):
        """Test that subprocess is called with correct timeout."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "1.0.0"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            detector.get_version('/usr/bin/tool', '--version')

        # Verify timeout parameter
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['timeout'] == 3.0  # 3 seconds (accommodates JVM tools)

    def test_subprocess_captures_output(self):
        """Test that subprocess captures both stdout and stderr."""
        detector = ToolDetector()
        mock_result = Mock()
        mock_result.stdout = "1.0.0"
        mock_result.stderr = ""

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            detector.get_version('/usr/bin/tool', '--version')

        # Verify capture_output and text parameters
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['capture_output'] is True
        assert call_kwargs['text'] is True


class TestCompareVersions:
    """Tests for ToolDetector.compare_versions() method."""

    def test_exact_version_match(self):
        """Test that exact version match returns True."""
        detector = ToolDetector()

        result = detector.compare_versions('8.0.0', '8.0.0')

        assert result is True

    def test_current_greater_than_minimum(self):
        """Test that higher version returns True."""
        detector = ToolDetector()

        result = detector.compare_versions('8.1.0', '8.0.0')

        assert result is True

    def test_current_less_than_minimum(self):
        """Test that lower version returns False."""
        detector = ToolDetector()

        result = detector.compare_versions('7.5.0', '8.0.0')

        assert result is False

    def test_major_version_difference(self):
        """Test major version comparison."""
        detector = ToolDetector()

        assert detector.compare_versions('2.0.0', '1.9.9') is True
        assert detector.compare_versions('1.9.9', '2.0.0') is False

    def test_minor_version_difference(self):
        """Test minor version comparison."""
        detector = ToolDetector()

        assert detector.compare_versions('1.10.0', '1.9.0') is True
        assert detector.compare_versions('1.9.0', '1.10.0') is False

    def test_patch_version_difference(self):
        """Test patch version comparison."""
        detector = ToolDetector()

        assert detector.compare_versions('1.2.10', '1.2.9') is True
        assert detector.compare_versions('1.2.9', '1.2.10') is False

    def test_two_component_vs_three_component(self):
        """Test comparing 2-component vs 3-component versions."""
        detector = ToolDetector()

        # Python tuple comparison: (1, 2) < (1, 2, 0)
        assert detector.compare_versions('1.2.0', '1.2') is True
        assert detector.compare_versions('1.2', '1.1.9') is True

    def test_three_component_vs_two_component(self):
        """Test comparing 3-component vs 2-component versions."""
        detector = ToolDetector()

        assert detector.compare_versions('1.10', '1.9.5') is True

    def test_invalid_current_version_format(self):
        """Test that invalid current version returns False."""
        detector = ToolDetector()

        result = detector.compare_versions('invalid', '1.0.0')

        assert result is False

    def test_invalid_minimum_version_format(self):
        """Test that invalid minimum version returns False."""
        detector = ToolDetector()

        result = detector.compare_versions('1.0.0', 'invalid')

        assert result is False

    def test_non_numeric_version_components(self):
        """Test that non-numeric version components return False."""
        detector = ToolDetector()

        result = detector.compare_versions('1.2.abc', '1.2.0')

        assert result is False

    def test_empty_version_strings(self):
        """Test that empty version strings return False."""
        detector = ToolDetector()

        assert detector.compare_versions('', '1.0.0') is False
        assert detector.compare_versions('1.0.0', '') is False


class TestCheckPermissions:
    """Tests for ToolDetector.check_permissions() method."""

    def test_executable_file_with_permissions(self):
        """Test checking permissions on executable file."""
        detector = ToolDetector()

        # Mock os.path.exists to return True
        # Mock os.access to return True (executable)
        # Mock Path.stat to return file stats with execute permission
        mock_stat = Mock()
        mock_stat.st_mode = 0o100755  # -rwxr-xr-x

        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(Path, 'stat', return_value=mock_stat):
            has_exec, perms = detector.check_permissions('/usr/bin/python3')

        assert has_exec is True
        assert 'rwx' in perms or 'r-x' in perms  # Has execute bit

    def test_non_executable_file(self):
        """Test checking permissions on non-executable file."""
        detector = ToolDetector()

        mock_stat = Mock()
        mock_stat.st_mode = 0o100644  # -rw-r--r--

        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=False), \
             patch.object(Path, 'stat', return_value=mock_stat):
            has_exec, perms = detector.check_permissions('/usr/bin/tool')

        assert has_exec is False
        assert perms == '-rw-r--r--'

    def test_file_not_found(self):
        """Test checking permissions on non-existent file."""
        detector = ToolDetector()

        with patch('os.path.exists', return_value=False):
            has_exec, perms = detector.check_permissions('/nonexistent/tool')

        assert has_exec is False
        assert perms == 'file not found'

    def test_os_error_during_check(self):
        """Test that OSError is handled gracefully."""
        detector = ToolDetector()

        with patch('os.path.exists', return_value=True), \
             patch('os.access', side_effect=OSError("Access error")):
            has_exec, perms = detector.check_permissions('/usr/bin/tool')

        assert has_exec is False
        assert perms == 'permission denied'

    def test_permission_error_during_stat(self):
        """Test that PermissionError during stat is handled."""
        detector = ToolDetector()

        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(Path, 'stat', side_effect=PermissionError("Cannot stat")):
            has_exec, perms = detector.check_permissions('/usr/bin/tool')

        assert has_exec is False
        assert perms == 'permission denied'

    def test_unexpected_exception(self):
        """Test that unexpected exceptions are handled."""
        detector = ToolDetector()

        with patch('os.path.exists', return_value=True), \
             patch('os.access', side_effect=Exception("Unexpected error")):
            has_exec, perms = detector.check_permissions('/usr/bin/tool')

        assert has_exec is False
        assert perms == 'unknown error'

    def test_filemode_formatting(self):
        """Test that stat.filemode formats permissions correctly."""
        detector = ToolDetector()

        # Regular file with rwxr-xr-x permissions
        mock_stat = Mock()
        mock_stat.st_mode = 0o100755

        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(Path, 'stat', return_value=mock_stat):
            _, perms = detector.check_permissions('/usr/bin/tool')

        # stat.filemode should format as "-rwxr-xr-x"
        assert perms.startswith('-')
        assert len(perms) == 10  # Unix permission string is 10 chars


class TestVersionPattern:
    """Tests for ToolDetector.VERSION_PATTERN regex."""

    def test_pattern_matches_standard_semver(self):
        """Test that pattern matches standard semantic versions."""
        detector = ToolDetector()

        test_cases = [
            ("1.2.3", "1.2.3"),
            ("10.20.30", "10.20.30"),
            ("0.0.1", "0.0.1"),
        ]

        for input_str, expected in test_cases:
            match = detector.VERSION_PATTERN.search(input_str)
            assert match is not None
            assert match.group(1) == expected

    def test_pattern_matches_with_v_prefix(self):
        """Test that pattern matches versions with 'v' prefix."""
        detector = ToolDetector()

        match = detector.VERSION_PATTERN.search("v1.2.3")
        assert match is not None
        assert match.group(1) == "1.2.3"  # Without 'v'

    def test_pattern_matches_two_components(self):
        """Test that pattern matches 2-component versions."""
        detector = ToolDetector()

        match = detector.VERSION_PATTERN.search("Python 3.11")
        assert match is not None
        assert match.group(1) == "3.11"

    def test_pattern_extracts_from_mixed_text(self):
        """Test that pattern extracts version from mixed text."""
        detector = ToolDetector()

        test_cases = [
            "Python 3.11.5 (default, Sep 12 2023)",
            "npm v8.19.2",
            "ruff version 0.1.8",
            "go version go1.21.3 darwin/arm64",
        ]

        for text in test_cases:
            match = detector.VERSION_PATTERN.search(text)
            assert match is not None, f"Failed to match: {text}"


class TestTimeoutConstant:
    """Tests for ToolDetector.TIMEOUT_MS constant."""

    def test_timeout_value_is_3_seconds(self):
        """Test that timeout constant is set to 3 seconds to accommodate JVM tools."""
        detector = ToolDetector()

        assert detector.TIMEOUT_MS == 3.0  # 3 seconds (JVM tools like mvn/gradle need 1-2s)
