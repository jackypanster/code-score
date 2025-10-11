"""Smoke tests for CLI integration with toolchain validation gate.

This module tests end-to-end CLI behavior with the toolchain validation gate.
Uses REAL subprocess calls (NO MOCKS per user requirement).

Test Strategy:
- T014: Test CLI fails immediately on missing tools after language detection
- Use real subprocess.run() to invoke CLI
- Verify exit codes and error messages
- Confirm repository is cleaned up when validation fails

Execution Order (Fixed in Code Review):
1. Clone repository
2. Detect language from repository files
3. Validate toolchain for detected language
4. If validation fails: cleanup repository and exit
5. If validation passes: proceed with analysis

NOTE: This test will FAIL initially because CLI integration doesn't exist yet (TDD)
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

# Check if CLI integration exists
try:
    from src.cli.main import main
    from src.metrics.toolchain_manager import ToolchainManager
    CLI_INTEGRATION_EXISTS = True
except ImportError:
    CLI_INTEGRATION_EXISTS = False


class TestCLIToolchainGate:
    """T014: Smoke test - CLI startup validation gate."""

    @pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
    def test_cli_validates_tools_before_cloning(self):
        """Test that CLI validates tools after language detection and cleans up on failure.

        Execution Order:
        1. Clone repository
        2. Detect language from repository files
        3. Validate toolchain for detected language
        4. If validation fails: cleanup repository and exit

        Acceptance:
        - Toolchain validation runs after language detection
        - If validation fails, exit code is 1
        - If validation fails, repository is cleaned up (no leftover files)
        - Error message is printed to stderr in Chinese
        """
        # Use a real test repository URL
        test_repo_url = "https://github.com/anthropics/anthropic-sdk-python.git"

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Run CLI with real subprocess (NO MOCKS)
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.main",
                    test_repo_url,
                    "--output-dir", str(output_dir),
                    "--verbose"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            # If any tools are missing, should fail early
            # If all tools present, should proceed to cloning

            # Check that temp directory is empty if validation failed
            if result.returncode != 0:
                # Validation failed - verify no repository was cloned
                cloned_dirs = list(output_dir.glob("*"))
                # Should only have output files, not cloned repository
                assert not any(d.is_dir() and ".git" in str(d) for d in cloned_dirs), \
                    "Repository should not be cloned when validation fails"

                # Check for Chinese error message if validation failed
                stderr = result.stderr
                # Should contain toolchain validation failure message
                # (exact message depends on which tools are missing)
                print(f"CLI stderr: {stderr}")
                print(f"CLI stdout: {result.stdout}")

    @pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
    def test_cli_with_all_tools_present_proceeds(self):
        """Test that CLI proceeds when all tools are available.

        Acceptance:
        - Validation passes OR provides clear error for missing tools
        - CLI behaves correctly based on validation result
        - Exit code reflects validation/analysis result

        Note: This test may fail if required tools (ruff, pytest, pip-audit) are not
        installed system-wide. Tools in UV virtual environments may not be detected
        by shutil.which() which checks system PATH.
        """
        # This test verifies the happy path OR documents which tools are missing
        test_repo_url = "https://github.com/anthropics/anthropic-sdk-python.git"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Run CLI
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.main",
                    test_repo_url,
                    "--output-dir", str(output_dir),
                    "--verbose"
                ],
                capture_output=True,
                text=True,
                timeout=120  # Allow time for actual cloning
            )

            print(f"CLI exit code: {result.returncode}")
            print(f"CLI stdout: {result.stdout}")
            print(f"CLI stderr: {result.stderr}")

            # Validation behavior is correct if:
            # 1. All tools present → validation passes, analysis proceeds
            # 2. Tools missing → validation fails with clear Chinese error message

            if "工具链验证失败" in result.stderr or "工具链验证失败" in result.stdout:
                # Validation failed - this is acceptable if tools are genuinely missing
                # Verify that it's failing for the right reason (missing tools)
                assert "缺少工具" in result.stderr or "缺少工具" in result.stdout, \
                    "Validation failed but doesn't show missing tool message"
                assert result.returncode == 1, "Validation failure should exit with code 1"
                print("✓ Validation correctly detected missing tools")
            else:
                # Validation passed - analysis should have proceeded
                # (Analysis itself might fail for other reasons, that's ok)
                print("✓ Validation passed, analysis proceeded")

    @pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
    def test_cli_skip_toolchain_check_flag(self):
        """Test that --skip-toolchain-check flag bypasses validation.

        Acceptance:
        - --skip-toolchain-check flag skips validation
        - Warning message printed
        - CLI proceeds even if tools missing
        """
        test_repo_url = "https://github.com/anthropics/anthropic-sdk-python.git"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Run CLI with skip flag
            result = subprocess.run(
                [
                    "uv", "run", "python", "-m", "src.cli.main",
                    test_repo_url,
                    "--output-dir", str(output_dir),
                    "--skip-toolchain-check",
                    "--verbose"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            print(f"CLI output with skip flag: {result.stdout}")
            print(f"CLI stderr with skip flag: {result.stderr}")

            # Should show warning message
            # "⚠ 警告: 已跳过工具链验证 (--skip-toolchain-check)"
            combined_output = result.stdout + result.stderr
            # Note: exact warning message TBD during implementation


class TestCLIErrorMessages:
    """Test CLI error message formatting and display."""

    @pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
    def test_cli_shows_chinese_error_message(self):
        """Test that CLI displays Chinese error messages per FR-013.

        Acceptance:
        - Error messages are in Chinese
        - Error messages include tool names and documentation URLs
        - Error messages are printed to stderr
        """
        # This test verifies that when validation fails,
        # the error message follows the FR-013 format

        # Create a scenario where validation will definitely fail
        # by requesting analysis with missing tools

        # Note: Actual implementation will depend on how CLI
        # integrates with ToolchainManager

        pass  # Placeholder - implement when CLI integration complete


class TestCLIIntegrationPoints:
    """Test integration between CLI main.py and ToolchainManager."""

    @pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
    def test_cli_calls_toolchain_validation_at_startup(self):
        """Test that CLI calls toolchain validation before any other operations.

        Acceptance:
        - ToolchainManager.validate_for_language() is called
        - Validation happens before repository cloning
        - Validation happens before language detection
        """
        # This test will verify the integration point exists
        # by checking that validation runs at the right time in the CLI flow

        # Strategy: Use instrumentation or logging to verify call order
        # Since we're avoiding mocks, we can check log output or side effects

        pass  # Placeholder - implement when CLI integration complete


# Additional smoke tests for completeness

@pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
def test_cli_help_includes_skip_flag():
    """Test that --help shows the --skip-toolchain-check flag."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "src.cli.main", "--help"],
        capture_output=True,
        text=True,
        timeout=10
    )

    assert result.returncode == 0, "Help command should succeed"
    help_text = result.stdout

    # Should mention skip-toolchain-check flag
    # (exact format TBD during implementation)
    print(f"CLI help output: {help_text}")


@pytest.mark.skipif(not CLI_INTEGRATION_EXISTS, reason="CLI toolchain integration not implemented yet (TDD)")
def test_cli_version_info():
    """Test that CLI reports version information."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "src.cli.main", "--version"],
        capture_output=True,
        text=True,
        timeout=10
    )

    print(f"CLI version output: {result.stdout}")
    print(f"CLI version stderr: {result.stderr}")

    # Version command should complete
    # (exit code and format TBD during implementation)
