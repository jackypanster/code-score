"""Unit tests for ToolchainManager class.

This module tests the high-level toolchain validation orchestration logic
with mocked ToolDetector and tool registry.

Test Strategy:
- Mock ToolDetector to control validation outcomes
- Mock get_tools_for_language to control tool requirements
- Test error categorization (missing, outdated, permission, other)
- Test that global + language tools are both validated
- Test exception raising when validation fails
- Aim for >85% code coverage
"""

from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.metrics.error_handling import ToolchainValidationError
from src.metrics.models.tool_requirement import ToolRequirement
from src.metrics.models.validation_result import ValidationResult
from src.metrics.toolchain_manager import ToolchainManager


class TestValidateForLanguageSuccess:
    """Tests for successful validation scenarios."""

    def test_all_tools_pass_validation(self):
        """Test that validation passes when all tools are valid."""
        manager = ToolchainManager()

        # Mock tool requirements
        mock_tools = [
            ToolRequirement(
                name="python3",
                language="python",
                category="build",
                doc_url="https://python.org",
                min_version=None,
                version_command="--version"
            ),
            ToolRequirement(
                name="ruff",
                language="python",
                category="lint",
                doc_url="https://docs.astral.sh/ruff",
                min_version=None,
                version_command="--version"
            ),
        ]

        # Mock ToolDetector to return successful results
        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=mock_tools):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/tool'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    with patch.object(manager.detector, 'get_version', return_value=None):
                        report = manager.validate_for_language('python')

        assert report.passed is True
        assert report.language == 'python'
        assert len(report.checked_tools) == 2
        assert 'python3' in report.checked_tools
        assert 'ruff' in report.checked_tools
        assert len(report.errors_by_category) == 0

    def test_tools_with_valid_versions(self):
        """Test validation passes when tool versions meet requirements."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="npm",
            language="javascript",
            category="build",
            doc_url="https://npmjs.com",
            min_version="8.0.0",
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/npm'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    with patch.object(manager.detector, 'get_version', return_value='8.19.2'):
                        with patch.object(manager.detector, 'compare_versions', return_value=True):
                            report = manager.validate_for_language('javascript')

        assert report.passed is True
        assert len(report.errors_by_category) == 0


class TestValidateForLanguageFailures:
    """Tests for validation failure scenarios."""

    def test_missing_tool_raises_exception(self):
        """Test that missing tool raises ToolchainValidationError."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="ruff",
            language="python",
            category="lint",
            doc_url="https://docs.astral.sh/ruff",
            min_version=None,
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value=None):
                with pytest.raises(ToolchainValidationError) as exc_info:
                    manager.validate_for_language('python')

        error = exc_info.value
        assert error.report.passed is False
        assert 'missing' in error.report.errors_by_category
        assert len(error.report.errors_by_category['missing']) == 1
        assert error.report.errors_by_category['missing'][0].tool_name == 'ruff'

    def test_outdated_version_raises_exception(self):
        """Test that outdated tool version raises ToolchainValidationError."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="npm",
            language="javascript",
            category="build",
            doc_url="https://npmjs.com",
            min_version="8.0.0",
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/npm'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    with patch.object(manager.detector, 'get_version', return_value='7.5.0'):
                        with patch.object(manager.detector, 'compare_versions', return_value=False):
                            with pytest.raises(ToolchainValidationError) as exc_info:
                                manager.validate_for_language('javascript')

        error = exc_info.value
        assert 'outdated' in error.report.errors_by_category
        assert len(error.report.errors_by_category['outdated']) == 1
        result = error.report.errors_by_category['outdated'][0]
        assert result.tool_name == 'npm'
        assert result.version == '7.5.0'
        assert result.version_ok is False

    def test_permission_error_raises_exception(self):
        """Test that tool without execute permission raises ToolchainValidationError."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="ruff",
            language="python",
            category="lint",
            doc_url="https://docs.astral.sh/ruff",
            min_version=None,
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/ruff'):
                with patch.object(manager.detector, 'check_permissions', return_value=(False, '-rw-r--r--')):
                    with pytest.raises(ToolchainValidationError) as exc_info:
                        manager.validate_for_language('python')

        error = exc_info.value
        assert 'permission' in error.report.errors_by_category
        assert len(error.report.errors_by_category['permission']) == 1
        result = error.report.errors_by_category['permission'][0]
        assert result.tool_name == 'ruff'
        assert result.path == '/usr/bin/ruff'
        assert result.permissions == '-rw-r--r--'

    def test_version_detection_failure_raises_exception(self):
        """Test that version detection failure raises ToolchainValidationError."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="npm",
            language="javascript",
            category="build",
            doc_url="https://npmjs.com",
            min_version="8.0.0",
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/npm'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    with patch.object(manager.detector, 'get_version', return_value=None):
                        with pytest.raises(ToolchainValidationError) as exc_info:
                            manager.validate_for_language('javascript')

        error = exc_info.value
        assert 'other' in error.report.errors_by_category
        assert len(error.report.errors_by_category['other']) == 1
        result = error.report.errors_by_category['other'][0]
        assert result.tool_name == 'npm'
        assert result.version is None
        assert result.version_ok is False


class TestErrorCategorization:
    """Tests for error categorization logic (FR-017)."""

    def test_multiple_errors_grouped_by_category(self):
        """Test that multiple errors are correctly grouped by category."""
        manager = ToolchainManager()

        mock_tools = [
            ToolRequirement(name="ruff", language="python", category="lint",
                          doc_url="https://docs.astral.sh/ruff", min_version=None, version_command="--version"),
            ToolRequirement(name="pytest", language="python", category="test",
                          doc_url="https://docs.pytest.org", min_version=None, version_command="--version"),
            ToolRequirement(name="npm", language="javascript", category="build",
                          doc_url="https://npmjs.com", min_version="8.0.0", version_command="--version"),
        ]

        # Simulate different error types:
        # - ruff: missing
        # - pytest: permission error
        # - npm: outdated version
        def mock_availability(tool_name):
            if tool_name == "ruff":
                return None  # Missing
            return f"/usr/bin/{tool_name}"

        def mock_permissions(tool_path):
            if "pytest" in tool_path:
                return (False, "-rw-r--r--")  # No execute permission
            return (True, "-rwxr-xr-x")

        def mock_version(tool_path, version_command):
            if "npm" in tool_path:
                return "7.5.0"  # Outdated
            return None

        def mock_compare(current, minimum):
            return False  # npm version is outdated

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=mock_tools):
            with patch.object(manager.detector, 'check_availability', side_effect=mock_availability):
                with patch.object(manager.detector, 'check_permissions', side_effect=mock_permissions):
                    with patch.object(manager.detector, 'get_version', side_effect=mock_version):
                        with patch.object(manager.detector, 'compare_versions', side_effect=mock_compare):
                            with pytest.raises(ToolchainValidationError) as exc_info:
                                manager.validate_for_language('python')

        error = exc_info.value
        assert len(error.report.errors_by_category) == 3
        assert 'missing' in error.report.errors_by_category
        assert 'permission' in error.report.errors_by_category
        assert 'outdated' in error.report.errors_by_category

        # Verify each category has the correct tool
        assert error.report.errors_by_category['missing'][0].tool_name == 'ruff'
        assert error.report.errors_by_category['permission'][0].tool_name == 'pytest'
        assert error.report.errors_by_category['outdated'][0].tool_name == 'npm'

    def test_multiple_tools_same_category(self):
        """Test that multiple tools with same error category are grouped together."""
        manager = ToolchainManager()

        mock_tools = [
            ToolRequirement(name="ruff", language="python", category="lint",
                          doc_url="https://docs.astral.sh/ruff", min_version=None, version_command="--version"),
            ToolRequirement(name="pytest", language="python", category="test",
                          doc_url="https://docs.pytest.org", min_version=None, version_command="--version"),
        ]

        # Both tools missing
        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=mock_tools):
            with patch.object(manager.detector, 'check_availability', return_value=None):
                with pytest.raises(ToolchainValidationError) as exc_info:
                    manager.validate_for_language('python')

        error = exc_info.value
        assert len(error.report.errors_by_category) == 1
        assert 'missing' in error.report.errors_by_category
        assert len(error.report.errors_by_category['missing']) == 2
        tool_names = {result.tool_name for result in error.report.errors_by_category['missing']}
        assert tool_names == {'ruff', 'pytest'}


class TestGlobalAndLanguageTools:
    """Tests that global tools + language-specific tools are both validated."""

    def test_validates_both_global_and_language_tools(self):
        """Test that both global and language-specific tools are validated."""
        manager = ToolchainManager()

        # Mock get_tools_for_language to return both global and language tools
        mock_tools = [
            # Global tools
            ToolRequirement(name="git", language="global", category="build",
                          doc_url="https://git-scm.com", min_version=None, version_command="--version"),
            ToolRequirement(name="uv", language="global", category="build",
                          doc_url="https://docs.astral.sh/uv/", min_version=None, version_command="--version"),
            # Python-specific tools
            ToolRequirement(name="ruff", language="python", category="lint",
                          doc_url="https://docs.astral.sh/ruff", min_version=None, version_command="--version"),
        ]

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=mock_tools):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/tool'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    report = manager.validate_for_language('python')

        # Verify all 3 tools were checked (2 global + 1 language-specific)
        assert len(report.checked_tools) == 3
        assert 'git' in report.checked_tools
        assert 'uv' in report.checked_tools
        assert 'ruff' in report.checked_tools


class TestUnknownLanguageHandling:
    """Tests for unknown language error handling."""

    def test_unknown_language_raises_value_error(self):
        """Test that unknown language raises ValueError from tool registry."""
        manager = ToolchainManager()

        # Mock get_tools_for_language to raise ValueError
        with patch('src.metrics.toolchain_manager.get_tools_for_language',
                  side_effect=ValueError("Unsupported language: ruby")):
            with pytest.raises(ValueError) as exc_info:
                manager.validate_for_language('ruby')

        assert "Unsupported language" in str(exc_info.value)


class TestValidationReportStructure:
    """Tests for ValidationReport structure and content."""

    def test_report_contains_timestamp(self):
        """Test that validation report includes timestamp."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="python3",
            language="python",
            category="build",
            doc_url="https://python.org",
            min_version=None,
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/python3'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    report = manager.validate_for_language('python')

        assert report.timestamp is not None
        assert isinstance(report.timestamp, datetime)

    def test_report_includes_all_checked_tools(self):
        """Test that report lists all tools that were checked."""
        manager = ToolchainManager()

        mock_tools = [
            ToolRequirement(name="tool1", language="python", category="lint",
                          doc_url="https://example.com", min_version=None, version_command="--version"),
            ToolRequirement(name="tool2", language="python", category="test",
                          doc_url="https://example.com", min_version=None, version_command="--version"),
            ToolRequirement(name="tool3", language="python", category="build",
                          doc_url="https://example.com", min_version=None, version_command="--version"),
        ]

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=mock_tools):
            with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/tool'):
                with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                    report = manager.validate_for_language('python')

        assert len(report.checked_tools) == 3
        assert set(report.checked_tools) == {'tool1', 'tool2', 'tool3'}


class TestValidateSingleToolMethod:
    """Tests for _validate_single_tool private method."""

    def test_validate_single_tool_success_no_version_requirement(self):
        """Test validating a single tool without version requirement."""
        manager = ToolchainManager()

        tool_req = ToolRequirement(
            name="git",
            language="global",
            category="build",
            doc_url="https://git-scm.com",
            min_version=None,
            version_command="--version"
        )

        with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/git'):
            with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                result = manager._validate_single_tool(tool_req)

        assert result.tool_name == 'git'
        assert result.found is True
        assert result.path == '/usr/bin/git'
        assert result.version_ok is True
        assert result.error_category is None
        assert result.is_valid() is True

    def test_validate_single_tool_success_with_version_check(self):
        """Test validating a single tool with version requirement."""
        manager = ToolchainManager()

        tool_req = ToolRequirement(
            name="python3",
            language="python",
            category="build",
            doc_url="https://python.org",
            min_version="3.11.0",
            version_command="--version"
        )

        with patch.object(manager.detector, 'check_availability', return_value='/usr/bin/python3'):
            with patch.object(manager.detector, 'check_permissions', return_value=(True, '-rwxr-xr-x')):
                with patch.object(manager.detector, 'get_version', return_value='3.11.5'):
                    with patch.object(manager.detector, 'compare_versions', return_value=True):
                        result = manager._validate_single_tool(tool_req)

        assert result.tool_name == 'python3'
        assert result.found is True
        assert result.version == '3.11.5'
        assert result.version_ok is True
        assert result.error_category is None


class TestExceptionMessageFormat:
    """Tests that ToolchainValidationError contains proper error message."""

    def test_exception_message_format(self):
        """Test that ToolchainValidationError has formatted Chinese message."""
        manager = ToolchainManager()

        mock_tool = ToolRequirement(
            name="ruff",
            language="python",
            category="lint",
            doc_url="https://docs.astral.sh/ruff",
            min_version=None,
            version_command="--version"
        )

        with patch('src.metrics.toolchain_manager.get_tools_for_language', return_value=[mock_tool]):
            with patch.object(manager.detector, 'check_availability', return_value=None):
                with pytest.raises(ToolchainValidationError) as exc_info:
                    manager.validate_for_language('python')

        error = exc_info.value
        assert error.message is not None
        assert isinstance(error.message, str)
        assert len(error.message) > 0
        # Error message should contain Chinese text
        assert any('\u4e00' <= char <= '\u9fff' for char in error.message)
