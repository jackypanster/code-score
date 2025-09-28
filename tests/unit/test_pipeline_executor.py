"""
Unit tests for pipeline executor module.

This module contains unit tests for the pipeline execution utilities,
focusing on isolated testing of individual functions.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

from tests.smoke.pipeline_executor import (
    execute_pipeline,
    validate_pipeline_environment,
    cleanup_pipeline_outputs,
    check_pipeline_script_availability,
    get_pipeline_version_info,
    PipelineExecutionError,
    PipelineTimeoutError,
    _build_command_args
)
from tests.smoke.models import SmokeTestExecution


class TestPipelineExecutor:
    """Unit tests for pipeline executor functions."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create a mock project root with required structure."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        script_file = scripts_dir / "run_metrics.sh"
        script_file.write_text("#!/bin/bash\necho 'mock script'")
        script_file.chmod(0o755)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        return tmp_path

    def test_build_command_args_default(self):
        """Test building command arguments with default options."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

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
        """Test building command arguments with LLM report enabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

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
        """Test building command arguments with checklist disabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

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
        """Test building command arguments with all flags enabled."""
        script_path = Path("/test/script.sh")
        repository_url = "git@github.com:test/repo.git"

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

    def test_validate_pipeline_environment_success(self, mock_project_root):
        """Test successful pipeline environment validation."""
        is_valid, error_message = validate_pipeline_environment(mock_project_root)

        assert is_valid is True
        assert error_message is None

    def test_validate_pipeline_environment_missing_directory(self):
        """Test pipeline environment validation with missing directory."""
        nonexistent_path = Path("/nonexistent/directory")

        is_valid, error_message = validate_pipeline_environment(nonexistent_path)

        assert is_valid is False
        assert "does not exist" in error_message

    def test_validate_pipeline_environment_missing_script(self, tmp_path):
        """Test pipeline environment validation with missing script."""
        # Create directory but no script
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        is_valid, error_message = validate_pipeline_environment(tmp_path)

        assert is_valid is False
        assert "Pipeline script not found" in error_message

    def test_validate_pipeline_environment_not_directory(self, tmp_path):
        """Test pipeline environment validation with file instead of directory."""
        file_path = tmp_path / "not_a_directory"
        file_path.write_text("test")

        is_valid, error_message = validate_pipeline_environment(file_path)

        assert is_valid is False
        assert "not a directory" in error_message

    @patch('subprocess.run')
    def test_execute_pipeline_success(self, mock_subprocess, mock_project_root):
        """Test successful pipeline execution."""
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Pipeline completed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        repository_url = "git@github.com:test/repo.git"

        execution = execute_pipeline(
            repository_url=repository_url,
            working_directory=mock_project_root,
            timeout_seconds=60
        )

        assert execution.repository_url == repository_url
        assert execution.working_directory == mock_project_root
        assert execution.is_complete is True
        assert execution.is_successful is True
        assert execution.pipeline_exit_code == 0

    @patch('subprocess.run')
    def test_execute_pipeline_failure(self, mock_subprocess, mock_project_root):
        """Test pipeline execution failure."""
        # Mock failed subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Pipeline failed"
        mock_subprocess.return_value = mock_result

        repository_url = "git@github.com:test/repo.git"

        with pytest.raises(PipelineExecutionError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=mock_project_root,
                timeout_seconds=60
            )

        assert "Pipeline failed with exit code 1" in str(exc_info.value)

    @patch('subprocess.run')
    def test_execute_pipeline_timeout(self, mock_subprocess, mock_project_root):
        """Test pipeline execution timeout."""
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["test"], timeout=60
        )

        repository_url = "git@github.com:test/repo.git"

        with pytest.raises(PipelineTimeoutError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=mock_project_root,
                timeout_seconds=60
            )

        assert "timed out after 60 seconds" in str(exc_info.value)

    def test_execute_pipeline_missing_script(self, tmp_path):
        """Test pipeline execution with missing script."""
        repository_url = "git@github.com:test/repo.git"

        with pytest.raises(PipelineExecutionError) as exc_info:
            execute_pipeline(
                repository_url=repository_url,
                working_directory=tmp_path,
                timeout_seconds=60
            )

        assert "Pipeline script not found" in str(exc_info.value)

    def test_cleanup_pipeline_outputs_success(self, mock_project_root):
        """Test successful cleanup of pipeline outputs."""
        output_dir = mock_project_root / "output"

        # Create test output files
        (output_dir / "submission.json").write_text('{"test": "data"}')
        (output_dir / "score_input.json").write_text('{"test": "data"}')
        (output_dir / "evaluation_report.md").write_text("# Test Report")

        # Verify files exist
        assert (output_dir / "submission.json").exists()
        assert (output_dir / "score_input.json").exists()
        assert (output_dir / "evaluation_report.md").exists()

        # Cleanup
        cleanup_pipeline_outputs(mock_project_root)

        # Verify files are removed
        assert not (output_dir / "submission.json").exists()
        assert not (output_dir / "score_input.json").exists()
        assert not (output_dir / "evaluation_report.md").exists()

    def test_cleanup_pipeline_outputs_no_directory(self, tmp_path):
        """Test cleanup when output directory doesn't exist."""
        # Should not raise exception
        cleanup_pipeline_outputs(tmp_path)

    @patch('subprocess.run')
    def test_check_pipeline_script_availability_success(self, mock_subprocess):
        """Test successful pipeline script availability check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        available = check_pipeline_script_availability()

        assert available is True

    @patch('subprocess.run')
    def test_check_pipeline_script_availability_failure(self, mock_subprocess):
        """Test failed pipeline script availability check."""
        mock_subprocess.side_effect = FileNotFoundError()

        available = check_pipeline_script_availability()

        assert available is False

    @patch('subprocess.run')
    def test_get_pipeline_version_info_success(self, mock_subprocess, mock_project_root):
        """Test successful pipeline version info retrieval."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "code-score v1.0.0\n"
        mock_subprocess.return_value = mock_result

        version = get_pipeline_version_info(mock_project_root)

        assert version == "code-score v1.0.0"

    @patch('subprocess.run')
    def test_get_pipeline_version_info_failure(self, mock_subprocess, mock_project_root):
        """Test failed pipeline version info retrieval."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["test"], timeout=5
        )

        version = get_pipeline_version_info(mock_project_root)

        assert version is None

    def test_get_pipeline_version_info_missing_script(self, tmp_path):
        """Test pipeline version info with missing script."""
        version = get_pipeline_version_info(tmp_path)

        assert version is None


class TestSmokeTestExecutionModel:
    """Unit tests for SmokeTestExecution model."""

    def test_smoke_test_execution_creation(self, tmp_path):
        """Test creating SmokeTestExecution instance."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=tmp_path,
            execution_start_time=datetime.now()
        )

        assert execution.repository_url == "git@github.com:test/repo.git"
        assert execution.working_directory == tmp_path
        assert execution.is_complete is False
        assert execution.is_successful is False

    def test_smoke_test_execution_validation_empty_url(self, tmp_path):
        """Test validation with empty repository URL."""
        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="",
                working_directory=tmp_path,
                execution_start_time=datetime.now()
            )

        assert "repository_url must not be empty" in str(exc_info.value)

    def test_smoke_test_execution_validation_missing_directory(self):
        """Test validation with missing working directory."""
        nonexistent_path = Path("/nonexistent/directory")

        with pytest.raises(ValueError) as exc_info:
            SmokeTestExecution(
                repository_url="git@github.com:test/repo.git",
                working_directory=nonexistent_path,
                execution_start_time=datetime.now()
            )

        assert "working_directory must exist" in str(exc_info.value)

    def test_mark_completed_success(self, tmp_path):
        """Test marking execution as completed successfully."""
        start_time = datetime.now()
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

    def test_mark_completed_failure(self, tmp_path):
        """Test marking execution as completed with failure."""
        execution = SmokeTestExecution(
            repository_url="git@github.com:test/repo.git",
            working_directory=tmp_path,
            execution_start_time=datetime.now()
        )

        execution.mark_completed(1)

        assert execution.is_complete is True
        assert execution.is_successful is False
        assert execution.pipeline_exit_code == 1