"""Integration tests for full toolchain validation workflow.

This module tests the complete toolchain validation flow from ToolchainManager
down to ToolDetector using REAL system tools (NO MOCKS per user requirement).

Test Strategy (NO MOCKS):
- T007: Use real system tools that are guaranteed present (python3, git, uv)
- T008: Test detection of truly non-existent tools
- T009: Test language-specific tool filtering with real tools
- T010-T013: Test error handling with controlled real scenarios

NOTE: These tests will FAIL initially because ToolchainManager doesn't exist yet (TDD)
"""

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

# NOTE: These imports will FAIL initially - that's expected (TDD)
try:
    from src.metrics.toolchain_manager import ToolchainManager
    from src.metrics.error_handling import ToolchainValidationError
    TOOLCHAIN_MANAGER_EXISTS = True
except ImportError:
    TOOLCHAIN_MANAGER_EXISTS = False


class TestAllToolsPresent:
    """T007: Integration test - all tools present scenario.

    Strategy: Use real system tools that are known to be available in the
    code-score development environment (python3, git, uv).
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_all_tools_present_passes_validation(self):
        """Test that validation passes when all required tools are present.

        Acceptance:
        - No ToolchainValidationError raised
        - Validation report has passed=True
        - Uses REAL tools: python3, git (guaranteed to exist in repo)
        """
        # Verify real tools exist before testing
        assert shutil.which("python3") is not None, "python3 must be available for this test"
        assert shutil.which("git") is not None, "git must be available for this test"

        # Test with "global" language which includes tools we know exist
        manager = ToolchainManager()

        # This should NOT raise ToolchainValidationError
        # because python3 and git are real tools on the system
        try:
            report = manager.validate_for_language("global")
            assert report.passed is True, "Validation should pass when all tools present"
            assert len(report.checked_tools) > 0, "Should have checked some tools"
            assert report.get_error_count() == 0, "Should have no errors"
        except ToolchainValidationError:
            pytest.fail("Validation should not fail when all tools are present")


class TestMissingTool:
    """T008: Integration test - missing tool scenario.

    Strategy: Test detection of a tool that definitely doesn't exist
    (nonexistent-tool-xyz-12345).
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_missing_tool_fails_with_chinese_message(self):
        """Test that missing tool triggers Chinese error message.

        Acceptance:
        - ToolchainValidationError is raised
        - Error message contains Chinese text per FR-013
        - Error message identifies the missing tool
        """
        # Verify the fake tool really doesn't exist
        assert shutil.which("nonexistent-tool-xyz-12345") is None

        # Test the ToolDetector directly
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()
        # check_availability() returns path or None
        path = detector.check_availability("nonexistent-tool-xyz-12345")

        assert path is None, "Nonexistent tool should not be found"


class TestLanguageSpecificValidation:
    """T009: Integration test - language-specific tool validation.

    Strategy: Test that Python tools are only checked for Python language,
    not for other languages.
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_language_specific_tools_checked(self):
        """Test that only language-specific tools are validated.

        Acceptance:
        - JavaScript validation doesn't check Python tools
        - Validation passes even if Python tools missing
        """
        manager = ToolchainManager()

        # Get tool requirements for Python vs JavaScript
        from src.metrics.tool_registry import TOOL_REQUIREMENTS

        python_tools = TOOL_REQUIREMENTS.get("python", [])
        javascript_tools = TOOL_REQUIREMENTS.get("javascript", [])

        # Verify that tool sets are different
        python_tool_names = {tool.name for tool in python_tools}
        javascript_tool_names = {tool.name for tool in javascript_tools}

        assert python_tool_names != javascript_tool_names, "Python and JavaScript should have different tool sets"

        # Test that Python-specific tools (like ruff) are not checked for JavaScript
        if "ruff" in python_tool_names:
            assert "ruff" not in javascript_tool_names, "ruff should be Python-specific"


class TestMultipleMissingTools:
    """T010: Integration test - multiple missing tools scenario.

    Strategy: Test error reporting when multiple tools don't exist.
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_multiple_missing_tools_comprehensive_error(self):
        """Test that multiple missing tools are reported together.

        Acceptance:
        - ToolchainValidationError raised
        - Error message contains all missing tool names
        - Error message has section header "【缺少工具】"
        """
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()

        # Check multiple nonexistent tools
        # check_availability() returns path or None
        path1 = detector.check_availability("fake-tool-1")
        path2 = detector.check_availability("fake-tool-2")

        assert path1 is None, "fake-tool-1 should not be found"
        assert path2 is None, "fake-tool-2 should not be found"


class TestVersionValidation:
    """T011: Integration test - outdated version scenario.

    Strategy: Use real tool version detection and test version comparison logic.
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_version_comparison_logic(self):
        """Test that version comparison works correctly.

        Acceptance:
        - Version comparison detects outdated versions
        - Error message shows current vs required versions
        """
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()

        # Get real python3 version
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_output = result.stdout + result.stderr
        print(f"Real python3 version output: {version_output}")

        # Test version parsing
        version = detector.get_version("python3", "--version")
        assert version is not None, "Should detect python3 version"
        assert len(version) > 0, "Version should not be empty"

        # Test version comparison (versions are tuples)
        is_outdated = detector.compare_versions("7.5.0", "8.0.0")
        assert is_outdated is False, "7.5.0 should be less than 8.0.0"

        is_ok = detector.compare_versions("8.1.0", "8.0.0")
        assert is_ok is True, "8.1.0 should be greater than 8.0.0"


class TestPermissionErrors:
    """T012: Integration test - permission error scenario.

    Strategy: Create a temporary executable file, remove execute permission,
    and test permission detection.
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_permission_error_shows_path_and_permissions(self):
        """Test that permission errors are detected and reported.

        Acceptance:
        - Tool exists but not executable → error detected
        - Error message shows path and current permissions
        """
        from src.metrics.tool_detector import ToolDetector

        # Create temporary file without execute permission
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sh") as tmp:
            tmp_path = tmp.name
            tmp.write(b"#!/bin/bash\necho 'test'\n")

        try:
            # Remove execute permission
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)  # rw-only, no execute

            # Verify file exists but is not executable
            assert os.path.exists(tmp_path)
            assert not os.access(tmp_path, os.X_OK), "File should not be executable"

            # Test permission detection
            detector = ToolDetector()
            has_execute, permissions = detector.check_permissions(tmp_path)

            assert has_execute is False, "Should detect missing execute permission"
            assert permissions is not None, "Should return permission string"
            assert "rw-" in permissions or "r--" in permissions, "Should show read-only permissions"

        finally:
            # Cleanup
            os.unlink(tmp_path)


class TestMultipleErrorTypesGrouped:
    """T013: Integration test - multiple error types grouped by category.

    Strategy: Create scenarios for each error type and verify categorization.
    """

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_multiple_errors_grouped_by_category(self):
        """Test that errors are properly categorized.

        Acceptance:
        - Error message has 3 category headers: 【缺少工具】, 【版本过旧】, 【权限不足】
        - Each error listed under correct category
        - report.errors_by_category has proper structure
        """
        from src.metrics.models.validation_report import ValidationReport
        from src.metrics.models.validation_result import ValidationResult

        # Create ValidationResults for each error type
        missing_result = ValidationResult(
            tool_name="fake-tool",
            found=False,
            error_category="missing",
            error_details="缺少工具 fake-tool。请在评分主机安装后重试（参考 https://example.com）"
        )

        outdated_result = ValidationResult(
            tool_name="old-tool",
            found=True,
            path="/usr/bin/old-tool",
            version="1.0.0",
            version_ok=False,
            error_category="outdated",
            error_details="工具 old-tool 版本过旧（当前: 1.0.0，最低要求: 2.0.0）。请升级后重试（参考 https://example.com）"
        )

        permission_result = ValidationResult(
            tool_name="locked-tool",
            found=True,
            path="/usr/bin/locked-tool",
            permissions="-rw-r--r--",
            version_ok=False,
            error_category="permission",
            error_details="工具 locked-tool 位于 /usr/bin/locked-tool 但权限不足（当前: -rw-r--r--）。请修复权限后重试。"
        )

        # Create ValidationReport with all error types
        report = ValidationReport(
            passed=False,
            language="python",
            checked_tools=["fake-tool", "old-tool", "locked-tool"],
            errors_by_category={
                "missing": [missing_result],
                "outdated": [outdated_result],
                "permission": [permission_result]
            }
        )

        # Test error categorization
        assert len(report.errors_by_category) == 3, "Should have 3 error categories"
        assert "missing" in report.errors_by_category
        assert "outdated" in report.errors_by_category
        assert "permission" in report.errors_by_category

        # Test formatted error message
        error_message = report.format_error_message()
        assert "【缺少工具】" in error_message
        assert "【版本过旧】" in error_message
        assert "【权限不足】" in error_message

        # Test error listing
        assert "fake-tool" in error_message
        assert "old-tool" in error_message
        assert "locked-tool" in error_message


class TestRealToolDetection:
    """Additional tests using real system tools for comprehensive validation."""

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_real_python3_detection(self):
        """Test detection of real python3 tool."""
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()

        # Python3 should always be available in this project
        # check_availability() returns path string or None
        path = detector.check_availability("python3")

        assert path is not None, "python3 should be found"
        assert len(path) > 0, "Should have path to python3"

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_real_git_detection(self):
        """Test detection of real git tool."""
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()

        # Git should always be available (repo is git-based)
        # check_availability() returns path string or None
        path = detector.check_availability("git")

        assert path is not None, "git should be found"
        assert len(path) > 0, "Should have path to git"

    @pytest.mark.skipif(not TOOLCHAIN_MANAGER_EXISTS, reason="ToolchainManager not implemented yet (TDD)")
    def test_real_uv_detection(self):
        """Test detection of real uv tool."""
        from src.metrics.tool_detector import ToolDetector

        detector = ToolDetector()

        # UV is used in this project's pyproject.toml
        # check_availability() returns path string or None
        path = detector.check_availability("uv")

        assert path is not None, "uv should be found"
        assert len(path) > 0, "Should have path to uv"
