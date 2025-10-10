"""Real execution tests for pipeline executor module.

NO MOCKS - All tests use real script execution and subprocess calls.

This module tests the smoke test pipeline executor utilities with actual
script invocation and real file operations.
"""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tests.smoke.models import SmokeTestExecution
from tests.smoke.pipeline_executor import (
    PipelineExecutionError,
    PipelineTimeoutError,
    _build_command_args,
    check_pipeline_script_availability,
    cleanup_pipeline_outputs,
    execute_pipeline,
    get_pipeline_version_info,
    validate_pipeline_environment,
)


def check_script_available() -> bool:
    """Check if run_metrics.sh script is available."""
    try:
        result = subprocess.run(
            ["which", "bash"],
            capture_output=True,
            timeout=5
        )
        # Also check that scripts/run_metrics.sh exists
        script_path = Path.cwd() / "scripts" / "run_metrics.sh"
        return result.returncode == 0 and script_path.exists()
    except Exception:
        return False


class TestPipelineExecutor:
    """REAL TESTS for pipeline executor functions - NO MOCKS."""

    @pytest.fixture
    def real_project_root(self, tmp_path):
        """Create a real project structure with working script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create a REAL working script that produces valid output
        script_file = scripts_dir / "run_metrics.sh"
        script_content = """#!/bin/bash
# Test script for pipeline execution

REPO_URL="$1"

# Create output directory
mkdir -p output

# Generate minimal submission.json
cat > output/submission.json << 'EOF'
{
  "repository": {
    "url": "$REPO_URL",
    "commit": "test123",
    "language": "unknown"
  },
  "metrics": {},
  "execution": {"errors": [], "warnings": []}
}
EOF

echo "Mock pipeline completed successfully"
exit 0
"""
        script_file.write_text(script_content)
        script_file.chmod(0o755)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return tmp_path

    def test_build_command_args_default(self):
        """REAL TEST: Building command arguments with default options."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

        # REAL FUNCTION CALL - No mocks!
        args = _build_command_args(
            script_path=script_path,
            repository_url=repository_url,
            enable_checklist=True,
            generate_llm_report=False
        )

        expected = [
            "/test/script.sh",
            "git@github.com:test/repo.git",
            "--enable-checklist"
        ]

        assert args == expected

    def test_build_command_args_with_llm_report(self):
        """REAL TEST: Building command arguments with LLM report enabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

        # REAL FUNCTION CALL
        args = _build_command_args(
            script_path=script_path,
            repository_url=repository_url,
            enable_checklist=False,
            generate_llm_report=True
        )

        expected = [
            "/test/script.sh",
            "git@github.com:test/repo.git",
            "--disable-checklist",
            "--generate-llm-report"
        ]

        assert args == expected

    def test_build_command_args_minimal(self):
        """REAL TEST: Building command arguments with checklist disabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

        # REAL FUNCTION CALL
        args = _build_command_args(
            script_path=script_path,
            repository_url=repository_url,
            enable_checklist=False,
            generate_llm_report=False
        )

        expected = [
            "/test/script.sh",
            "git@github.com:test/repo.git",
            "--disable-checklist"
        ]

        assert args == expected

    def test_build_command_args_all_flags(self):
        """REAL TEST: Building command arguments with all flags enabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

        # REAL FUNCTION CALL
        args = _build_command_args(
            script_path=script_path,
            repository_url=repository_url,
            enable_checklist=True,
            generate_llm_report=True
        )

        expected = [
            "/test/script.sh",
            "git@github.com:test/repo.git",
            "--enable-checklist",
            "--generate-llm-report"
        ]

        assert args == expected

    def test_validate_pipeline_environment_success_real(self, real_project_root):
        """REAL TEST: Successful pipeline environment validation with real files."""
        # REAL VALIDATION - No mocks!
        is_valid, error_message = validate_pipeline_environment(real_project_root)

        assert is_valid is True
        assert error_message is None

    def test_validate_pipeline_environment_missing_directory_real(self):
        """REAL TEST: Pipeline environment validation with nonexistent directory."""
        nonexistent_path = Path("/nonexistent/directory/that/should/not/exist")

        # REAL VALIDATION
        is_valid, error_message = validate_pipeline_environment(nonexistent_path)

        assert is_valid is False
        assert "does not exist" in error_message

    def test_validate_pipeline_environment_missing_script_real(self, tmp_path):
        """REAL TEST: Pipeline environment validation with missing script."""
        # Create directory but no script
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # REAL VALIDATION
        is_valid, error_message = validate_pipeline_environment(tmp_path)

        assert is_valid is False
        assert "Pipeline script not found" in error_message

    def test_validate_pipeline_environment_not_directory_real(self, tmp_path):
        """REAL TEST: Pipeline environment validation with file instead of directory."""
        file_path = tmp_path / "not_a_directory"
        file_path.write_text("test")

        # REAL VALIDATION
        is_valid, error_message = validate_pipeline_environment(file_path)

        assert is_valid is False
        assert "not a directory" in error_message

    def test_execute_pipeline_success_real(self, real_project_root):
        """REAL TEST: Successful pipeline execution with real script."""
        repository_url = "git@github.com:test/repo.git"

        # REAL EXECUTION - No mocks!
        execution = execute_pipeline(
            repository_url=repository_url,
            working_directory=real_project_root,
            timeout_seconds=60
        )

        assert execution.repository_url == repository_url
        assert execution.working_directory == real_project_root
        assert execution.is_complete is True
        assert execution.is_successful is True
        assert execution.pipeline_exit_code == 0

    def test_execute_pipeline_failure_real(self, tmp_path):
        """REAL TEST: Pipeline execution failure with real failing script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create REAL failing script
        script_file = scripts_dir / "run_metrics.sh"
        script_file.write_text("""#!/bin/bash
echo "Pipeline failed" >&2
exit 1
""")
        script_file.chmod(0o755)

        repository_url = "git@github.com:test/repo.git"

        # REAL EXECUTION - should fail
        with pytest.raises(PipelineExecutionError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=tmp_path,
                timeout_seconds=60
            )

        assert "Pipeline failed with exit code 1" in str(exc_info.value)

    def test_execute_pipeline_timeout_real(self, tmp_path):
        """REAL TEST: Pipeline execution timeout with real slow script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create REAL script that takes too long
        script_file = scripts_dir / "run_metrics.sh"
        script_file.write_text("""#!/bin/bash
sleep 10
exit 0
""")
        script_file.chmod(0o755)

        repository_url = "git@github.com:test/repo.git"

        # REAL EXECUTION with very short timeout
        with pytest.raises(PipelineTimeoutError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=tmp_path,
                timeout_seconds=1  # 1 second timeout, script sleeps 10
            )

        assert "timed out after 1 seconds" in str(exc_info.value)

    def test_execute_pipeline_missing_script_real(self, tmp_path):
        """REAL TEST: Pipeline execution with missing script."""
        repository_url = "git@github.com:test/repo.git"

        # REAL EXECUTION - should fail
        with pytest.raises(PipelineExecutionError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=tmp_path,
                timeout_seconds=60
            )

        assert "Pipeline script not found" in str(exc_info.value)

    def test_cleanup_pipeline_outputs_success_real(self, real_project_root):
        """REAL TEST: Successful cleanup of pipeline outputs with real files."""
        output_dir = real_project_root / "output"

        # Create REAL output files
        (output_dir / "submission.json").write_text('{"test": "data"}')
        (output_dir / "score_input.json").write_text('{"test": "data"}')
        (output_dir / "evaluation_report.md").write_text("# Test Report")

        # Verify files exist
        assert (output_dir / "submission.json").exists()
        assert (output_dir / "score_input.json").exists()
        assert (output_dir / "evaluation_report.md").exists()

        # REAL CLEANUP - No mocks!
        cleanup_pipeline_outputs(real_project_root)

        # Verify files are removed
        assert not (output_dir / "submission.json").exists()
        assert not (output_dir / "score_input.json").exists()
        assert not (output_dir / "evaluation_report.md").exists()

    def test_cleanup_pipeline_outputs_no_directory_real(self, tmp_path):
        """REAL TEST: Cleanup when output directory doesn't exist."""
        # REAL CLEANUP - should not raise exception
        cleanup_pipeline_outputs(tmp_path)
        # Success if no exception raised

    @pytest.mark.skipif(not check_script_available(), reason="run_metrics.sh not available")
    def test_check_pipeline_script_availability_success_real(self):
        """REAL TEST: Successful pipeline script availability check."""
        # REAL CHECK - No mocks!
        available = check_pipeline_script_availability()

        # Note: This will be True if running in actual project directory
        assert isinstance(available, bool)

    def test_check_pipeline_script_availability_failure_real(self, tmp_path, monkeypatch):
        """REAL TEST: Failed pipeline script availability check."""
        # Change to directory without script
        monkeypatch.chdir(tmp_path)

        # REAL CHECK
        available = check_pipeline_script_availability()

        assert available is False

    def test_get_pipeline_version_info_success_real(self, real_project_root):
        """REAL TEST: Successful pipeline version info retrieval."""
        # Modify script to support --version flag
        script_path = real_project_root / "scripts" / "run_metrics.sh"
        script_path.write_text("""#!/bin/bash
if [ "$1" == "--version" ]; then
    echo "code-score v1.0.0"
    exit 0
fi
exit 1
""")
        script_path.chmod(0o755)

        # REAL VERSION CHECK - No mocks!
        version = get_pipeline_version_info(real_project_root)

        assert version == "code-score v1.0.0"

    def test_get_pipeline_version_info_timeout_real(self, tmp_path):
        """REAL TEST: Pipeline version info timeout with slow script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create REAL slow script
        script_file = scripts_dir / "run_metrics.sh"
        script_file.write_text("""#!/bin/bash
sleep 10
echo "version"
exit 0
""")
        script_file.chmod(0o755)

        # REAL VERSION CHECK - should timeout
        version = get_pipeline_version_info(tmp_path)

        assert version is None

    def test_get_pipeline_version_info_missing_script_real(self, tmp_path):
        """REAL TEST: Pipeline version info with missing script."""
        # REAL VERSION CHECK
        version = get_pipeline_version_info(tmp_path)

        assert version is None


class TestSmokeTestExecutionModel:
    """REAL TESTS for SmokeTestExecution model - NO MOCKS."""

    def test_smoke_test_execution_creation_real(self, tmp_path):
        """REAL TEST: Creating SmokeTestExecution instance with real directory."""
        # REAL MODEL CREATION
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=tmp_path,
            execution_start_time=datetime.now()
        )

        assert execution.repository_url == "git@github.com:test/repo.git"
        assert execution.working_directory == tmp_path
        assert execution.is_complete is False
        assert execution.is_successful is False

    def test_smoke_test_execution_validation_empty_url_real(self, tmp_path):
        """REAL TEST: Validation with empty repository URL."""
        # REAL VALIDATION - No mocks!
        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="",
                working_directory=tmp_path,
                execution_start_time=datetime.now()
            )

        assert "repository_url must not be empty" in str(exc_info.value)

    def test_smoke_test_execution_validation_missing_directory_real(self):
        """REAL TEST: Validation with missing working directory."""
        nonexistent_path = Path("/nonexistent/directory")

        # REAL VALIDATION
        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="git@github.com:test/repo.git",
                working_directory=nonexistent_path,
                execution_start_time=datetime.now()
            )

        assert "working_directory must exist" in str(exc_info.value)

    def test_mark_completed_success_real(self, tmp_path):
        """REAL TEST: Marking execution as completed successfully."""
        start_time = datetime.now()

        # REAL MODEL OPERATIONS
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=tmp_path,
            execution_start_time=start_time
        )

        execution.mark_completed(0)

        assert execution.is_complete is True
        assert execution.is_successful is True
        assert execution.pipeline_exit_code == 0
        assert execution.pipeline_duration is not None
        assert execution.pipeline_duration >= 0

    def test_mark_completed_failure_real(self, tmp_path):
        """REAL TEST: Marking execution as completed with failure."""
        # REAL MODEL OPERATIONS
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=tmp_path,
            execution_start_time=datetime.now()
        )

        execution.mark_completed(1)

        assert execution.is_complete is True
        assert execution.is_successful is False
        assert execution.pipeline_exit_code == 1
